#!/usr/bin/env python3
"""
Скрипт для очистки и повторной загрузки локальных моделей.
Удаляет все локальные модели и запускает их загрузку заново.
"""

import os
import sys
import json
import shutil
from pathlib import Path

# Добавляем корневой каталог проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Конфигурация
CONFIG_PATH = project_root / "config" / "config.json"
LOCAL_MODELS_DIR = project_root / "local_models"

def load_config():
    """Загружает конфигурацию из JSON файла"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ Ошибка чтения config.json: {e}")
        return {}

def clean_local_models():
    """Очищает директорию с локальными моделями"""
    if not LOCAL_MODELS_DIR.exists():
        print(f"📂 Директория {LOCAL_MODELS_DIR} не существует, создаем...")
        LOCAL_MODELS_DIR.mkdir(parents=True, exist_ok=True)
        return
    
    print(f"🗑️ Очистка директории {LOCAL_MODELS_DIR}...")
    
    # Получаем список моделей
    model_dirs = [d for d in LOCAL_MODELS_DIR.iterdir() if d.is_dir()]
    
    if not model_dirs:
        print("✅ Директория уже пуста")
        return
    
    print(f"📋 Найдено {len(model_dirs)} моделей для удаления:")
    for model_dir in model_dirs:
        print(f"  - {model_dir.name}")
    
    # Запрашиваем подтверждение
    confirmation = input("\n⚠️ Вы уверены, что хотите удалить все локальные модели? (y/n): ")
    
    if confirmation.lower() != 'y':
        print("❌ Операция отменена")
        return
    
    # Удаляем каждую директорию
    for model_dir in model_dirs:
        try:
            print(f"🗑️ Удаление {model_dir.name}...")
            shutil.rmtree(model_dir)
        except Exception as e:
            print(f"⚠️ Ошибка при удалении {model_dir.name}: {e}")
    
    print("✅ Все локальные модели удалены")

def download_models():
    """Запускает скрипт загрузки моделей"""
    download_script = project_root / "download_models.py"
    
    if not download_script.exists():
        print(f"❌ Скрипт загрузки моделей не найден: {download_script}")
        return False
    
    print(f"🚀 Запуск скрипта загрузки моделей...")
    
    try:
        # Запускаем скрипт загрузки моделей
        import subprocess
        result = subprocess.run([sys.executable, str(download_script)], 
                               check=True, 
                               capture_output=True, 
                               text=True)
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ Модели успешно загружены")
            return True
        else:
            print(f"❌ Ошибка при загрузке моделей: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при запуске скрипта загрузки моделей: {e}")
        return False

def main():
    """Основная функция"""
    print("🔄 Сброс и повторная загрузка локальных моделей")
    
    # Загружаем конфигурацию
    config = load_config()
    model_names = config.get("models", {}).get("embedding_models", [])
    
    if not model_names:
        print("❌ Список моделей в конфигурации пуст")
        return
    
    print(f"📋 Найдено моделей в конфигурации: {len(model_names)}")
    
    # Очищаем директорию с локальными моделями
    clean_local_models()
    
    # Загружаем модели заново
    download_models()
    
    print("\n✅ Процесс сброса и повторной загрузки моделей завершен")
    print("💡 Для проверки загруженных моделей выполните:")
    print("   python scripts/test_local_models.py")

if __name__ == "__main__":
    main() 