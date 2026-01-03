#!/usr/bin/env python3
"""
Конфигурация системы QA для нормативных документов
"""

import os
import logging
from pathlib import Path

# Базовая директория проекта
BASE_DIR = Path(__file__).parent

# Директории
FULLDOCS_DIR = BASE_DIR / "fulldocx"
VECTORDB_DIR = BASE_DIR / "vector-db-test" / "vectordb"
REPORTS_DIR = BASE_DIR / "reports"

# Создаем директории если их нет
REPORTS_DIR.mkdir(exist_ok=True)

# Модель для эмбедингов
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"

# Настройки обработки
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200
MIN_CHUNK_SIZE = 100

# Параметры векторного поиска
SEARCH_K = 50

# Параметры валидации
MIN_CHUNKS_COUNT = 2
MIN_AVG_CHUNK_SIZE = 100

# Логирование
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = REPORTS_DIR / "processing.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """Настройка логирования для всего приложения"""

    # Создаем handler для файла
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

    # Создаем handler для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger


# Настройка логирования при импорте модуля
logger = setup_logging()
