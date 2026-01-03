#!/usr/bin/env python3
"""
Создание единой векторной БД для всех нормативных документов
"""

import json
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from typing import List

from config import FULLDOCS_DIR, VECTORDB_DIR, EMBEDDING_MODEL
from universal_chunker import UniversalDocumentChunker

logger = logging.getLogger(__name__)


class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model: SentenceTransformer):
        self.model = model

    def embed_documents(self, texts):
        return self.model.encode(texts, show_progress_bar=True).tolist()

    def embed_query(self, text: str):
        return self.model.encode([text], show_progress_bar=False)[0].tolist()


def create_unified_db():
    """Создает единую БД из всех документов"""

    # Находим все DOCX файлы
    docx_files = sorted(FULLDOCS_DIR.glob("*.docx"))
    print(f"📂 Найдено документов: {len(docx_files)}")

    all_chunks = []

    # Обрабатываем каждый документ
    for i, docx_file in enumerate(docx_files, 1):
        print(f"\n[{i}/{len(docx_files)}] {docx_file.name}")

        structure_file = docx_file.with_name(docx_file.stem + '_structure.txt')

        if not structure_file.exists():
            print(f"   ⚠️ Структура не найдена, пропускаем")
            continue

        try:
            # Создаем чанки
            chunker = UniversalDocumentChunker(docx_file, structure_file)
            chunks = chunker.extract_chunks()
            
            print(f"   ✓ {len(chunks)} чанков")
            all_chunks.extend(chunks)

        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            continue

    print(f"\n📊 ВСЕГО ЧАНКОВ: {len(all_chunks)}")

    # Создаем документы для LangChain
    documents = []
    for chunk in all_chunks:
        doc = Document(
            page_content=chunk['text'],
            metadata=chunk['metadata']
        )
        documents.append(doc)

    # Загружаем модель
    print(f"\n📦 Загрузка модели: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = SentenceTransformerEmbeddings(model)
    print(f"✓ Модель загружена")

    # Создаем FAISS индекс
    print(f"💾 Создание единой БД из {len(documents)} чанков...")
    vectorstore = FAISS.from_documents(documents, embedding=embeddings)

    # Сохраняем
    output_dir = VECTORDB_DIR / "unified_all_docs_e5"
    output_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(output_dir))

    print(f"✓ БД сохранена: {output_dir}")

    # Тестовый поиск
    print("\n" + "=" * 80)
    print("ТЕСТОВЫЙ ПОИСК")
    print("=" * 80)

    test_queries = [
        "Что такое юридическое лицо?",
        "Какие коммунальные услуги?",
        "Что такое многоквартирный дом?",
    ]

    for query in test_queries:
        print(f"\n🔍 {query}")
        results = vectorstore.similarity_search(query, k=2)
        
        for i, r in enumerate(results, 1):
            doc = r.metadata.get('document', 'Unknown')
            art = r.metadata.get('article', '')
            print(f"   {i}. [{doc}] {art}")
            print(f"      {r.page_content[:100]}...")

    print("\n✅ ГОТОВО!")


if __name__ == '__main__':
    create_unified_db()
