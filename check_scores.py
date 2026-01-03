#!/usr/bin/env python3
"""
Проверка embedding scores для поиска
"""

import sys
import numpy as np
from pathlib import Path
from typing import List

# Добавляем путь к vector-db-test
sys.path.insert(0, str(Path(__file__).parent / "vector-db-test"))

from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings


class SentenceTransformerEmbeddings(Embeddings):
    """Обертка для SentenceTransformer"""

    def __init__(self, model: SentenceTransformer):
        self.model = model

    def embed_documents(self, texts):
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode([text], show_progress_bar=False)[0]
        return embedding.tolist()


def check_scores():
    """Проверяет embedding scores"""

    # Загружаем векторную БД
    vectordb_path = Path("/home/olga/normativ_docs/Волков/vector-db-test/vectordb/unified_all_docs_e5")

    print(f"📂 Загрузка векторной БД из: {vectordb_path}")

    # Загружаем модель
    print("📦 Загрузка модели intfloat/multilingual-e5-small...")
    model = SentenceTransformer("intfloat/multilingual-e5-small")
    embeddings = SentenceTransformerEmbeddings(model)

    # Загружаем FAISS
    vectorstore = FAISS.load_local(
        str(vectordb_path),
        embeddings=embeddings,
        allow_dangerous_deserialization=True
    )

    print("✓ Векторная БД загружена")
    print()

    # Проверяем запрос "Что такое залог?"
    question = "Что такое залог?"
    print(f"ВОПРОС: {question}")
    print()

    # Делаем поиск с scores
    results_with_scores = vectorstore.similarity_search_with_score(question, k=15)

    print("ТОП-15 РЕЗУЛЬТАТОВ С SCORES:")
    print("=" * 80)

    for i, (doc, score) in enumerate(results_with_scores, 1):
        article = doc.metadata.get('article', 'Нет')
        chapter = doc.metadata.get('chapter', 'Нет')

        # Конвертируем score из дистанции в сходство
        # FAISS возвращает L2 дистанцию, чем меньше - тем лучше
        # Для сходства можно использовать 1 / (1 + distance)
        similarity = 1 / (1 + score)

        marker = ""
        if 'Статья 334' in article:
            marker = " ✅ ИСКОМАЯ СТАТЬЯ!"
        elif 'Глава 23' in chapter:
            marker = " ⭐ Правильная глава"

        print(f"{i}. {article}")
        print(f"   {chapter}")
        print(f"   Score (L2 distance): {score:.4f}")
        print(f"   Similarity: {similarity:.4f}{marker}")
        print(f"   Текст: {doc.page_content[:100]}...")
        print()


if __name__ == '__main__':
    check_scores()
