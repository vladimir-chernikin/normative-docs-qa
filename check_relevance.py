#!/usr/bin/env python3
"""
Проверка релевантности найденных фрагментов
"""

import sys
import json
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


def check_relevance():
    """Проверяет релевантность поиска"""

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

    # Тестовые вопросы с ожидаемыми статьями
    test_cases = [
        {
            "question": "Что такое юридическое лицо?",
            "expected_chapter": "Глава 4. Юридические лица",
            "expected_article": "Статья 48. Понятие юридического лица"
        },
        {
            "question": "Что такое залог?",
            "expected_chapter": "Глава 23. Обеспечение исполнения обязательств",
            "expected_article": "Статья 334. Понятие залога"
        },
        {
            "question": "Что такое иск и как он предъявляется?",
            "expected_chapter": "Глава 12. Исковая давность",
            "expected_article": None  # Может быть не найдено
        },
        {
            "question": "Какие есть способы обеспечения исполнения обязательств?",
            "expected_chapter": "Глава 23. Обеспечение исполнения обязательств",
            "expected_article": "Статья 329. Способы обеспечения исполнения обязательств"
        }
    ]

    print("=" * 80)
    print("ПРОВЕРКА РЕЛЕВАНТНОСТИ ПОИСКА")
    print("=" * 80)
    print()

    for i, test_case in enumerate(test_cases, 1):
        question = test_case["question"]
        expected_chapter = test_case["expected_chapter"]
        expected_article = test_case["expected_article"]

        print(f"ТЕСТ #{i}")
        print(f"ВОПРОС: {question}")
        print()

        # Ищем с k=5 и k=10
        for k in [3, 5, 10]:
            results = vectorstore.similarity_search(question, k=k)

            print(f"🔍 Поиск top-{k}:")

            # Проверяем, есть ли ожидаемая глава/статья
            found_chapter = False
            found_article = False

            for j, result in enumerate(results, 1):
                chapter = result.metadata.get('chapter', '')
                article = result.metadata.get('article', '')

                is_expected_chapter = expected_chapter and expected_chapter in chapter
                is_expected_article = expected_article and expected_article == article

                if is_expected_chapter:
                    found_chapter = True
                if is_expected_article:
                    found_article = True

                # Маркируем ожидаемые результаты
                marker = ""
                if is_expected_article:
                    marker = " ✅ ОЖИДАЕТСЯ"
                elif is_expected_chapter:
                    marker = " ⭐ ОЖИДАЕМАЯ ГЛАВА"

                print(f"  {j}. {article}")
                print(f"     {chapter}{marker}")
                print(f"     {result.page_content[:150]}...")
                print()

            # Результат проверки
            if expected_article:
                if found_article:
                    print(f"✅ Ожидаемая статья НАЙДЕНА в top-{k}")
                else:
                    print(f"❌ Ожидаемая статья НЕ НАЙДЕНА в top-{k}")
            elif expected_chapter:
                if found_chapter:
                    print(f"✅ Ожидаемая глава НАЙДЕНА в top-{k}")
                else:
                    print(f"❌ Ожидаемая глава НЕ НАЙДЕНА в top-{k}")

            print()

        print("-" * 80)
        print()


if __name__ == '__main__':
    check_relevance()
