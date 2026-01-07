#!/usr/bin/env python3
"""
Скрипт для создания векторной базы из .txt файлов
Разбивает документы на чанки, создает эмбеддинги, сохраняет в FAISS
"""

import os
import sys
from pathlib import Path
from typing import List
import logging

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    # Импортируем из utils
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.embeddings import SentenceTransformerEmbeddings
except ImportError as e:
    logger.error(f"Ошибка импорта: {e}")
    logger.error("Установите зависимости: pip install sentence-transformers langchain-community faiss-cpu")
    sys.exit(1)


class VectorDBCreator:
    """Создание векторной базы из .txt файлов"""

    def __init__(self,
                 source_dir: str,
                 output_dir: str,
                 model_name: str = "cointegrated/rubert-tiny2"):
        """
        Args:
            source_dir: Папка с .txt файлами
            output_dir: Папка для сохранения FAISS индекса
            model_name: Название модели для эмбеддингов
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.model_name = model_name

        # Создаем папку для вывода
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Загружаем модель
        logger.info(f"Загрузка модели: {model_name}")
        st_model = SentenceTransformer(model_name)
        logger.info(f"Модель загружена (размер embeddings: {st_model.get_sentence_embedding_dimension()})")

        # Оборачиваем в LangChain совместимый класс
        self.embeddings = SentenceTransformerEmbeddings(st_model)

        # Текст сплиттер для разбивки на чанки
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Размер чанка в символах
            chunk_overlap=200,  # Перекрытие чанков
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def read_txt_files(self) -> List[tuple]:
        """Читает все .txt файлы из папки

        Returns:
            Список кортежей (имя_файла, содержимое)
        """
        txt_files = list(self.source_dir.glob("*.txt"))
        logger.info(f"Найдено {len(txt_files)} .txt файлов")

        documents = []
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                documents.append((txt_file.stem, content))
                logger.info(f"  Загружен: {txt_file.name} ({len(content)} символов)")
            except Exception as e:
                logger.error(f"Ошибка чтения {txt_file}: {e}")

        return documents

    def split_text_into_chunks(self, text: str, source_name: str) -> List[Document]:
        """Разбивает текст на чанки

        Args:
            text: Исходный текст
            source_name: Имя исходного файла

        Returns:
            Список Document объектов
        """
        chunks = self.text_splitter.split_text(text)

        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "source_file": source_name,
                    "chunk_id": str(i),
                    "hierarchy_path": source_name
                }
            )
            documents.append(doc)

        return documents

    def create_vector_store(self, documents: List[Document]) -> FAISS:
        """Создает FAISS векторное хранилище

        Args:
            documents: Список Document объектов

        Returns:
            FAISS объект
        """
        logger.info(f"Создание векторного хранилища из {len(documents)} документов...")

        # Создаем FAISS индекс
        vector_store = FAISS.from_documents(
            documents=documents,
            embedding=self.embeddings
        )

        logger.info("Векторное хранилище создано")
        return vector_store

    def save_vector_store(self, vector_store: FAISS, name: str):
        """Сохраняет FAISS индекс в папку

        Args:
            vector_store: FAISS объект
            name: Название индекса (без расширения)
        """
        index_path = self.output_dir / name
        vector_store.save_local(str(index_path))
        logger.info(f"Индекс сохранен: {index_path}")

    def create(self, index_name: str = "rubert-tiny2-faiss"):
        """Основной метод создания векторной базы

        Args:
            index_name: Название сохраняемого индекса
        """
        # Шаг 1: Читаем .txt файлы
        documents = self.read_txt_files()

        if not documents:
            logger.error("Нет документов для обработки!")
            return

        # Шаг 2: Разбиваем на чанки
        logger.info("Разбиение документов на чанки...")
        all_chunks = []

        for file_name, content in documents:
            chunks = self.split_text_into_chunks(content, file_name)
            all_chunks.extend(chunks)
            logger.info(f"  {file_name}: {len(chunks)} чанков")

        logger.info(f"Всего чанков: {len(all_chunks)}")

        # Шаг 3: Создаем векторную базу
        vector_store = self.create_vector_store(all_chunks)

        # Шаг 4: Сохраняем
        self.save_vector_store(vector_store, index_name)

        logger.info("=" * 50)
        logger.info("ГОТОВО!")
        logger.info(f"Документов: {len(documents)}")
        logger.info(f"Чанков: {len(all_chunks)}")
        logger.info(f"Модель: {self.model_name}")
        logger.info(f"Индекс: {self.output_dir / index_name}")
        logger.info("=" * 50)


def main():
    """Главная функция"""
    import argparse

    parser = argparse.ArgumentParser(description="Создание векторной базы из .txt файлов")
    parser.add_argument(
        "--source",
        type=str,
        default="data/markdown_with_headers0",
        help="Папка с .txt файлами (по умолчанию: data/markdown_with_headers0)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="vectordb",
        help="Папка для сохранения индекса (по умолчанию: vectordb)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="cointegrated/rubert-tiny2",
        help="Модель для эмбеддингов (по умолчанию: cointegrated/rubert-tiny2)"
    )
    parser.add_argument(
        "--index-name",
        type=str,
        default="rubert-tiny2-faiss",
        help="Название индекса (по умолчанию: rubert-tiny2-faiss)"
    )

    args = parser.parse_args()

    # Переходим в папку проекта
    os.chdir(Path(__file__).parent)

    # Создаем векторную базу
    creator = VectorDBCreator(
        source_dir=args.source,
        output_dir=args.output,
        model_name=args.model
    )

    creator.create(index_name=args.index_name)


if __name__ == '__main__':
    main()
