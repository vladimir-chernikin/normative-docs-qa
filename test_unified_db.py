#!/usr/bin/env python3
"""
Тестирование единой векторной БД
"""

from pathlib import Path
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from typing import List


class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model: SentenceTransformer):
        self.model = model

    def embed_documents(self, texts):
        return self.model.encode(texts, show_progress_bar=False).tolist()

    def embed_query(self, text: str):
        return self.model.encode([text], show_progress_bar=False)[0].tolist()


def test_unified_db():
    """Тестирует единую БД"""

    # Загружаем БД
    db_path = Path("vector-db-test/vectordb/unified_all_docs_e5")
    
    print("📦 Загрузка модели...")
    model = SentenceTransformer("intfloat/multilingual-e5-small")
    embeddings = SentenceTransformerEmbeddings(model)
    
    print(f"📂 Загрузка БД из: {db_path}")
    vectorstore = FAISS.load_local(str(db_path), embeddings=embeddings, allow_dangerous_deserialization=True)
    print("✓ БД загружена\n")

    # Тестовые вопросы по разным документам
    test_questions = [
        {
            "question": "Что такое юридическое лицо?",
            "expected_doc": "Гражданский кодекс",
            "expected_article": "Статья 48"
        },
        {
            "question": "Что такое залог?",
            "expected_doc": "Гражданский кодекс",
            "expected_article": "Статья 334"
        },
        {
            "question": "Какие коммунальные услуги предоставляются?",
            "expected_doc": "Правила № 354",
            "expected_section": "Холодное водоснабжение"
        },
        {
            "question": "Как рассчитывается плата за коммунальные услуги?",
            "expected_doc": "Правила № 354"
        },
        {
            "question": "Что такое многоквартирный дом?",
            "expected_doc": "Жилищый кодекс"
        },
        {
            "question": "Какие права есть у собственника помещения?",
            "expected_doc": "Жилищый кодекс"
        },
        {
            "question": "Что такое общее имущество в МКД?",
            "expected_doc": "Правила 491"
        },
        {
            "question": "Как проводится общее собрание собственников?",
            "expected_doc": "Приказ 44"
        },
        {
            "question": "Что такое энергосбережение?",
            "expected_doc": "261-ФЗ"
        },
        {
            "question": "Какие права на персональные данные?",
            "expected_doc": "152-ФЗ"
        }
    ]

    print("=" * 80)
    print("ТЕСТИРОВАНИЕ ЕДИНОЙ БД")
    print("=" * 80)
    print(f"Всего вопросов: {len(test_questions)}\n")

    for i, test in enumerate(test_questions, 1):
        print(f"\n[ТЕСТ {i}/{len(test_questions)}]")
        print(f"ВОПРОС: {test['question']}")
        
        if 'expected_doc' in test:
            print(f"ОЖИДАЕТСЯ: {test.get('expected_doc', 'Любой')}")
        
        # Поиск
        results = vectorstore.similarity_search_with_score(test['question'], k=3)
        
        print(f"\nРЕЗУЛЬТАТЫ (top-3):")
        print("-" * 80)

        for j, (doc, score) in enumerate(results, 1):
            # Конвертируем score в сходство
            similarity = 1 / (1 + score)
            
            doc_name = doc.metadata.get('document', 'Неизвестно')
            article = doc.metadata.get('article', '')
            chapter = doc.metadata.get('chapter', '')
            
            # Проверяем соответствие ожиданиям
            expected = test.get('expected_doc', '')
            match = "✅" if expected and expected.lower() in doc_name.lower() else ""
            
            print(f"{j}. [{doc_name}] {match}")
            if article:
                print(f"   {article}")
            elif chapter:
                print(f"   {chapter}")
            print(f"   Схожесть: {similarity:.4f}")
            print(f"   Текст: {doc.page_content[:120]}...")
            print()

        print("-" * 80)

    print("\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")


if __name__ == '__main__':
    test_unified_db()
