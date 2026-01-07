#!/usr/bin/env python3
"""
Обработка нормативных документов в векторные базы

Класс DocumentProcessor обрабатывает ОДИН документ:
- Разбивает на чанки через UniversalDocumentChunker
- Создает embeddings через SentenceTransformer
- Сохраняет в отдельную FAISS базу

Использование:
    from document_processor import DocumentProcessor

    processor = DocumentProcessor()
    success, message, stats = processor.process_document(docx_path, vectordb_dir)
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Tuple

# Добавляем путь к vector-db-test
sys.path.insert(0, str(Path(__file__).parent / "vector-db-test"))

from config import FULLDOCS_DIR, VECTORDB_DIR, EMBEDDING_MODEL, MIN_CHUNKS_COUNT, MIN_AVG_CHUNK_SIZE
from universal_chunker import UniversalDocumentChunker
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from utils.embeddings import SentenceTransformerEmbeddings

logger = logging.getLogger(__name__)


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


def main():
    """Обработка одного документа (интерактивно или через аргументы)"""

    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        # Передали имя файла как аргумент
        docx_name = sys.argv[1]
        docx_path = FULLDOCS_DIR / docx_name

        if not docx_path.exists():
            print(f"❌ Файл не найден: {docx_path}")
            return 1

        print(f"Обработка: {docx_path.name}")
        print()
    else:
        # Интерактивный режим
        # Находим все документы
        docx_files = sorted(FULLDOCS_DIR.glob("*.docx"))

        if not docx_files:
            print("❌ Документы не найдены")
            return 1

        print("=" * 80)
        print("ВЫБЕРИТЕ ДОКУМЕНТ ДЛЯ ОБРАБОТКИ")
        print("=" * 80)

        for i, docx in enumerate(docx_files, 1):
            print(f"{i:2d}. {docx.name}")

        print()
        choice = input("Введите номер документа: ").strip()

        if not choice.isdigit():
            print("❌ Неверный ввод")
            return 1

        idx = int(choice) - 1
        if idx < 0 or idx >= len(docx_files):
            print(f"❌ Неверный номер: {choice}")
            return 1

        docx_path = docx_files[idx]

        print()
        print(f"Обработка: {docx_path.name}")
        print()

    # Обрабатываем
    processor = DocumentProcessor()
    success, message, stats = processor.process_document(docx_path, VECTORDB_DIR)

    print()
    print("=" * 80)
    if success:
        print("✅ УСПЕХ!")
        print(f"   Чанков: {stats['chunks_count']}")
        print(f"   База: {stats['db_path']}")
    else:
        print(f"❌ ОШИБКА: {message}")
    print("=" * 80)

    return 0 if success else 1


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    sys.exit(main())
