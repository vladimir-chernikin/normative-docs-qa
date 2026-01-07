#!/usr/bin/env python3
"""
Скрипт для объединения всех векторных БД в единую базу

Объединяет 18 отдельных FAISS индексов в один для быстрого поиска.
"""

import sys
import os
from pathlib import Path
import json
import logging

# Добавляем корень проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from typing import List
from utils.embeddings import SentenceTransformerEmbeddings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def merge_vector_dbs():
    """Объединяет все векторные БД в одну"""

    logger.info("=" * 80)
    logger.info("ОБЪЕДИНЕНИЕ ВЕКТОРНЫХ БАЗ НОРМАТИВНЫХ ДОКУМЕНТОВ")
    logger.info("=" * 80)

    # Конфигурация
    vectordb_dir = project_root / "vector-db-test/vectordb"
    model_name = "intfloat/multilingual-e5-base"
    output_dir = vectordb_dir / "unified_all_docs_e5-base"

    # Проверяем входную директорию
    if not vectordb_dir.exists():
        logger.error(f"❌ Директория не найдена: {vectordb_dir}")
        return False

    # Находим все директории с векторными БД
    db_dirs = sorted([d for d in vectordb_dir.iterdir() if d.is_dir() and not d.name.startswith('.')])

    if not db_dirs:
        logger.error("❌ Векторные БД не найдены!")
        return False

    logger.info(f"📁 Найдено {len(db_dirs)} векторных БД")

    # Загружаем модель
    logger.info(f"📦 Загрузка модели: {model_name}")
    model = SentenceTransformer(model_name)
    embeddings = SentenceTransformerEmbeddings(model)
    logger.info("✅ Модель загружена")

    # Загружаем все БД
    vector_stores = []
    total_vectors = 0

    logger.info("\n" + "=" * 80)
    logger.info("ЗАГРУЗКА ВЕКТОРНЫХ БАЗ")
    logger.info("=" * 80)

    for i, db_dir in enumerate(db_dirs, 1):
        db_name = db_dir.name
        logger.info(f"\n[{i}/{len(db_dirs)}] Загрузка: {db_name}")

        try:
            # Загружаем FAISS индекс
            vector_store = FAISS.load_local(
                str(db_dir),
                embeddings,
                allow_dangerous_deserialization=True
            )

            num_vectors = vector_store.index.ntotal
            total_vectors += num_vectors
            logger.info(f"  ├─ Векторов: {num_vectors}")
            logger.info(f"  └─ ✅ Загружено")

            vector_stores.append(vector_store)

        except Exception as e:
            logger.error(f"  ❌ Ошибка загрузки {db_name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    if not vector_stores:
        logger.error("\n❌ Не удалось загрузить ни одной векторной БД!")
        return False

    logger.info("\n" + "=" * 80)
    logger.info("СТАТИСТИКА ОБЪЕДИНЕНИЯ")
    logger.info("=" * 80)
    logger.info(f"Всего БД обработано: {len(vector_stores)}")
    logger.info(f"Всего векторов: {total_vectors}")
    logger.info(f"Размерность векторов: {vector_stores[0].index.d}")

    # Создаем объединенную векторную БД
    logger.info("\n" + "=" * 80)
    logger.info("ОБЪЕДИНЕНИЕ ИНДЕКСОВ")
    logger.info("=" * 80)

    try:
        # Используем метод merge_from для объединения FAISS индексов
        unified_store = vector_stores[0]

        logger.info(f"Базовая БД: {db_dirs[0].name} ({unified_store.index.ntotal} векторов)")

        for i in range(1, len(vector_stores)):
            db_name = db_dirs[i].name
            vectors_count = vector_stores[i].index.ntotal
            logger.info(f"Добавляем: {db_name} ({vectors_count} векторов)...")

            # Объединяем индексы
            unified_store.index.merge_from(vector_stores[i].index)

            # Добавляем документы в docstore БЕЗ добавления в индекс
            for doc_id in vector_stores[i].index_to_docstore_id.values():
                try:
                    doc = vector_stores[i].docstore.search(doc_id)
                    if doc:
                        # Добавляем метаданные о документе
                        if hasattr(doc, 'metadata'):
                            doc.metadata['source_db'] = db_dirs[i].name
                        # Добавляем ТОЛЬКО в docstore, НЕ в индекс (избегаем дубликатов)
                        new_doc_id = str(len(unified_store.index_to_docstore_id))
                        unified_store.docstore.add({new_doc_id: doc})
                except Exception as e:
                    logger.warning(f"  ⚠️ Ошибка добавления документа: {e}")
                    continue

        logger.info(f"\n✅ Объединенный индекс: {unified_store.index.ntotal} векторов")

        # Сохраняем объединенную БД
        logger.info(f"\n💾 Сохранение в: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

        unified_store.save_local(str(output_dir))
        logger.info("✅ Объединенная векторная БД сохранена")

        # Создаем отчет
        report = {
            "unified_db_path": str(output_dir),
            "model": model_name,
            "total_vectors": int(unified_store.index.ntotal),
            "dimension": int(unified_store.index.d),
            "source_dbs": {
                "count": len(db_dirs),
                "names": [d.name for d in db_dirs]
            },
            "created_at": str(Path.cwd())
        }

        report_file = project_root / "vector-db-test/unified_db_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"📊 Отчет сохранен: {report_file}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ ОБЪЕДИНЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        logger.info("=" * 80)
        logger.info(f"📁 Путь к объединенной БД: {output_dir}")
        logger.info(f"📊 Всего векторов: {unified_store.index.ntotal}")
        logger.info(f"📦 Модель: {model_name}")
        logger.info(f"📄 Исходных БД: {len(db_dirs)}")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при объединении: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = merge_vector_dbs()
    sys.exit(0 if success else 1)
