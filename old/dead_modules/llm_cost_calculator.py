#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для расчета стоимости запросов к различным LLM API
на основе количества входных и выходных токенов.
"""

import os
import json
import argparse
from typing import Dict, Any, Union, Optional, Tuple
from pathlib import Path

class LLMCostCalculator:
    """Калькулятор стоимости запросов к LLM API"""
    
    def __init__(self, pricing_file: Optional[str] = None):
        """
        Инициализация калькулятора стоимости запросов.
        
        Args:
            pricing_file: Путь к файлу с ценами на LLM API. Если None, 
                          будет использован файл по умолчанию.
        """
        if pricing_file is None:
            # Определение пути к корневой директории проекта
            project_root = Path(__file__).parent.parent
            pricing_file = os.path.join(project_root, "config", "llm_pricing.json")
        
        self.pricing_data = self._load_pricing_data(pricing_file)
    
    def _load_pricing_data(self, pricing_file: str) -> Dict[str, Any]:
        """
        Загрузка данных о ценах из JSON-файла.
        
        Args:
            pricing_file: Путь к файлу с ценами на LLM API.
            
        Returns:
            Dict[str, Any]: Данные о ценах.
        """
        try:
            with open(pricing_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Ошибка при загрузке файла с ценами: {e}")
    
    def get_available_providers(self) -> list:
        """
        Получить список доступных провайдеров.
        
        Returns:
            list: Список доступных провайдеров.
        """
        return list(self.pricing_data["providers"].keys())
    
    def get_available_models(self, provider: str) -> list:
        """
        Получить список доступных моделей для указанного провайдера.
        
        Args:
            provider: Идентификатор провайдера.
            
        Returns:
            list: Список доступных моделей.
        """
        if provider not in self.pricing_data["providers"]:
            raise ValueError(f"Провайдер {provider} не найден")
        
        return list(self.pricing_data["providers"][provider]["models"].keys())
    
    def calculate_cost(self, 
                      provider: str, 
                      model: str, 
                      input_tokens: int, 
                      output_tokens: int,
                      input_type: str = "text") -> Dict[str, float]:
        """
        Рассчитать стоимость запроса к LLM API.
        
        Args:
            provider: Идентификатор провайдера.
            model: Идентификатор модели.
            input_tokens: Количество входных токенов.
            output_tokens: Количество выходных токенов.
            input_type: Тип входных данных (для мультимодальных моделей).
                        Возможные значения: "text", "image", "video", "audio".
                        
        Returns:
            Dict[str, float]: Словарь с рассчитанной стоимостью:
                - input_cost: Стоимость входных токенов.
                - output_cost: Стоимость выходных токенов.
                - total_cost: Общая стоимость.
        """
        if provider not in self.pricing_data["providers"]:
            raise ValueError(f"Провайдер {provider} не найден")
        
        provider_data = self.pricing_data["providers"][provider]
        
        if model not in provider_data["models"]:
            raise ValueError(f"Модель {model} не найдена у провайдера {provider}")
        
        model_data = provider_data["models"][model]
        
        # Определение стоимости входных токенов
        input_price = model_data["input_price_per_1m"]
        
        # Для мультимодальных моделей (например, Gemini) цена может зависеть от типа входных данных
        if isinstance(input_price, dict):
            if input_type not in input_price:
                raise ValueError(f"Тип входных данных {input_type} не поддерживается моделью {model}")
            input_price = input_price[input_type]
        
        # Расчет стоимости
        input_cost = (input_tokens / 1_000_000) * input_price
        output_cost = (output_tokens / 1_000_000) * model_data["output_price_per_1m"]
        total_cost = input_cost + output_cost
        
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        }
    
    def get_model_info(self, provider: str, model: str) -> Dict[str, Any]:
        """
        Получить информацию о модели.
        
        Args:
            provider: Идентификатор провайдера.
            model: Идентификатор модели.
            
        Returns:
            Dict[str, Any]: Информация о модели.
        """
        if provider not in self.pricing_data["providers"]:
            raise ValueError(f"Провайдер {provider} не найден")
        
        provider_data = self.pricing_data["providers"][provider]
        
        if model not in provider_data["models"]:
            raise ValueError(f"Модель {model} не найдена у провайдера {provider}")
        
        model_data = provider_data["models"][model]
        
        return {
            "provider": provider_data["name"],
            "model": model,
            "description": model_data.get("description", ""),
            "context_window": model_data.get("context_window", 0),
            "input_price_per_1m": model_data["input_price_per_1m"],
            "output_price_per_1m": model_data["output_price_per_1m"]
        }
    
    def compare_models(self, 
                      input_tokens: int, 
                      output_tokens: int,
                      models: Optional[list] = None,
                      input_type: str = "text") -> Dict[str, Dict[str, float]]:
        """
        Сравнить стоимость запроса для разных моделей.
        
        Args:
            input_tokens: Количество входных токенов.
            output_tokens: Количество выходных токенов.
            models: Список моделей в формате "provider/model".
                   Если None, будут использованы все доступные модели.
            input_type: Тип входных данных (для мультимодальных моделей).
                        
        Returns:
            Dict[str, Dict[str, float]]: Словарь с рассчитанной стоимостью для каждой модели.
        """
        result = {}
        
        if models is None:
            # Использовать все доступные модели
            models = []
            for provider in self.get_available_providers():
                for model in self.get_available_models(provider):
                    models.append(f"{provider}/{model}")
        
        for model_id in models:
            try:
                provider, model = model_id.split("/")
                cost = self.calculate_cost(provider, model, input_tokens, output_tokens, input_type)
                result[model_id] = cost
            except (ValueError, KeyError) as e:
                print(f"Ошибка при расчете стоимости для модели {model_id}: {e}")
        
        # Сортировка по общей стоимости
        return dict(sorted(result.items(), key=lambda x: x[1]["total_cost"]))

def main():
    """Основная функция для запуска из командной строки."""
    parser = argparse.ArgumentParser(description="Калькулятор стоимости запросов к LLM API")
    parser.add_argument("--provider", type=str, help="Идентификатор провайдера")
    parser.add_argument("--model", type=str, help="Идентификатор модели")
    parser.add_argument("--input-tokens", type=int, default=1000, help="Количество входных токенов")
    parser.add_argument("--output-tokens", type=int, default=500, help="Количество выходных токенов")
    parser.add_argument("--input-type", type=str, default="text", 
                        choices=["text", "image", "video", "audio"],
                        help="Тип входных данных (для мультимодальных моделей)")
    parser.add_argument("--compare", action="store_true", help="Сравнить стоимость для всех моделей")
    parser.add_argument("--pricing-file", type=str, help="Путь к файлу с ценами")
    
    args = parser.parse_args()
    
    calculator = LLMCostCalculator(args.pricing_file)
    
    if args.compare:
        # Сравнение всех моделей
        results = calculator.compare_models(args.input_tokens, args.output_tokens, input_type=args.input_type)
        
        print(f"\nСравнение стоимости для {args.input_tokens} входных и {args.output_tokens} выходных токенов:")
        print("-" * 80)
        print(f"{'Модель':<30} {'Входные токены':<15} {'Выходные токены':<15} {'Общая стоимость':<15}")
        print("-" * 80)
        
        for model_id, cost in results.items():
            print(f"{model_id:<30} ${cost['input_cost']:<14.5f} ${cost['output_cost']:<14.5f} ${cost['total_cost']:<14.5f}")
    
    elif args.provider and args.model:
        # Расчет для конкретной модели
        try:
            cost = calculator.calculate_cost(
                args.provider, args.model, args.input_tokens, args.output_tokens, args.input_type
            )
            
            model_info = calculator.get_model_info(args.provider, args.model)
            
            print(f"\nРасчет стоимости для модели {args.provider}/{args.model}:")
            print(f"Описание: {model_info['description']}")
            print(f"Контекстное окно: {model_info['context_window']} токенов")
            print(f"Входные токены: {args.input_tokens} (${cost['input_cost']:.5f})")
            print(f"Выходные токены: {args.output_tokens} (${cost['output_cost']:.5f})")
            print(f"Общая стоимость: ${cost['total_cost']:.5f}")
        
        except ValueError as e:
            print(f"Ошибка: {e}")
    
    else:
        # Вывод списка доступных провайдеров и моделей
        print("\nДоступные провайдеры и модели:")
        
        for provider in calculator.get_available_providers():
            print(f"\n{provider}:")
            
            for model in calculator.get_available_models(provider):
                try:
                    model_info = calculator.get_model_info(provider, model)
                    print(f"  - {model}: {model_info['description']}")
                except ValueError:
                    print(f"  - {model}")
        
        print("\nИспользуйте --provider и --model для расчета стоимости конкретной модели")
        print("или --compare для сравнения всех моделей.")

if __name__ == "__main__":
    main()