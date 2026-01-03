#!/usr/bin/env python3
"""
Тестовый скрипт для проверки поиска по векторной базе
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from typing import List

class SentenceTransformerEmbeddings(Embeddings):
    """Обертка для SentenceTransformer совместимая с LangChain"""

    def __init__(self, model: SentenceTransformer):
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, show_progress_bar=False).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.model.encode([text], show_progress_bar=False)[0].tolist()


def test_search():
    """Тестирует поиск статьи 196"""

    # Загружаем модель
    print("Загрузка модели...")
    st_model = SentenceTransformer("cointegrated/rubert-tiny2")
    embeddings = SentenceTransformerEmbeddings(st_model)

    # Загружаем векторную базу
    print("Загрузка векторной базы...")
    vector_store = FAISS.load_local(
        "vectordb/rubert-tiny2-faiss",
        embeddings,
        allow_dangerous_deserialization=True
    )

    # Тестируемые запросы
    queries = [
        "Какой срок исковой давности?",
        "Статья 196 ГК РФ",
        "срок давности по коммунальным платежам",
        "общий срок исковой давности составляет"
    ]

    print("\n" + "=" * 60)
    print("ТЕСТ ПОИСКА В ВЕКТОРНОЙ БАЗЕ")
    print("=" * 60)

    for query in queries:
        print(f"\n🔍 Запрос: {query}")
        print("-" * 60)

        # Ищем релевантные документы
        results = vector_store.similarity_search_with_score(query, k=3)

        for i, (doc, score) in enumerate(results, 1):
            # Конвертируем score (L2 distance) в процент
            similarity = 1.0 / (1.0 + float(score))
            relevance = min(99.99, similarity * 100)

            # Проверяем на статью 196
            is_art196 = "Статья 196" in doc.page_content or "196" in doc.page_content

            marker = "✅" if is_art196 else "  "
            print(f"{marker} Результат #{i} (релевантность: {relevance:.1f}%)")
            print(f"   Источник: {doc.metadata.get('source_file', 'N/A')}")

            # Показываем отрывок текста
            content_preview = doc.page_content[:200].replace('\n', ' ')
            print(f"   Текст: {content_preview}...")

            # Если нашли статью 196 - показываем полностью
            if is_art196:
                print("\n   🎉 НАЙДЕНА СТАТЬЯ 196!")
                # Находим строку со статьей
                lines = doc.page_content.split('\n')
                for line in lines:
                    if '196' in line or ('исковой давности' in line and 'срок' in line):
                        print(f"   📌 {line.strip()}")

        print()

    print("=" * 60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 60)


if __name__ == '__main__':
    test_search()
