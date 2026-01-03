#!/usr/bin/env python3
"""
Масштабирование на все нормативные документы
Автоматическая обработка с проверкой качества
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Tuple

# Добавляем путь к vector-db-test
sys.path.insert(0, str(Path(__file__).parent / "vector-db-test"))

from config import FULLDOCS_DIR, VECTORDB_DIR, REPORTS_DIR, EMBEDDING_MODEL, MIN_CHUNKS_COUNT, MIN_AVG_CHUNK_SIZE
from universal_chunker import UniversalDocumentChunker
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
import asyncio
import httpx

logger = logging.getLogger(__name__)


class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model: SentenceTransformer):
        self.model = model

    def embed_documents(self, texts):
        return self.model.encode(texts, show_progress_bar=False).tolist()

    def embed_query(self, text: str):
        return self.model.encode([text], show_progress_bar=False)[0].tolist()


class DocumentProcessor:
    """Процессор для одного документа"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or EMBEDDING_MODEL
        self.model = None
        self.embeddings = None

    def _load_model(self):
        """Ленивая загрузка модели"""
        if self.model is None:
            logger.info(f"Загрузка модели: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.embeddings = SentenceTransformerEmbeddings(self.model)
            logger.info("Модель загружена")

    def process_document(self, docx_path: Path, vectordb_dir: Path) -> Tuple[bool, str, dict]:
        """Обрабатывает один документ: чанки + embeddings"""

        doc_name = docx_path.stem
        # Структура может быть с или без .docx
        structure_path = Path(str(docx_path).replace('.docx', '_structure.txt'))

        if not structure_path.exists():
            return False, f"Структура не найдена: {structure_path}", {}

        logger.info(f"{'='*80}")
        logger.info(f"ОБРАБОТКА: {doc_name}")
        logger.info(f"{'='*80}")

        try:
            # 1. Создаем чанки
            logger.info("Этап 1: Создание чанков...")
            chunker = UniversalDocumentChunker(docx_path, structure_path)
            chunks = chunker.extract_chunks()

            if not chunks:
                return False, "Не создано ни одного чанка", {}

            logger.info(f"Создано {len(chunks)} чанков")

            # Валидация чанков
            if not self._validate_chunks(chunks):
                return False, "Валидация чанков не пройдена", {}

            # 2. Создаем embeddings
            logger.info("Этап 2: Создание embeddings...")
            self._load_model()

            # Формируем имя для векторной БД
            db_name = doc_name.replace(' ', '_').replace('(', '').replace(')', '').replace(',', '')
            output_dir = vectordb_dir / db_name

            # Создаем FAISS
            documents = []
            for chunk in chunks:
                doc = Document(
                    page_content=chunk['text'],
                    metadata=chunk['metadata']
                )
                documents.append(doc)

            vectorstore = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )

            # Сохраняем
            output_dir.mkdir(parents=True, exist_ok=True)
            vectorstore.save_local(str(output_dir))

            logger.info(f"Векторная БД сохранена: {output_dir}")

            # 3. Тестовый поиск
            logger.info("Этап 3: Тестовый поиск...")
            test_results = self._test_search(vectorstore, doc_name)

            stats = {
                'doc_name': doc_name,
                'chunks_count': len(chunks),
                'db_path': str(output_dir),
                'test_results': test_results
            }

            logger.info(f"{doc_name} - УСПЕХ!")

            return True, "OK", stats

        except Exception as e:
            error_msg = f"Ошибка: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}

    def _validate_chunks(self, chunks: List[dict]) -> bool:
        """Проверяет качество чанков"""

        if len(chunks) < MIN_CHUNKS_COUNT:
            logger.warning(f"Слишком мало чанков (< {MIN_CHUNKS_COUNT})")
            return False

        # Проверяем средний размер
        total_size = sum(len(c['text']) for c in chunks)
        avg_size = total_size / len(chunks)

        if avg_size < MIN_AVG_CHUNK_SIZE:
            logger.warning(f"Слишком маленькие чанки (средний: {avg_size})")
            return False

        logger.info(f"Валидация OK (средний размер: {avg_size:.0f} символов)")
        return True

    def _test_search(self, vectorstore, doc_name: str) -> dict:
        """Тестовый поиск"""

        # Простые тестовые запросы
        test_queries = ["Что такое", "Правила", "Обязанности"]

        results = {}
        for query in test_queries:
            try:
                search_results = vectorstore.similarity_search(query, k=3)
                results[query] = len(search_results)
            except Exception as e:
                logger.error(f"Ошибка поиска для '{query}': {e}")
                results[query] = 0

        logger.info(f"Тестовый поиск: {results}")
        return results


def process_all_documents():
    """Обрабатывает все документы"""

    # Пути из конфигурации
    fulldocx_dir = FULLDOCS_DIR
    vectordb_dir = VECTORDB_DIR

    # Находим все DOCX файлы
    docx_files = sorted(fulldocx_dir.glob("*.docx"))

    logger.info(f"Найдено {len(docx_files)} документов")

    # Фильтруем (пропускаем уже обработанные)
    processed = []
    failed = []

    processor = DocumentProcessor()

    for i, docx_file in enumerate(docx_files, 1):
        logger.info(f"{'#'*80}")
        logger.info(f"ДОКУМЕНТ {i} из {len(docx_files)}")
        logger.info(f"{'#'*80}")

        success, message, stats = processor.process_document(docx_file, vectordb_dir)

        if success:
            processed.append(stats)
            logger.info(f"ПРОЦЕСС: {len(processed)}/{len(docx_files)}")
        else:
            failed.append({
                'doc': docx_file.name,
                'error': message
            })
            logger.error(f"ПРОЦЕСС: {len(processed)}/{len(docx_files)} (ошибок: {len(failed)})")

    # Итоговый отчет
    logger.info("=" * 80)
    logger.info("ИТОГОВЫЙ ОТЧЕТ")
    logger.info("=" * 80)

    logger.info(f"Успешно обработано: {len(processed)}/{len(docx_files)}")
    logger.error(f"Ошибок: {len(failed)}/{len(docx_files)}")

    if processed:
        logger.info("ОБРАБОТАННЫЕ ДОКУМЕНТЫ:")
        for i, stat in enumerate(processed, 1):
            logger.info(f"{i}. {stat['doc_name']}")
            logger.info(f"   Чанков: {stat['chunks_count']}")
            logger.debug(f"   БД: {stat['db_path']}")

    if failed:
        logger.error("ОШИБКИ:")
        for fail in failed:
            logger.error(f"{fail['doc']}")
            logger.error(f"   Причина: {fail['error']}")

    # Сохраняем отчет
    report = {
        'total': len(docx_files),
        'processed': len(processed),
        'failed': len(failed),
        'processed_docs': processed,
        'failed_docs': failed
    }

    report_file = REPORTS_DIR / "processing_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"Отчет сохранен: {report_file}")


if __name__ == '__main__':
    process_all_documents()
