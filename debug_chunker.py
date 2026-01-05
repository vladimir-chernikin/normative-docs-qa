#!/usr/bin/env python3
"""
Debug проблем в Smart Chunker
"""

import json
from pathlib import Path
from smart_chunker import SmartDocumentChunker

# Пути
FULLDOCS_DIR = Path(__file__).parent / "fulldocx"
DOCX_FILE = FULLDOCS_DIR / "Жилищный кодекс Российской Федерации.docx"
STRUCTURE_FILE = FULLDOCS_DIR / "Жилищный кодекс Российской Федерации_structure.txt"

chunker = SmartDocumentChunker(DOCX_FILE, STRUCTURE_FILE)
chunks = chunker.extract_text_with_structure()

level_1 = [c for c in chunks if c['level'] == 1]
level_2 = [c for c in chunks if c['level'] == 2]

print("=" * 80)
print("ПРОБЛЕМА 1: Слишком маленькие статьи")
print("=" * 80)

# Находим статьи меньше 200 символов
small_articles = [c for c in level_1 if len(c['text']) < 200]

print(f"\nНайдено {len(small_articles)} статей < 200 символов:\n")
for i, article in enumerate(small_articles[:10], 1):
    print(f"{i}. {article['metadata']['article']}")
    print(f"   Размер: {len(article['text'])} символов")
    print(f"   Текст: {article['text'][:200]}")
    print()

print("=" * 80)
print("ПРОБЛЕМА 2: Слишком большие статьи")
print("=" * 80)

# Находим статьи больше 15000 символов
large_articles = [c for c in level_1 if len(c['text']) > 15000]

print(f"\nНайдено {len(large_articles)} статей > 15000 символов:\n")
for i, article in enumerate(large_articles[:5], 1):
    print(f"{i}. {article['metadata']['article']}")
    print(f"   Размер: {len(article['text'])} символов")
    print(f"   Глава: {article['metadata'].get('chapter', 'N/A')}")
    # Показываем первые 3 строки
    lines = article['text'].split('\n')[:5]
    print(f"   Начало:")
    for line in lines:
        print(f"      {line[:100]}")
    print()

print("=" * 80)
print("ПРОБЛЕМА 3: Статья 161 не найдена")
print("=" * 80)

# Ищем статьи с "161" в названии
articles_161 = [c for c in chunks if '161' in c['metadata'].get('article', '')]

print(f"\nНайдено {len(articles_161)} чанков с '161':\n")
for i, chunk in enumerate(articles_161[:5], 1):
    print(f"{i}. Level {chunk['level']}: {chunk['metadata']['article']}")
    print(f"   Размер: {len(chunk['text'])} символов")
    print()

# Если не нашли, ищем похожие
if not articles_161:
    print("❌ Статья 161 действительно не найдена!\n")

    # Ищем статьи 160, 162, 163
    for num in [160, 162, 163, 164, 165]:
        found = [c for c in chunks if f'Статья {num}' in c['metadata'].get('article', '')]
        if found:
            print(f"✅ Нашлась Статья {num}:")
            for f in found[:1]:
                print(f"   {f['metadata']['article']}")
            print()

print("=" * 80)
print("ПРОБЛЕМА 4: Подпункты (а, б, в)")
print("=" * 80)

# Ищем чанки где текст начинается с "а)" или "б)"
chunks_with_letters = []
for chunk in level_2:
    lines = chunk['text'].split('\n')
    for line in lines:
        stripped = line.strip()
        if stripped and len(stripped) > 2 and stripped[0] in 'abcdefghijklmnopqrstuvwxyzабвгдежзийклмнопрстуфхцчшщъыьэюя' and stripped[1] == ')':
            chunks_with_letters.append(chunk)
            break

print(f"\nНайдено {len(chunks_with_letters)} чанков с подпунктами (а, б, в):\n")

if chunks_with_letters:
    # Показываем примеры
    for i, chunk in enumerate(chunks_with_letters[:3], 1):
        print(f"{i}. {chunk['metadata']['article']}")
        # Находим строки с подпунктами
        lines = chunk['text'].split('\n')
        sublists = [l for l in lines if l.strip() and len(l.strip()) > 2 and l.strip()[0] in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' and l.strip()[1] == ')']
        print(f"   Подпунктов: {len(sublists)}")
        print(f"   Примеры:")
        for sl in sublists[:3]:
            print(f"      {sl[:100]}")
        print()
else:
    print("❌ Чанков с подпунктами не найдено")

print("\n" + "=" * 80)
print("ПРОВЕРКА: Первые 5 статей")
print("=" * 80)

for i, chunk in enumerate(level_1[:5], 1):
    print(f"\n{i}. {chunk['metadata']['article']}")
    print(f"   Размер: {len(chunk['text'])} символов")
    lines = chunk['text'].split('\n')
    print(f"   Строк: {len(lines)}")
    print(f"   Первые 3 строки:")
    for line in lines[:3]:
        print(f"      {line[:80]}")
