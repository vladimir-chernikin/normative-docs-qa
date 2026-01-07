#!/usr/bin/env python3
"""
Скрипт для удаления дубликатов из объединенной векторной базы
"""

import sys
import os
from pathlib import Path
import json
import logging
import pickle

# Добавляем корень проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from typing import List, Dict, Set
from utils.embeddings import SentenceTransformerEmbeddings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def remove_duplicates():
    """Удаляет дубликаты из объединенной векторной БД"""

    logger.info("=" * 80)
    logger.info("УДАЛЕНИЕ ДУБЛИКАТОВ ИЗ ОБЪЕДИНЕННОЙ ВЕКТОРНОЙ БАЗЫ")
    logger.info("=" * 80)

    # Конфигурация
    vectordb_dir = project_root / "vector-db-test/vectordb"
    model_name = "intfloat/multilingual-e5-base"
    input_dir = vectordb_dir / "unified_all_docs_e5-base"
    output_dir = vectordb_dir / "unified_all_docs_e5-base_dedup"

    if not input_dir.exists():
        logger.error(f"❌ Директория не найдена: {input_dir}")
        return False

    # Загружаем модель
    logger.info(f"📦 Загрузка модели: {model_name}")
    model = SentenceTransformer(model_name)
    embeddings = SentenceTransformerEmbeddings(model)
    logger.info("✅ Модель загружена")

    # Загружаем объединенную БД
    logger.info(f"📂 Загрузка объединенной БД из: {input_dir}")
    vector_store = FAISS.load_local(
        str(input_dir),
        embeddings,
        allow_dangerous_deserialization=True
    )

    original_vectors = vector_store.index.ntotal
    logger.info(f"📊 Исходное количество векторов: {original_vectors}")

    # Извлекаем все документы
    logger.info("📄 Извлечение документов...")
    all_docs = []
    seen_content: Set[str] = set()

    # Проходим по docstore
    for doc_id in vector_store.index_to_docstore_id.values():
        try:
            doc = vector_store.docstore.search(doc_id)
            if doc and hasattr(doc, 'page_content'):
                content = doc.page_content

                # Проверяем на дубликаты по содержимому
                if content not in seen_content:
                    seen_content.add(content)
                    all_docs.append(doc)
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при извлечении документа {doc_id}: {e}")
            continue

    unique_docs = len(all_docs)
    duplicates = original_vectors - unique_docs

    logger.info("=" * 80)
    logger.info("СТАТИСТИКА ДЕДУПЛИКАЦИИ")
    logger.info("=" * 80)
    logger.info(f"Исходных векторов: {original_vectors}")
    logger.info(f"Уникальных документов: {unique_docs}")
    logger.info(f"Найдено дубликатов: {duplicates} ({duplicates/original_vectors*100:.1f}%)")

    if duplicates == 0:
        logger.info("✅ Дубликатов не найдено!")
        return True

    # Создаем новую БД без дубликатов
    logger.info("\n" + "=" * 80)
    logger.info("СОЗДАНИЕ ОЧИЩЕННОЙ БАЗЫ")
    logger.info("=" * 80)

    logger.info(f"🔄 Создание новой FAISS базы из {unique_docs} уникальных документов...")

    # Создаем новую БД из уникальных документов
    cleaned_store = FAISS.from_documents(
        all_docs,
        embeddings,
    )

    logger.info(f"✅ Создана база: {cleaned_store.index.ntotal} векторов")

    # Сохраняем очищенную БД
    logger.info(f"\n💾 Сохранение в: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    cleaned_store.save_local(str(output_dir))
    logger.info("✅ Очищенная векторная БД сохранена")

    # Создаем отчет
    report = {
        "cleaned_db_path": str(output_dir),
        "original_db_path": str(input_dir),
        "model": model_name,
        "original_vectors": int(original_vectors),
        "unique_vectors": int(cleaned_store.index.ntotal),
        "duplicates_removed": int(duplicates),
        "dimension": int(cleaned_store.index.d),
        "created_at": str(Path.cwd())
    }

    report_file = project_root / "vector-db-test/dedup_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"📊 Отчет сохранен: {report_file}")

    logger.info("\n" + "=" * 80)
    logger.info("✅ ДЕДУПЛИКАЦИЯ ЗАВЕРШЕНА!")
    logger.info("=" * 80)
    logger.info(f"📁 Путь к очищенной БД: {output_dir}")
    logger.info(f"📊 Итоговое количество векторов: {cleaned_store.index.ntotal}")
    logger.info(f"🗑️ Удалено дубликатов: {duplicates}")

    return True


if __name__ == '__main__':
    success = remove_duplicates()
    sys.exit(0 if success else 1)
