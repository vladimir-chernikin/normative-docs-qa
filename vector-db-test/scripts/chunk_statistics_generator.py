#!/usr/bin/env python3
"""
Скрипт для подготовки данных о размерах чанков для гистограмм.
Анализирует документы в указанной директории, собирает статистику
по размерам чанков в символах и токенах.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List
import time

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Импортируем необходимые модули
from backend.chunk_analyzer import ChunkAnalyzer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(project_root, "logs", "chunk_statistics.log"), mode="w")
    ]
)
logger = logging.getLogger(__name__)

def ensure_dir_exists(path: str):
    """Убедиться, что директория существует, если нет - создать"""
    os.makedirs(path, exist_ok=True)

def save_json(data: Dict[str, Any], file_path: str):
    """Сохранить данные в JSON файл"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Данные сохранены в {file_path}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в {file_path}: {e}")

def generate_chunk_statistics(source_dir: str, output_dir: str = None):
    """
    Генерирует статистику по размерам чанков для всех документов в указанной директории.
    
    Args:
        source_dir: Путь к директории с документами
        output_dir: Путь для сохранения результатов (по умолчанию: data/chunk_statistics)
    """
    start_time = time.time()
    
    # Если output_dir не указан, используем директорию по умолчанию
    if not output_dir:
        output_dir = os.path.join(project_root, "data", "chunk_statistics")
    
    # Убедимся, что директория для сохранения результатов существует
    ensure_dir_exists(output_dir)
    
    # Создаем экземпляр ChunkAnalyzer
    config_path = os.path.join(project_root, "config", "config.json")
    analyzer = ChunkAnalyzer(config_path)
    
    # Проверяем существование директории с документами
    source_path = Path(source_dir)
    if not source_path.exists() or not source_path.is_dir():
        logger.error(f"Директория с документами не найдена: {source_dir}")
        return
    
    # Получаем список markdown файлов
    markdown_files = list(source_path.glob("*.md"))
    if not markdown_files:
        logger.warning(f"В директории {source_dir} не найдено markdown файлов")
        return
    
    logger.info(f"Найдено {len(markdown_files)} markdown файлов в {source_dir}")
    
    # Анализируем каждый документ
    all_results = {}
    total_chunks = 0
    
    for file_path in markdown_files:
        try:
            logger.info(f"Анализ документа: {file_path.name}")
            result = analyzer.analyze_document(str(file_path))
            all_results[file_path.name] = result
            total_chunks += result.get("total_chunks", 0)
            
            # Сохраняем результаты для отдельного документа
            doc_result_path = os.path.join(output_dir, f"{file_path.stem}_stats.json")
            save_json(result, doc_result_path)
            
        except Exception as e:
            logger.error(f"Ошибка при анализе документа {file_path}: {e}")
    
    # Получаем сводную статистику
    summary = analyzer.get_summary_statistics(all_results)
    
    # Сохраняем сводную статистику
    summary_path = os.path.join(output_dir, "summary_statistics.json")
    save_json(summary, summary_path)
    
    # Сохраняем полные результаты
    full_results = {
        "documents": all_results,
        "summary": summary,
        "analysis_time": time.time() - start_time,
        "total_documents": len(all_results),
        "total_chunks": total_chunks
    }
    full_results_path = os.path.join(output_dir, "full_statistics.json")
    save_json(full_results, full_results_path)
    
    logger.info(f"Анализ завершен. Обработано {len(all_results)} документов, {total_chunks} чанков")
    logger.info(f"Время выполнения: {time.time() - start_time:.2f} секунд")
    logger.info(f"Результаты сохранены в директории: {output_dir}")
    
    return full_results

def main():
    """Основная функция скрипта"""
    parser = argparse.ArgumentParser(description="Генерация статистики по размерам чанков документов")
    parser.add_argument("--source", type=str, default=os.path.join(project_root, "data", "markdown_with_headers0"),
                        help="Путь к директории с документами (по умолчанию: data/markdown_with_headers0)")
    parser.add_argument("--output", type=str, default=None,
                        help="Путь для сохранения результатов (по умолчанию: data/chunk_statistics)")
    args = parser.parse_args()
    
    # Создаем директорию для логов, если её нет
    ensure_dir_exists(os.path.join(project_root, "logs"))
    
    logger.info(f"Запуск генерации статистики по чанкам")
    logger.info(f"Директория с документами: {args.source}")
    logger.info(f"Директория для результатов: {args.output or os.path.join(project_root, 'data', 'chunk_statistics')}")
    
    # Генерируем статистику
    generate_chunk_statistics(args.source, args.output)

if __name__ == "__main__":
    main() 