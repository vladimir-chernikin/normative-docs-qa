#!/usr/bin/env python3
"""
Скрипт для проверки автономности системы.
Проверяет наличие всех необходимых моделей локально и их работоспособность без доступа к интернету.
"""

import os
import sys
import json
import time
import socket
from pathlib import Path

# Добавляем корневой каталог проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Конфигурация
CONFIG_PATH = project_root / "config" / "config.json"
LOCAL_MODELS_DIR = project_root / "local_models"

# Маппинг коротких имен на полные пути в Hugging Face
MODEL_MAPPING = {
    "rubert-tiny2": "cointegrated/rubert-tiny2",
    "multilingual-e5-small": "intfloat/multilingual-e5-small",
    "paraphrase-multilingual-MiniLM-L12-v2": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "labse": "sentence-transformers/LaBSE"
}

def is_internet_available():
    """Проверяет доступность интернета"""
    try:
        # Пробуем подключиться к Hugging Face
        socket.create_connection(("huggingface.co", 443), timeout=3)
        return True
    except OSError:
        return False

def verify_model_integrity(model_path: Path) -> bool:
    """
    Проверяет целостность загруженной модели.
    
    Args:
        model_path: Путь к директории модели
        
    Returns:
        True если модель целостная, иначе False
    """
    # Проверяем наличие основных файлов модели
    required_files = ["config.json"]
    model_files = ["model.safetensors", "pytorch_model.bin"]
    
    # Проверяем наличие конфигурации
    for file in required_files:
        if not (model_path / file).exists():
            print(f"⚠️ В локальной модели отсутствует файл {file}")
            return False
    
    # Проверяем наличие файлов модели (хотя бы одного из вариантов)
    has_model_file = any((model_path / file).exists() for file in model_files)
    if not has_model_file:
        print("⚠️ В локальной модели отсутствуют файлы весов модели")
        return False
    
    # Проверяем наличие токенизатора
    tokenizer_files = ["tokenizer.json", "vocab.txt"]
    has_tokenizer = any((model_path / file).exists() for file in tokenizer_files)
    if not has_tokenizer:
        print("⚠️ В локальной модели отсутствуют файлы токенизатора")
        return False
        
    return True

def load_config():
    """Загружает конфигурацию из JSON файла"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ Ошибка чтения config.json: {e}")
        return {}

def test_model_offline(model_name: str):
    """
    Тестирует загрузку модели в автономном режиме
    
    Args:
        model_name: Короткое имя модели
    """
    local_model_path = LOCAL_MODELS_DIR / model_name
    
    print(f"\n{'='*60}")
    print(f"🔍 Проверка автономности модели: {model_name}")
    print(f"📂 Локальный путь: {local_model_path}")
    
    # Проверяем наличие локальной модели
    if not local_model_path.exists():
        print(f"❌ Локальная модель не найдена")
        return False
    
    # Проверяем целостность модели
    if not verify_model_integrity(local_model_path):
        print(f"❌ Локальная модель повреждена или неполная")
        return False
    
    print(f"✅ Локальная модель найдена и проверена")
    
    # Тестируем загрузку в автономном режиме
    print(f"⏳ Тестирование загрузки модели в автономном режиме...")
    
    try:
        # Отключаем сеть для проверки автономности
        # Для этого блокируем доступ к huggingface.co через hosts
        original_socket_create_connection = socket.create_connection
        
        def blocked_create_connection(*args, **kwargs):
            host = args[0][0]
            if "huggingface" in host:
                raise socket.timeout("Симуляция отсутствия сети для теста автономности")
            return original_socket_create_connection(*args, **kwargs)
        
        # Подменяем функцию создания соединения
        socket.create_connection = blocked_create_connection
        
        # Пробуем загрузить модель из локальной папки
        start_time = time.time()
        
        # Импортируем здесь, чтобы перехватить сетевые запросы
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer(str(local_model_path))
        load_time = time.time() - start_time
        
        # Восстанавливаем оригинальную функцию
        socket.create_connection = original_socket_create_connection
        
        print(f"✅ Модель успешно загружена в автономном режиме за {load_time:.2f}с")
        
        # Тестируем работу модели
        test_texts = [
            "Тестовое предложение для проверки работы модели",
            "Статья 1. Общие положения Гражданского кодекса Российской Федерации"
        ]
        
        print(f"⏳ Тестирование работы модели на {len(test_texts)} текстах...")
        test_start = time.time()
        embeddings = model.encode(test_texts)
        test_time = time.time() - test_start
        
        print(f"✅ Модель работает! Размер эмбеддингов: {embeddings.shape}")
        print(f"⏱️ Время обработки: {test_time:.3f}с")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании модели в автономном режиме: {e}")
        return False
    finally:
        # Восстанавливаем оригинальную функцию в случае ошибки
        if socket.create_connection != original_socket_create_connection:
            socket.create_connection = original_socket_create_connection

def main():
    """Основная функция"""
    print("\n" + "="*80)
    print("🔒 ПРОВЕРКА АВТОНОМНОСТИ СИСТЕМЫ")
    print("="*80)
    print("Этот скрипт проверяет, что система может работать без доступа к интернету.")
    print("Все модели должны загружаться только из локального хранилища.")
    
    # Проверяем доступность интернета
    internet_available = is_internet_available()
    print(f"🌐 Доступ к интернету: {'✅ Доступен' if internet_available else '❌ Недоступен'}")
    
    # Загружаем конфигурацию
    config = load_config()
    model_names = config.get("models", {}).get("embedding_models", [])
    
    if not model_names:
        print("❌ Список моделей в конфигурации пуст")
        return
    
    print(f"📋 Найдено моделей в конфигурации: {len(model_names)}")
    
    # Проверяем наличие директории local_models
    if not LOCAL_MODELS_DIR.exists():
        print(f"❌ Директория {LOCAL_MODELS_DIR} не существует")
        print(f"💡 Создайте директорию и загрузите модели с помощью скрипта download_models.py")
        return
    
    # Тестируем каждую модель в автономном режиме
    results = {}
    for model_name in model_names:
        results[model_name] = test_model_offline(model_name)
    
    # Выводим общий результат
    print("\n" + "="*80)
    print("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ АВТОНОМНОСТИ")
    print("="*80)
    
    success_count = sum(1 for result in results.values() if result)
    print(f"✅ Успешно проверено моделей: {success_count}/{len(model_names)}")
    
    for model_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {model_name}")
    
    if success_count == len(model_names):
        print("\n🎉 СИСТЕМА ПОЛНОСТЬЮ АВТОНОМНА!")
        print("✅ Все модели могут работать без доступа к интернету.")
    else:
        print("\n⚠️ СИСТЕМА НЕ ПОЛНОСТЬЮ АВТОНОМНА!")
        print("❌ Некоторые модели требуют доступа к интернету.")
        print("\n💡 Для загрузки недостающих моделей выполните:")
        print("   python download_models.py")

if __name__ == "__main__":
    main() 