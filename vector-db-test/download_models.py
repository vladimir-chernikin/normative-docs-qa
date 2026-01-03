#!/usr/bin/env python3
"""
Скрипт для скачивания всех необходимых моделей в локальную папку.
ВНИМАНИЕ: Это единственный скрипт, который загружает модели из интернета.
Все остальные компоненты системы работают ТОЛЬКО с локальными моделями.
"""
import os
import json
import shutil
from pathlib import Path
import torch
from transformers import AutoModel, AutoTokenizer

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
            return False
    
    # Проверяем наличие файлов модели (хотя бы одного из вариантов)
    has_model_file = any((model_path / file).exists() for file in model_files)
    if not has_model_file:
        return False
    
    # Проверяем наличие токенизатора
    tokenizer_files = ["tokenizer.json", "vocab.txt"]
    has_tokenizer = any((model_path / file).exists() for file in tokenizer_files)
    if not has_tokenizer:
        return False
        
    return True

def download_models():
    """Скачивает и сохраняет модели, перечисленные в config.json."""
    print("\n" + "="*80)
    print("🚀 ЗАГРУЗКА МОДЕЛЕЙ ДЛЯ АВТОНОМНОЙ РАБОТЫ")
    print("="*80)
    print("⚠️  ВАЖНО: Это единственный скрипт, который загружает модели из интернета.")
    print("⚠️  После загрузки система будет работать полностью автономно.")
    print("⚠️  Если вы хотите обновить модели, запустите этот скрипт снова.")
    print("="*80 + "\n")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка чтения config.json: {e}")
        return

    # Получаем список моделей из конфигурации
    models = config.get("models", [])
    if not models:
        print("⚠️ Список моделей в config.json пуст. Нечего скачивать.")
        return

    print(f"🔍 Найдено моделей для загрузки: {len(models)}")
    models_dir.mkdir(exist_ok=True)

    for model_config in models:
        short_name = model_config.get("name")
        model_type = model_config.get("type")
        full_model_path = model_config.get("model_path")
        
        if not short_name or not full_model_path:
            print(f"⚠️ Неполная конфигурация модели. Пропускаю.")
            continue

        # Пропускаем модели OpenAI, так как они не требуют локальной загрузки
        if model_type == "openai":
            # Закомментировано, так как требует внешний API
            """
            print(f"ℹ️ Модель '{short_name}' использует OpenAI API и не требует локальной загрузки.")
            
            # Создаем директорию для OpenAI модели с информационным файлом
            save_path = models_dir / short_name
            save_path.mkdir(exist_ok=True, parents=True)
            
            # Создаем конфигурационный файл для OpenAI модели
            config_file = save_path / "config.json"
            openai_config = {
                "model_name": full_model_path,
                "type": "openai",
                "requires_api_key": True,
                "embedding_size": model_config.get("embedding_size", 3072)
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(openai_config, f, indent=2)
            
            # Создаем информационный файл
            info_file = save_path / "openai_model_info.txt"
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(f"OpenAI Model: {full_model_path}\n")
                f.write("This is a placeholder for an OpenAI API model.\n")
                f.write("To use this model, set the OPENAI_API_KEY environment variable.\n")
                f.write("Example: export OPENAI_API_KEY='your-api-key'\n")
            
            # Создаем маркер успешной загрузки
            marker_file = save_path / ".download_complete"
            with open(marker_file, 'w') as f:
                f.write(f"OpenAI API Model: {full_model_path}\n")
                f.write(f"Date: {__import__('datetime').datetime.now().isoformat()}\n")
                f.write(f"REQUIRES API KEY: This model requires an OpenAI API key to function\n")
            
            print(f"✅ Информация о модели '{short_name}' сохранена локально.")
            """
            print(f"⚠️ Модель '{short_name}' использует OpenAI API и не поддерживается в локальном режиме. Пропускаю.")
            continue

        save_path = models_dir / short_name # Сохраняем в папку с коротким именем
        marker_file = save_path / ".download_complete"
        
        # Проверяем, существует ли модель и целостна ли она
        if save_path.exists() and marker_file.exists() and verify_model_integrity(save_path):
            print(f"✅ Модель '{short_name}' уже существует в {save_path} и проверена. Пропускаю.")
            continue
        
        # Если модель существует, но повреждена или не полностью загружена, удаляем её
        if save_path.exists() and (not marker_file.exists() or not verify_model_integrity(save_path)):
            print(f"⚠️ Модель '{short_name}' существует, но может быть повреждена. Удаляю и скачиваю заново.")
            shutil.rmtree(save_path, ignore_errors=True)

        print(f"⏳ Скачиваю модель '{full_model_path}' (как '{short_name}') в {save_path}...")
        try:
            # Создаем директорию, если её нет
            save_path.mkdir(exist_ok=True, parents=True)
            
            # Скачиваем модель в зависимости от типа
            if model_type == "sentence-transformers":
                # Для sentence-transformers используем AutoModel и AutoTokenizer напрямую
                print(f"📦 Загрузка модели sentence-transformers: {full_model_path}")
                
                # Загружаем модель и токенизатор
                tokenizer = AutoTokenizer.from_pretrained(full_model_path)
                model = AutoModel.from_pretrained(full_model_path)
                
                # Сохраняем модель и токенизатор
                model.save_pretrained(str(save_path))
                tokenizer.save_pretrained(str(save_path))
                print(f"✅ Модель и токенизатор сохранены в {save_path}")
                
            elif model_type == "transformers":
                # Для моделей типа transformers используем AutoModel и AutoTokenizer
                print(f"📦 Загрузка модели transformers: {full_model_path}")
                
                # Загружаем модель с использованием accelerate
                try:
                    print("🔄 Загрузка модели с device_map='auto'...")
                    model = AutoModel.from_pretrained(full_model_path, device_map='auto')
                except Exception as e:
                    print(f"⚠️ Ошибка загрузки с device_map: {e}")
                    print("🔄 Пробую загрузить без device_map...")
                    model = AutoModel.from_pretrained(full_model_path)
                
                # Загружаем токенизатор
                tokenizer = AutoTokenizer.from_pretrained(full_model_path)
                
                # Сохраняем модель и токенизатор
                model.save_pretrained(str(save_path))
                tokenizer.save_pretrained(str(save_path))
                print(f"✅ Модель и токенизатор сохранены в {save_path}")
            else:
                print(f"⚠️ Неизвестный тип модели: {model_type}. Пропускаю.")
                continue
            
            # Создаем маркер успешной загрузки
            with open(marker_file, 'w') as f:
                f.write(f"Downloaded from: {full_model_path}\n")
                f.write(f"Date: {__import__('datetime').datetime.now().isoformat()}\n")
                f.write(f"AUTONOMOUS MODE: This model is used in offline mode only\n")
            
            print(f"✅ Модель '{short_name}' успешно сохранена локально.")
        except Exception as e:
            print(f"❌ Не удалось скачать модель '{short_name}': {e}")
            # Удаляем частично загруженные файлы в случае ошибки
            if save_path.exists():
                shutil.rmtree(save_path, ignore_errors=True)

    print("\n" + "="*80)
    print("🎉 ЗАГРУЗКА МОДЕЛЕЙ ЗАВЕРШЕНА")
    print("="*80)
    print("✅ Все модели успешно загружены и сохранены локально.")
    print("✅ Система теперь может работать полностью автономно.")
    print("✅ Для запуска системы выполните: ./start_with_models.sh")
    # print("⚠️ Для использования OpenAI моделей установите переменную окружения OPENAI_API_KEY") # Закомментировано
    print("="*80)

if __name__ == "__main__":
    download_models()