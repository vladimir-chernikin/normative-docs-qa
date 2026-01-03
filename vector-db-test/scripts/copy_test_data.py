#!/usr/bin/env python3
"""
Скрипт для копирования тестовых данных из текущей базы в новую
"""

import os
import sys
import json
import shutil
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Добавляем путь к корневой директории проекта
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def load_config(config_path: str = "config/config.json") -> Dict[str, Any]:
    """Загружает конфигурацию из файла"""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Файл конфигурации не найден: {config_file}")
        
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def copy_test_data(config: Dict[str, Any], sample_count: int = 3) -> None:
    """
    Копирует тестовые данные из текущей базы в новую
    
    Args:
        config: Конфигурация проекта
        sample_count: Количество файлов для копирования
    """
    # Получаем пути к директориям из конфигурации
    if "databases" in config:
        source_dir = config["databases"]["current"]["source_documents"]
        target_dir = config["databases"]["new"]["source_documents"]
    else:
        source_dir = config["data_paths"]["source_documents"]
        target_dir = config["data_paths"].get("source_documents_new", f"{source_dir}_new")
    
    # Проверяем существование исходной директории
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"Ошибка: Исходная директория не найдена: {source_path}")
        return
    
    # Создаем целевую директорию, если она не существует
    target_path = Path(target_dir)
    target_path.mkdir(exist_ok=True, parents=True)
    
    # Получаем список markdown файлов
    markdown_files = list(source_path.glob("*.md"))
    
    if not markdown_files:
        print(f"Ошибка: В исходной директории нет markdown файлов: {source_path}")
        return
    
    # Если запрошено больше файлов, чем есть в исходной директории, 
    # используем все доступные файлы
    sample_count = min(sample_count, len(markdown_files))
    
    # Выбираем случайные файлы для копирования
    selected_files = random.sample(markdown_files, sample_count)
    
    print(f"Копирование {sample_count} файлов из {source_dir} в {target_dir}:")
    
    # Копируем выбранные файлы
    for file_path in selected_files:
        target_file = target_path / file_path.name
        print(f"  Копирую: {file_path.name}")
        shutil.copy2(file_path, target_file)
    
    # Проверяем результат
    copied_files = list(target_path.glob("*.md"))
    print(f"\nУспешно скопировано {len(copied_files)} файлов в {target_dir}")

def main():
    """Главная функция"""
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description='Копирование тестовых данных из текущей базы в новую')
    parser.add_argument('--config', type=str, default='config/config.json',
                        help='Путь к файлу конфигурации')
    parser.add_argument('--count', type=int, default=3,
                        help='Количество файлов для копирования')
    
    args = parser.parse_args()
    
    try:
        # Загружаем конфигурацию
        config = load_config(args.config)
        
        # Копируем тестовые данные
        copy_test_data(config, args.count)
        
    except KeyboardInterrupt:
        print("\nКопирование прервано пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main() 