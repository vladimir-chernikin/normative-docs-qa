#!/usr/bin/env python3
"""
Создание embeddings для умных чанков с метаданными
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Добавляем путь к vector-db-test
sys.path.insert(0, str(Path(__file__).parent / "vector-db-test"))

from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
import numpy as np
import pickle


class SentenceTransformerEmbeddings(Embeddings):
    """Обертка для SentenceTransformer"""

    def __init__(self, model: SentenceTransformer):
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode([text], show_progress_bar=False)[0]
        return embedding.tolist()


class StructuredVectorDB:
    """Векторная БД с метаданными структуры"""

    def __init__(self, model_name: str = "intfloat/multilingual-e5-small"):
        print(f"📦 Загрузка модели: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embeddings = SentenceTransformerEmbeddings(self.model)

        print(f"✓ Модель загружена (размер: {self.model.get_sentence_embedding_dimension()})")

    def create_vector_db(self, chunks: List[Dict[str, Any]], output_path: Path):
        """Создает FAISS индекс из чанков"""

        print(f"📊 Создание векторной БД из {len(chunks)} чанков...")

        # Преобразуем чанки в LangChain Document format
        documents = []
        for chunk in chunks:
            doc = Document(
                page_content=chunk['text'],
                metadata=chunk['metadata']
            )
            documents.append(doc)

        # Создаем FAISS индекс
        print(f"💾 Создание FAISS индекса...")
        vectorstore = FAISS.from_documents(
            documents=documents,
            embedding=self.embeddings
        )

        # Сохраняем
        output_path.mkdir(parents=True, exist_ok=True)

        # FAISS индекс
        faiss_path = output_path / "index.faiss"
        vectorstore.save_local(str(output_path))

        print(f"✓ Векторная БД сохранена в: {output_path}")
        print(f"  - {faiss_path}")
        print(f"  - {output_path / 'index.pkl'}")

        return vectorstore

    def search(self, query: str, vectorstore, top_k: int = 3):
        """Поиск релевантных чанков"""

        print(f"🔍 Поиск: {query}")
        results = vectorstore.similarity_search(query, k=top_k)

        print(f"\n✓ Найдено {len(results)} релевантных фрагментов:\n")

        for i, result in enumerate(results, 1):
            print(f"ФРАГМЕНТ #{i}")
            print(f"  Документ: {result.metadata.get('document', 'Неизвестно')}")
            print(f"  Раздел: {result.metadata.get('division', 'Нет')}")
            print(f"  Глава: {result.metadata.get('chapter', 'Нет')}")
            print(f"  Статья: {result.metadata.get('article', 'Нет')}")
            print(f"  Текст (первые 300 символов): {result.page_content[:300]}...")
            print()


# Тестовый запуск
if __name__ == '__main__':
    # Пути
    chunks_file = Path("/home/olga/normativ_docs/Волков/reports/test_chunks_code.json")
    output_dir = Path("/home/olga/normativ_docs/Волков/vector-db-test/vectordb/Гражданский_кодекс_РФ_часть_1_e5")

    # Загружаем чанки
    print(f"📂 Загрузка чанков из: {chunks_file}")
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"✓ Загружено {len(chunks)} чанков")
    print()

    # Создаем векторную БД
    db = StructuredVectorDB()
    vectorstore = db.create_vector_db(chunks, output_dir)

    print()
    print("=" * 80)
    print("ТЕСТОВЫЙ ПОИСК")
    print("=" * 80)
    print()

    # Тестовые запросы для Части 2 (договоры, купля-продажа, аренда)
    test_queries = [
        "Что такое договор купли-продажи?",
        "Какие обязанности есть у продавца?",
        "Что такое договор аренды?",
        "Какие права есть у покупателя?",
        "Что такое договор поставки?",
    ]

    for query in test_queries:
        db.search(query, vectorstore, top_k=2)
        print("-" * 80)
        print()
