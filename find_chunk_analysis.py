#!/usr/bin/env python3
"""
Анализ чанков ПП 354: поиск чанка с давлением 0,03 МПа
"""

import sys
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Путь к векторной базе
vectordb_path = Path("/home/olga/normativ_docs/Волков/vector-db-test/vectordb/ПП_РФ_от_06.05.2011_№_354_Правила_предоставления_коммунальных_услуг_Правила_№_354")

# Загружаю метаданные
index_path = vectordb_path / "index.pkl"
with open(index_path, 'rb') as f:
    index_data = pickle.load(f)

# Пробую разные структуры FAISS
print(f"Тип index_data: {type(index_data)}")

if isinstance(index_data, tuple):
    print(f"Размер tuple: {len(index_data)}")
    # Обычно tuple: (index_to_docstore_id, docstore)
    if len(index_data) >= 2:
        docstore = index_data[1]
    else:
        print("❌ Не удалось получить docstore из tuple")
        sys.exit(1)
elif hasattr(index_data, 'docstore'):
    docstore = index_data.docstore
else:
    print("❌ Неизвестная структура index.pkl")
    sys.exit(1)

# Получаю все документы
if isinstance(docstore, dict):
    docs_dict = docstore
elif hasattr(docstore, '_dict'):
    docs_dict = docstore._dict
elif hasattr(docstore, '_index'):
    docs_dict = {k: docstore._index.get(k) for k in docstore._index.keys() if hasattr(docstore._index, 'get')}
else:
    print(f"❌ Не удалось получить документы из docstore (тип: {type(docstore)})")
    sys.exit(1)

print(f"Всего документов в базе: {len(docs_dict)}")
print()

# Ищу чанки с "0,03 МПа"
print("=" * 80)
print("ПОИСК ЧАНКОВ С '0,03 МПа'")
print("=" * 80)
print()

found_chunks = []
for idx, (doc_id, doc) in enumerate(docs_dict.items(), 1):
    content = doc.page_content
    metadata = doc.metadata

    if "0,03 МПа" in content or "0.03 МПа" in content:
        found_chunks.append({
            'position': idx,
            'doc_id': doc_id,
            'content': content,
            'metadata': metadata,
            'length': len(content)
        })

print(f"Найдено чанков с '0,03 МПа': {len(found_chunks)}")
print()

# Показываю детали
for i, chunk in enumerate(found_chunks, 1):
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

# Если чанки не найдены, ищу "0,03"
if not found_chunks:
    print("❌ Чанки с '0,03 МПа' не найдены")
    print()
    print("Попробую найти просто '0,03'...")
    print()

    found_chunks = []
    for idx, (doc_id, doc) in enumerate(docs_dict.items(), 1):
        content = doc.page_content
        metadata = doc.metadata

        if "0,03" in content or "0.03" in content:
            found_chunks.append({
                'position': idx,
                'doc_id': doc_id,
                'content': content,
                'metadata': metadata,
                'length': len(content)
            })

    print(f"Найдено чанков с '0,03': {len(found_chunks)}")
    print()

    for i, chunk in enumerate(found_chunks[:5], 1):  # Первые 5
        print(f"{'='*80}")
        print(f"ЧАНК #{i} (позиция в базе: {chunk['position']})")
        print(f"{'='*80}")
        print(f"Документ: {chunk['metadata'].get('document', 'Unknown')}")
        print(f"Тип: {chunk['metadata'].get('type', 'Unknown')}")
        print(f"Приложение: {chunk['metadata'].get('app', 'Нет')}")
        print()
        print(f"СОДЕРЖИМОНИЕ:")
        print("-" * 80)
        print(chunk['content'][:600])
        if len(chunk['content']) > 600:
            print("...")
        print()

# Анализирую: почему эти чанки не находятся в топе
print()
print("=" * 80)
print("АНАЛИЗ: ПОЧЕМУ ЧАНКИ НЕ В ТОПЕ?")
print("=" * 80)
print()

if found_chunks:
    # Проверяю наличие keywords в чанках
    for i, chunk in enumerate(found_chunks, 1):
        content = chunk['content']
        has_keyword_water = 'вод' in content.lower()
        has_keyword_pressure = 'давлен' in content.lower()
        has_keyword_cold = 'холод' in content.lower()

        print(f"ЧАНК #{i} (позиция {chunk['position']}):")
        print(f"  ✓ Ключевые слова:")
        print(f"    - 'вод': {has_keyword_water}")
        print(f"    - 'давлен': {has_keyword_pressure}")
        print(f"    - 'холод': {has_keyword_cold}")
        print(f"  ✓ Ключевые слова в начале чанка:")
        first_200 = content[:200].lower()
        print(f"    {first_200}")
        print()
