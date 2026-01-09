#!/usr/bin/env python3
"""
Простой поиск чанков с '0,03' через grep
"""

import os
import subprocess
from pathlib import Path

# Временный файл: экспортирую все чанки в текст
vectordb_path = Path("/home/olga/normativ_docs/Волков/vector-db-test/vectordb/ПП_РФ_от_06.05.2011_№_354_Правила_предоставления_коммунальных_услуг_Правила_№_354")

# Способ 1: через Python с langchain
try:
    from langchain_community.vectorstores import FAISS
    from sentence_transformers import SentenceTransformer
    from utils.embeddings import SentenceTransformerEmbeddings

    # Загружаю модель
    print("Загружаю модель эмбеддингов...")
    model = SentenceTransformer("intfloat/multilingual-e5-base")
    embeddings = SentenceTransformerEmbeddings(model)

    # Загружаю векторную базу
    print("Загружаю векторную базу...")
    vectorstore = FAISS.load_local(str(vectordb_path), embeddings, allow_dangerous_deserialization=True)

    # Получаю все документы
    print("Извлекаю все документы...")
    # В LangChain FAISS документы хранятся в docstore
    if hasattr(vectorstore, 'docstore'):
        docs = vectorstore.docstore._dict.values()
    else:
        print("❌ Не удалось получить документы")
        exit(1)

    print(f"Всего документов: {len(docs)}")
    print()

    # Ищу чанки с "0,03"
    print("=" * 80)
    print("ПОИСК ЧАНКОВ С '0,03'")
    print("=" * 80)
    print()

    found_chunks = []
    for idx, doc in enumerate(docs, 1):
        content = doc.page_content
        metadata = doc.metadata

        if "0,03" in content or "0.03" in content:
            found_chunks.append({
                'position': idx,
                'content': content,
                'metadata': metadata,
                'length': len(content)
            })

    print(f"Найдено чанков с '0,03': {len(found_chunks)}")
    print()

    # Показываю первые 5
    for i, chunk in enumerate(found_chunks[:5], 1):
        print(f"{'='*80}")
        print(f"ЧАНК #{i} (позиция в базе: {chunk['position']})")
        print(f"{'='*80}")
        print(f"Документ: {chunk['metadata'].get('document', 'Unknown')}")
        print(f"Тип: {chunk['metadata'].get('type', 'Unknown')}")
        print(f"Приложение: {chunk['metadata'].get('app', 'Нет')}")
        print(f"Размер: {chunk['length']} символов")
        print()
        print(f"СОДЕРЖИМОНИЕ:")
        print("-" * 80)
        print(chunk['content'][:800])
        if len(chunk['content']) > 800:
            print("...")
        print()

    # Если чанки не найдены, ищу related keywords
    if not found_chunks:
        print("❌ Чанки с '0,03' не найдены")
        print()
        print("Ищу чанки со словами 'давление' + 'МПа'...")
        print()

        found_chunks = []
        for idx, doc in enumerate(docs, 1):
            content = doc.page_content
            metadata = doc.metadata

            if 'давлен' in content.lower() and 'мпа' in content.lower():
                found_chunks.append({
                    'position': idx,
                    'content': content,
                    'metadata': metadata,
                    'length': len(content)
                })

        print(f"Найдено чанков с 'давление' + 'МПа': {len(found_chunks)}")
        print()

        for i, chunk in enumerate(found_chunks[:5], 1):
            print(f"{'='*80}")
            print(f"ЧАНК #{i} (позиция в базе: {chunk['position']})")
            print(f"{'='*80}")
            print(f"Документ: {chunk['metadata'].get('document', 'Unknown')}")
            print(f"Приложение: {chunk['metadata'].get('app', 'Нет')}")
            print()
            print(f"СОДЕРЖИМОНИЕ:")
            print("-" * 80)
            print(chunk['content'][:800])
            if len(chunk['content']) > 800:
                print("...")
            print()

except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
