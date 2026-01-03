#!/usr/bin/env python3
"""
Загрузчик и тестировщик локальных embedding моделей для системы векторизации

Этот скрипт:
1. Загружает локальные embedding модели (sentence-transformers/transformers)
2. Тестирует их работоспособность
3. Мониторит использование GPU памяти в реальном времени
4. Измеряет производительность на тестовых текстах
"""

import os
import sys
import json
import time
import logging
import threading
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path

import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoTokenizer
import pynvml
import psutil

# Добавляем путь к config для импорта конфигурации
sys.path.append(str(Path(__file__).parent.parent))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('embedding_models.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GPUMonitor:
    """Класс для мониторинга GPU памяти в реальном времени"""
    
    def __init__(self):
        try:
            pynvml.nvmlInit()
            self.gpu_available = True
            self.device_count = pynvml.nvmlDeviceGetCount()
        except Exception as e:
            logger.warning(f"GPU мониторинг недоступен: {e}")
            self.gpu_available = False
            self.device_count = 0
        
        self.monitoring = False
        self.thread = None
        
    def start_monitoring(self, device_id: int = 0):
        """Запускает мониторинг GPU"""
        if not self.gpu_available:
            logger.warning("GPU недоступен для мониторинга")
            return
            
        self.monitoring = True
        self.thread = threading.Thread(target=self._monitor_loop, args=(device_id,))
        self.thread.daemon = True
        self.thread.start()
        logger.info("GPU мониторинг запущен")
        
    def _monitor_loop(self, device_id: int):
        """Основной цикл мониторинга"""
        while self.monitoring:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                used_mb = mem_info.used // 1024**2
                total_mb = mem_info.total // 1024**2
                usage_percent = (used_mb / total_mb) * 100
                
                print(f"\r[GPU-{device_id}] {used_mb:,}/{total_mb:,} MB ({usage_percent:.1f}%)", 
                      end="", flush=True)
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Ошибка мониторинга GPU: {e}")
                break
                
    def stop_monitoring(self):
        """Останавливает мониторинг GPU"""
        self.monitoring = False
        if self.thread:
            self.thread.join(timeout=2)
        print()  # новая строка
        logger.info("GPU мониторинг остановлен")
        
    def get_gpu_info(self) -> Dict:
        """Получает информацию о GPU"""
        if not self.gpu_available:
            return {"available": False}
            
        gpu_info = {"available": True, "devices": []}
        
        for i in range(self.device_count):
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                gpu_info["devices"].append({
                    "id": i,
                    "name": name,
                    "memory_total_mb": mem_info.total // 1024**2,
                    "memory_used_mb": mem_info.used // 1024**2,
                    "memory_free_mb": mem_info.free // 1024**2
                })
            except Exception as e:
                logger.error(f"Ошибка получения информации о GPU {i}: {e}")
                
        return gpu_info


class EmbeddingModelLoader:
    """Класс для загрузки и управления embedding моделями"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config_path = Path(config_path)
        self.models = {}
        self.gpu_monitor = GPUMonitor()
        self.device = self._detect_device()
        
        # Загружаем конфигурацию моделей
        self.model_configs = self._load_model_configs()
        
    def _detect_device(self) -> str:
        """Определяет доступное устройство для вычислений"""
        if torch.cuda.is_available():
            device = "cuda"
            logger.info(f"Обнаружен CUDA: {torch.cuda.get_device_name()}")
        else:
            device = "cpu"
            logger.info("CUDA недоступен, используется CPU")
        return device
        
    def _load_model_configs(self) -> List[Dict]:
        """Загружает конфигурацию моделей из JSON файла"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            models = config.get('models', [])
            logger.info(f"Загружено {len(models)} конфигураций моделей")
            return models
            
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            return []
    
    def get_model_config_by_name(self, model_name: str) -> Optional[Dict]:
        """Получает конфигурацию модели по имени"""
        configs = self._load_model_configs()
        for config in configs:
            if config.get('name') == model_name:
                return config
        return None
    
    def load_model_by_name(self, model_name: str) -> Optional[Union[SentenceTransformer, Tuple]]:
        """Загружает модель по имени"""
        config = self.get_model_config_by_name(model_name)
        if config is None:
            logger.error(f"Конфигурация модели {model_name} не найдена")
            return None
        return self.load_model(config)
            
    def load_model(self, model_config: Dict) -> Optional[Union[SentenceTransformer, Tuple]]:
        """
        Загружает модель по конфигурации
        
        Args:
            model_config: Конфигурация модели
            
        Returns:
            Загруженная модель или None в случае ошибки
        """
        model_name = model_config['name']
        model_path = model_config['model_path']
        model_type = model_config['type']
        estimated_vram = model_config.get('estimated_vram_mb', 0)
        
        logger.info(f"Загрузка модели: {model_name} ({model_type})")
        logger.info(f"Путь: {model_path}")
        logger.info(f"Ожидаемое потребление VRAM: {estimated_vram} MB")
        
        start_time = time.time()
        
        try:
            if model_type == "sentence-transformers":
                model = SentenceTransformer(model_path, device=self.device)
                
            elif model_type == "transformers":
                if self.device == "cuda":
                    try:
                        # Пробуем загрузить с accelerate
                        logger.info(f"Загрузка модели {model_name} с использованием accelerate (device_map='auto')")
                        model = AutoModel.from_pretrained(model_path, device_map='auto')
                    except Exception as e:
                        logger.warning(f"Ошибка загрузки с accelerate: {e}")
                        logger.info("Пробуем загрузить без device_map")
                        model = AutoModel.from_pretrained(model_path).to(self.device)
                else:
                    model = AutoModel.from_pretrained(model_path)
                    
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                model = (model, tokenizer)
                
            else:
                logger.error(f"Неподдерживаемый тип модели: {model_type}")
                return None
                
            load_time = time.time() - start_time
            logger.info(f"Модель {model_name} загружена за {load_time:.2f} сек")
            
            self.models[model_name] = {
                'model': model,
                'config': model_config,
                'load_time': load_time
            }
            
            return model
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели {model_name}: {e}")
            return None
            
    def test_model_embedding(self, model_name: str, test_texts: List[str]) -> Dict:
        """
        Тестирует embedding модель на тестовых текстах
        
        Args:
            model_name: Имя модели для тестирования
            test_texts: Список тестовых текстов
            
        Returns:
            Результаты тестирования
        """
        if model_name not in self.models:
            logger.error(f"Модель {model_name} не загружена")
            return {}
            
        model_info = self.models[model_name]
        model = model_info['model']
        config = model_info['config']
        
        logger.info(f"Тестирование модели {model_name} на {len(test_texts)} текстах")
        
        results = {
            'model_name': model_name,
            'model_type': config['type'],
            'embedding_size': config['embedding_size'],
            'test_count': len(test_texts),
            'embeddings': [],
            'processing_times': [],
            'average_time': 0,
            'total_time': 0
        }
        
        total_start = time.time()
        
        for i, text in enumerate(test_texts):
            start_time = time.time()
            
            try:
                if config['type'] == "sentence-transformers":
                    embedding = model.encode([text])[0]
                    
                elif config['type'] == "transformers":
                    model_obj, tokenizer = model
                    inputs = tokenizer(text, return_tensors='pt', 
                                     truncation=True, padding=True)
                    
                    if self.device == "cuda":
                        inputs = {k: v.cuda() for k, v in inputs.items()}
                        
                    with torch.no_grad():
                        outputs = model_obj(**inputs)
                        embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()[0]
                        
                processing_time = time.time() - start_time
                results['processing_times'].append(processing_time)
                results['embeddings'].append(embedding.tolist())
                
                logger.info(f"Текст {i+1}: {processing_time:.3f}с, размер: {len(embedding)}")
                
            except Exception as e:
                logger.error(f"Ошибка обработки текста {i+1}: {e}")
                results['processing_times'].append(-1)
                results['embeddings'].append([])
                
        results['total_time'] = time.time() - total_start
        results['average_time'] = np.mean([t for t in results['processing_times'] if t > 0])
        
        logger.info(f"Тестирование завершено за {results['total_time']:.2f}с")
        logger.info(f"Среднее время на текст: {results['average_time']:.3f}с")
        
        return results
        
    def load_and_test_all_models(self, test_texts: List[str]) -> Dict:
        """
        Загружает и тестирует все модели из конфигурации
        
        Args:
            test_texts: Тестовые тексты для проверки
            
        Returns:
            Сводные результаты тестирования
        """
        logger.info("Начинаем загрузку и тестирование всех моделей")
        
        # Показываем информацию о GPU
        gpu_info = self.gpu_monitor.get_gpu_info()
        logger.info(f"GPU информация: {json.dumps(gpu_info, indent=2, ensure_ascii=False)}")
        
        results = {
            'system_info': {
                'device': self.device,
                'gpu_info': gpu_info,
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3)
            },
            'models_tested': [],
            'test_texts': test_texts,
            'summary': {}
        }
        
        # Сортируем модели по приоритету (от легких к тяжелым)
        sorted_models = sorted(self.model_configs, key=lambda x: x['priority'])
        
        for model_config in sorted_models:
            model_name = model_config['name']
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Тестирование модели: {model_name}")
            logger.info(f"{'='*60}")
            
            # Запускаем GPU мониторинг
            if self.device == "cuda":
                self.gpu_monitor.start_monitoring()
                
            # Загружаем модель
            model = self.load_model(model_config)
            
            if model is None:
                logger.error(f"Пропускаем модель {model_name} - ошибка загрузки")
                continue
                
            # Тестируем модель
            test_results = self.test_model_embedding(model_name, test_texts)
            results['models_tested'].append(test_results)
            
            # Останавливаем мониторинг
            if self.device == "cuda":
                self.gpu_monitor.stop_monitoring()
                
            # Освобождаем память
            del self.models[model_name]
            if self.device == "cuda":
                torch.cuda.empty_cache()
                
            logger.info(f"Модель {model_name} протестирована и выгружена")
            
        # Создаем сводку
        if results['models_tested']:
            summary = {}
            for test_result in results['models_tested']:
                summary[test_result['model_name']] = {
                    'avg_time': test_result['average_time'],
                    'total_time': test_result['total_time'],
                    'embedding_size': test_result['embedding_size'],
                    'model_type': test_result['model_type']
                }
            results['summary'] = summary
            
        return results
        
    def save_results(self, results: Dict, output_file: str = "model_test_results.json"):
        """Сохраняет результаты тестирования в JSON файл"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Результаты сохранены в {output_file}")
        except Exception as e:
            logger.error(f"Ошибка сохранения результатов: {e}")


def main():
    """Основная функция для тестирования моделей"""
    
    # Тестовые тексты для проверки моделей
    test_texts = [
        "Статья 1. Общие положения Гражданского кодекса Российской Федерации",
        "Настоящий Федеральный закон регулирует отношения, возникающие в сфере жилищного права",
        "Правительство Российской Федерации постановляет установить следующие нормативы потребления",
        "Юридическое лицо считается созданным с момента его государственной регистрации",
        "Договор считается заключенным, если между сторонами в требуемой в подлежащих случаях форме достигнуто соглашение по всем существенным условиям договора"
    ]
    
    print("🚀 Запуск тестирования embedding моделей")
    print(f"📋 Количество тестовых текстов: {len(test_texts)}")
    print("="*70)
    
    # Создаем загрузчик моделей
    loader = EmbeddingModelLoader()
    
    if not loader.model_configs:
        logger.error("Не найдены конфигурации моделей. Проверьте config/config.json")
        return
        
    # Запускаем тестирование всех моделей
    results = loader.load_and_test_all_models(test_texts)
    
    # Сохраняем результаты
    loader.save_results(results, "vector-db-test/scripts/model_test_results.json")
    
    # Выводим сводку
    print("\n" + "="*70)
    print("📊 СВОДКА РЕЗУЛЬТАТОВ ТЕСТИРОВАНИЯ")
    print("="*70)
    
    if results['summary']:
        for model_name, stats in results['summary'].items():
            print(f"\n🔹 {model_name}:")
            print(f"   • Тип модели: {stats['model_type']}")
            print(f"   • Размер embedding: {stats['embedding_size']}")
            print(f"   • Среднее время на текст: {stats['avg_time']:.3f}с")
            print(f"   • Общее время тестирования: {stats['total_time']:.2f}с")
    else:
        print("❌ Ни одна модель не была успешно протестирована")
        
    print("\n✅ Тестирование завершено!")


if __name__ == "__main__":
    main() 