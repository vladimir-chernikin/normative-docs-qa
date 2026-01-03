#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки функциональности подстановки цен
для моделей, отсутствующих в файле llm_pricing.json
"""

import os
import sys
import json
from pathlib import Path

# Добавляем корневую директорию проекта в путь импорта
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.llm_cost_manager import LLMCostManager

def test_model_price_fallback():
    """
    Тестирование функциональности подстановки цен для моделей,
    отсутствующих в файле llm_pricing.json
    """
    # Инициализация менеджера стоимости
    cost_manager = LLMCostManager()
    
    # Список тестовых случаев
    test_cases = [
        # Существующие модели (для проверки базовой функциональности)
        {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "input_tokens": 1000,
            "output_tokens": 500,
            "expected_substitute": False
        },
        {
            "provider": "openai",
            "model": "gpt-4",
            "input_tokens": 1000,
            "output_tokens": 500,
            "expected_substitute": False
        },
        # Несуществующие модели с ожидаемой подстановкой
        {
            "provider": "openai",
            "model": "gpt-3.5-turbo-1106",
            "input_tokens": 1000,
            "output_tokens": 500,
            "expected_substitute": True,
            "expected_family": "gpt-3.5-turbo"
        },
        {
            "provider": "openai",
            "model": "gpt-4-0613",
            "input_tokens": 1000,
            "output_tokens": 500,
            "expected_substitute": True,
            "expected_family": "gpt-4"
        },
        {
            "provider": "mistral",
            "model": "mistral-tiny-2402",
            "input_tokens": 1000,
            "output_tokens": 500,
            "expected_substitute": True,
            "expected_family": "mistral-tiny"
        },
        {
            "provider": "gemini",
            "model": "gemini-1.5-pro-experimental",
            "input_tokens": 1000,
            "output_tokens": 500,
            "expected_substitute": True,
            "expected_family": "gemini-1.5-pro"
        },
        {
            "provider": "zai",
            "model": "glm-4.5-preview",
            "input_tokens": 1000,
            "output_tokens": 500,
            "expected_substitute": True,
            "expected_family": "glm-4.5"
        }
    ]
    
    print("Тестирование функциональности подстановки цен для моделей")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases):
        print(f"\nТест #{i+1}: {test_case['provider']}/{test_case['model']}")
        
        # Рассчитываем стоимость
        result = cost_manager.calculate_cost(
            provider=test_case["provider"],
            model=test_case["model"],
            input_tokens=test_case["input_tokens"],
            output_tokens=test_case["output_tokens"]
        )
        
        # Проверяем результат
        has_substitute = "substitute_model" in result
        
        if test_case["expected_substitute"] and has_substitute:
            print(f"✅ Подстановка выполнена: {result['substitute_model']}")
            
            # Проверяем, что подстановка соответствует ожидаемому семейству
            if "expected_family" in test_case:
                family_match = test_case["expected_family"] in result["substitute_model"]
                if family_match:
                    print(f"✅ Подстановка из правильного семейства: {test_case['expected_family']}")
                else:
                    print(f"❌ Подстановка из неправильного семейства: ожидалось {test_case['expected_family']}, получено {result['substitute_model']}")
        
        elif not test_case["expected_substitute"] and not has_substitute:
            print("✅ Подстановка не требуется, используется оригинальная модель")
        
        elif test_case["expected_substitute"] and not has_substitute:
            print("❌ Ожидалась подстановка, но она не выполнена")
        
        else:  # not test_case["expected_substitute"] and has_substitute
            print(f"❌ Не ожидалась подстановка, но она выполнена: {result['substitute_model']}")
        
        # Выводим информацию о стоимости
        print(f"Стоимость: ${result['total_cost']:.6f} (вход: ${result['input_cost']:.6f}, выход: ${result['output_cost']:.6f})")
    
    print("\n" + "=" * 60)
    print("Тестирование завершено")

if __name__ == "__main__":
    test_model_price_fallback()