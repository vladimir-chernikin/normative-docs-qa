#!/usr/bin/env python3
"""
Скрипт для проверки наличия моделей в локальной папке.
Этот скрипт проверяет наличие всех необходимых моделей и выводит информацию о них.
Он не загружает модели из интернета, а только проверяет их наличие.
"""

import os
import sys
import json
from pathlib import Path

# Определяем пути
project_root = Path(__file__).parent
config_path = project_root / "config" / "config.json"
models_dir = project_root / "local_models"

# Маппинг коротких имен на полные пути в Hugging Face
MODEL_MAPPING = {
    "rubert-tiny2": "cointegrated/rubert-tiny2",
    "multilingual-e5-small": "intfloat/multilingual-e5-small",
    "paraphrase-multilingual-MiniLM-L12-v2": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "labse": "sentence-transformers/LaBSE",
    "frida": "ai-forever/FRIDA"
    # "openai-e5-large": "text-embedding-3-large"  # OpenAI модель - закомментировано, так как требует внешний API
}

def load_config():
    """Загружает конфигурацию из JSON файла"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ Ошибка чтения config.json: {e}")
        return {}

def verify_model_integrity(model_path: Path, model_type: str = "sentence-transformers") -> bool:
    """
    Проверяет целостность загруженной модели.
    
    Args:
        model_path: Путь к директории модели
        model_type: Тип модели (sentence-transformers, transformers, openai)
        
    Returns:
        True если модель целостная, иначе False
    """
    # Для OpenAI моделей проверяем только наличие конфигурационного файла
    if model_type == "openai":
        # Закомментировано, так как OpenAI модели не поддерживаются в локальном режиме
        """
        config_file = model_path / "config.json"
        info_file = model_path / "openai_model_info.txt"
        return config_file.exists() and info_file.exists()
        """
        return False
    
    # Проверяем наличие основных файлов модели
    required_files = ["config.json"]
    model_files = ["model.safetensors", "pytorch_model.bin"]
    
    # Проверяем наличие конфигурации
    for file in required_files:
        if not (model_path / file).exists():
            return False
    
    # Проверяем наличие файлов модели (хотя бы одного из вариантов)
    has_model_file = any((model_path / file).exists() for file in model_files)
    
    # Проверяем наличие шардированных файлов модели (для Frida и других больших моделей)
    has_sharded_model = any(f.name.startswith("model-") and f.name.endswith(".safetensors") for f in model_path.glob("model-*.safetensors"))
    
    if not (has_model_file or has_sharded_model):
        return False
    
    # Проверяем наличие токенизатора
    tokenizer_files = ["tokenizer.json", "vocab.txt", "vocab.json"]
    has_tokenizer = any((model_path / file).exists() for file in tokenizer_files)
    if not has_tokenizer:
        return False
        
    return True

def check_models():
    """Проверяет наличие моделей в локальной папке"""
    print("\n" + "="*80)
    print("🔍 ПРОВЕРКА НАЛИЧИЯ МОДЕЛЕЙ")
    print("="*80)
    
    # Загружаем конфигурацию
    config = load_config()
    
    # Извлекаем список моделей из конфигурации
    # ИСПРАВЛЕНО: Теперь правильно обрабатываем формат конфигурации
    models_config = config.get("models", [])
    
    if not models_config:
        print("❌ Список моделей в config.json пуст")
        return False
    
    print(f"📋 Найдено моделей в конфигурации: {len(models_config)}")
    
    # Проверяем наличие директории local_models
    if not models_dir.exists():
        print(f"❌ Директория {models_dir} не существует")
        print(f"💡 Создайте директорию и загрузите модели с помощью скрипта download_models.py")
        return False
    
    # Проверяем каждую модель
    all_models_ok = True
    missing_models = []
    
    for model_config in models_config:
        model_name = model_config.get("name")
        model_type = model_config.get("type")
        model_path = models_dir / model_name
        full_model_path = model_config.get("model_path")
        
        print(f"\n📦 Проверка модели: {model_name}")
        print(f"  📂 Локальный путь: {model_path}")
        print(f"  🌐 Оригинальный путь: {full_model_path}")
        print(f"  🔧 Тип модели: {model_type}")
        
        # Для OpenAI моделей проверяем наличие переменной окружения
        if model_type == "openai":
            # Закомментировано, так как OpenAI модели не поддерживаются в локальном режиме
            """
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if not openai_api_key:
                print(f"  ⚠️ OPENAI_API_KEY не установлен в переменных окружения")
                print(f"  💡 Установите переменную окружения OPENAI_API_KEY для использования модели {model_name}")
            else:
                print(f"  ✅ OPENAI_API_KEY найден в переменных окружения")
            
            # Проверяем наличие конфигурационных файлов для OpenAI модели
            if not model_path.exists():
                print(f"  ⚠️ Директория модели не существует")
                print(f"  💡 Запустите скрипт download_models.py для создания конфигурации")
                all_models_ok = False
                missing_models.append(model_name)
                continue
            
            if not verify_model_integrity(model_path, model_type):
                print(f"  ⚠️ Конфигурация модели повреждена или отсутствует")
                print(f"  💡 Запустите скрипт download_models.py для создания конфигурации")
                all_models_ok = False
                missing_models.append(model_name)
                continue
            
            print(f"  ✅ Конфигурация модели найдена и проверена")
            """
            print(f"  ⚠️ Модель '{model_name}' использует OpenAI API и не поддерживается в локальном режиме")
            all_models_ok = False
            missing_models.append(model_name)
            continue
        
        # Для локальных моделей проверяем наличие файлов
        if not model_path.exists():
            print(f"  ❌ Модель отсутствует")
            all_models_ok = False
            missing_models.append(model_name)
            continue
        
        if not verify_model_integrity(model_path, model_type):
            print(f"  ⚠️ Модель повреждена или неполная")
            all_models_ok = False
            missing_models.append(model_name)
            continue
        
        print(f"  ✅ Модель найдена и проверена")
    
    print("\n" + "="*80)
    if all_models_ok:
        print("✅ ВСЕ МОДЕЛИ НАЙДЕНЫ И ГОТОВЫ К ИСПОЛЬЗОВАНИЮ")
    else:
        print("⚠️ НЕКОТОРЫЕ МОДЕЛИ ОТСУТСТВУЮТ ИЛИ ПОВРЕЖДЕНЫ")
        print(f"❌ Отсутствующие модели: {', '.join(missing_models)}")
        print("\n💡 Для загрузки моделей выполните:")
        print("   python download_models.py")
    print("="*80)
    
    return all_models_ok

if __name__ == "__main__":
    success = check_models()
    if not success:
        sys.exit(1) 