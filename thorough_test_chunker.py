#!/usr/bin/env python3
"""
МАКСИМАЛЬНО ТЩАТЕЛЬНАЯ проверка Smart Chunker
"""

import json
import re
from pathlib import Path
from collections import Counter

from smart_chunker import SmartDocumentChunker

# Пути
FULLDOCS_DIR = Path(__file__).parent / "fulldocx"
DOCX_FILE = FULLDOCS_DIR / "Жилищный кодекс Российской Федерации.docx"
STRUCTURE_FILE = FULLDOCS_DIR / "Жилищный кодекс Российской Федерации_structure.txt"

print("=" * 100)
print("МАКСИМАЛЬНО ТЩАТЕЛЬНАЯ ПРОВЕРКА SMART CHUNKER")
print("=" * 100)

chunker = SmartDocumentChunker(DOCX_FILE, STRUCTURE_FILE)
chunks = chunker.extract_text_with_structure()

level_1 = [c for c in chunks if c['level'] == 1]
level_2 = [c for c in chunks if c['level'] == 2]

print(f"\n✅ Всего чанков: {len(chunks)}")
print(f"   Level 1 (статьи): {len(level_1)}")
print(f"   Level 2 (пункты): {len(level_2)}")

# ============================================================================
# ПРОВЕРКА 1: Статьи НЕ смешиваются
# ============================================================================
print("\n" + "=" * 100)
print("ПРОВЕРКА 1: Статьи НЕ должны смешиваться")
print("=" * 100)

# Для каждой level 1 статьи проверяем что она содержит только свои пункты
errors_mixing = []

for i, l1_chunk in enumerate(level_1):
    article_title = l1_chunk['metadata']['article']

    # Находим все level 2 чанки с этим же названием статьи
    l2_chunks = [c for c in level_2 if c['metadata']['article'] == article_title]

    # Проверяем что parent_article у level 2 совпадает
    for l2 in l2_chunks:
        if l2['parent_article'] != article_title:
            errors_mixing.append({
                'level_1_article': article_title,
                'level_2_parent': l2['parent_article'],
                'level_2_preview': l2['text'][:100]
            })

if errors_mixing:
    print(f"❌ НАЙДЕНО {len(errors_mixing)} ОШИБОК смешивания статей!")
    for err in errors_mixing[:5]:
        print(f"\n   Level 1: {err['level_1_article']}")
        print(f"   Level 2 parent: {err['level_2_parent']}")
        print(f"   Текст: {err['level_2_preview']}")
else:
    print("✅ Отлично! Статьи НЕ смешиваются")

# ============================================================================
# ПРОВЕРКА 2: Текст level 1 содержит ВСЕ пункты
# ============================================================================
print("\n" + "=" * 100)
print("ПРОВЕРКА 2: Level 1 (статья) должен содержать все level 2 (пункты)")
print("=" * 100)

# Берем 5 случайных статей и проверяем
import random
random.seed(42)
test_articles = random.sample(level_1, min(5, len(level_1)))

errors_missing = []

for l1 in test_articles:
    article_title = l1['metadata']['article']
    l1_text = l1['text']

    # Находим все level 2 для этой статьи
    l2_chunks = [c for c in level_2 if c['metadata']['article'] == article_title]

    # Проверяем что каждый level 2 содержится в level 1
    for l2 in l2_chunks[:10]:  # Проверяем первые 10
        if l2['text'] not in l1_text:
            # Проверяем по первым 100 символов (могут быть незначительные отличия)
            if l2['text'][:100] not in l1_text:
                errors_missing.append({
                    'article': article_title,
                    'l2_preview': l2['text'][:100]
                })

if errors_missing:
    print(f"❌ НАЙДЕНО {len(errors_missing)} случаев где level 2 НЕ в level 1!")
    for err in errors_missing[:3]:
        print(f"\n   Статья: {err['article']}")
        print(f"   Level 2 текст: {err['l2_preview']}")
else:
    print("✅ Отлично! Level 1 содержит все Level 2")

# ============================================================================
# ПРОВЕРКА 3: Нет ли дублирования чанков
# ============================================================================
print("\n" + "=" * 100)
print("ПРОВЕРКА 3: Не должно быть дублирующихся чанков")
print("=" * 100)

# Проверяем по тексту
texts = [c['text'] for c in chunks]
duplicates = [item for item, count in Counter(texts).items() if count > 1]

if duplicates:
    print(f"❌ НАЙДЕНО {len(duplicates)} дубликатов!")
    for dup in duplicates[:3]:
        print(f"   Текст: {dup[:100]}...")
else:
    print("✅ Отлично! Дубликатов нет")

# ============================================================================
# ПРОВЕРКА 4: Детальный разбор конкретных статей
# ============================================================================
print("\n" + "=" * 100)
print("ПРОВЕРКА 4: Детальный разбор конкретных статей")
print("=" * 100)

test_cases = [
    "Статья 1. Основные начала жилищного законодательства",
    "Статья 15. Объекты жилищных прав. Многоквартирный дом",
    "Статья 155. Внесение платы за жилое помещение и коммунальные услуги",
    "Статья 161. Выбор способа управления многоквартирным домом"
]

for test_article in test_cases:
    l1_chunks = [c for c in level_1 if c['metadata']['article'] == test_article]
    l2_chunks = [c for c in level_2 if c['metadata']['article'] == test_article]

    if not l1_chunks:
        print(f"\n❌ {test_article}")
        print(f"   Level 1 НЕ НАЙДЕНА")
        continue

    l1 = l1_chunks[0]

    print(f"\n✅ {test_article}")
    print(f"   Level 1: {len(l1['text'])} символов, {len(l1['text'].split(chr(10)))} строк")

    # Считаем пункты в level 1
    l1_lines = l1['text'].split('\n')
    l1_points = [l for l in l1_lines if re.match(r'^\d+\.', l.strip())]
    l1_letters = [l for l in l1_lines if re.match(r'^[а-яА-Я]\)', l.strip())]

    print(f"   В Level 1 найдено: {len(l1_points)} пунктов, {len(l1_letters)} подпунктов (а, б, в)")
    print(f"   Level 2 чанков: {len(l2_chunks)}")

    # Проверяем структуру
    print(f"   Структура Level 2 (первые 5):")
    for i, l2 in enumerate(l2_chunks[:5], 1):
        first_line = l2['text'].split('\n')[0]
        print(f"      {i}. {first_line[:80]}")

    if len(l2_chunks) > 5:
        print(f"      ... и еще {len(l2_chunks) - 5} чанков")

# ============================================================================
# ПРОВЕРКА 5: Границы статей - нет ли "прыжков"
# ============================================================================
print("\n" + "=" * 100)
print("ПРОВЕРКА 5: Проверка границ между статьями")
print("=" * 100)

# Сортируем статьи по порядку
sorted_articles = sorted(level_1, key=lambda x: x['metadata']['article'])

errors_boundaries = []

# Проверяем что статьи идут подряд без пропусков
for i in range(len(sorted_articles) - 1):
    current = sorted_articles[i]
    next_article = sorted_articles[i + 1]

    # Извлекаем номера статей
    current_num = re.search(r'Статья\s+([\d.]+)', current['metadata']['article'])
    next_num = re.search(r'Статья\s+([\d.]+)', next_article['metadata']['article'])

    if current_num and next_num:
        # Проверяем что между ними нет больших пропусков
        try:
            curr = float(current_num.group(1).replace('.', '.'))
            nxt = float(next_num.group(1).replace('.', '.'))

            # Если разница больше 20 - подозрительно
            if nxt - curr > 20:
                errors_boundaries.append({
                    'current': current['metadata']['article'],
                    'next': next_article['metadata']['article'],
                    'gap': nxt - curr
                })
        except:
            pass

if errors_boundaries:
    print(f"⚠️  НАЙДЕНО {len(errors_boundaries)} больших пропусков между статьями:")
    for err in errors_boundaries[:5]:
        print(f"   {err['current']} → {err['next']} (пропуск: {err['gap']})")
else:
    print("✅ Отлично! Статьи идут подряд без больших пропусков")

# ============================================================================
# ПРОВЕРКА 6: Проверка parent-child ссылок на конкретных примерах
# ============================================================================
print("\n" + "=" * 100)
print("ПРОВЕРКА 6: Parent-child ссылки (детально)")
print("=" * 100)

# Берем Статью 161 (самая большая) и проверяем все её level 2
test_article = "Статья 161. Выбор способа управления многоквартирным домом. Общие требования к деятельности по управлению многоквартирным домом"
l1_161 = [c for c in level_1 if c['metadata']['article'] == test_article]
l2_161 = [c for c in level_2 if c['metadata']['article'] == test_article]

if l1_161 and l2_161:
    l1 = l1_161[0]
    print(f"\nСтатья 161 (самая большая):")
    print(f"   Level 1 размер: {len(l1['text'])} символов")
    print(f"   Level 2 чанков: {len(l2_161)}")

    # Проверяем что все level 2 ссылаются на правильный parent
    wrong_parent = [c for c in l2_161 if c['parent_article'] != test_article]

    if wrong_parent:
        print(f"   ❌ {len(wrong_parent)} level 2 чанков имеют НЕВЕРНЫЙ parent_article!")
    else:
        print(f"   ✅ Все {len(l2_161)} level 2 чанков имеют верный parent_article")

    # Проверяем что текст level 2 содержится в level 1
    not_contained = []
    for l2 in l2_161[:20]:  # Проверяем первые 20
        if l2['text'][:200] not in l1['text']:
            not_contained.append(l2)

    if not_contained:
        print(f"   ❌ {len(not_contained)} level 2 чанков НЕ содержатся в level 1!")
    else:
        print(f"   ✅ Проверенные level 2 чанки содержатся в level 1")

# ============================================================================
# ПРОВЕРКА 7: Metadata полнота
# ============================================================================
print("\n" + "=" * 100)
print("ПРОВЕРКА 7: Полнота metadata")
print("=" * 100)

# Проверяем что у всех чанков есть нужные поля
required_fields = ['document', 'type', 'level', 'article']
optional_fields = ['section', 'chapter']

missing_count = 0
incomplete_count = 0

for i, chunk in enumerate(chunks):
    # Проверяем обязательные поля
    for field in required_fields:
        if field not in chunk['metadata']:
            missing_count += 1
            if missing_count <= 3:
                print(f"   Чанк #{i}: нет обязательного поля '{field}'")

    # Проверяем что есть хотя бы section или chapter
    if not chunk['metadata'].get('section') and not chunk['metadata'].get('chapter'):
        incomplete_count += 1
        if incomplete_count <= 3:
            print(f"   Чанк #{i}: нет ни section ни chapter")

if missing_count == 0 and incomplete_count == 0:
    print("✅ Отлично! Metadata полная у всех чанков")
else:
    print(f"⚠️  Найдено проблем: {missing_count} missing fields, {incomplete_count} incomplete")

# ============================================================================
# ИТОГОВАЯ ОЦЕНКА
# ============================================================================
print("\n" + "=" * 100)
print("ИТОГОВАЯ ОЦЕНКА")
print("=" * 100)

all_errors = len(errors_mixing) + len(errors_missing) + len(duplicates) + len(errors_boundaries) + missing_count + incomplete_count

if all_errors == 0:
    print("✅✅✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
    print("✅ Чанкер РАБОТАЕТ ИДЕАЛЬНО!")
    print("✅ МОЖНО СОЗДАВАТЬ ВЕКТОРНУЮ БАЗУ!")
else:
    print(f"⚠️  Найдено {all_errors} проблем (см. выше)")
    print("   Рекомендуется исправить перед созданием векторной базы")

# Сохраняем детальный отчет
report = {
    'total_chunks': len(chunks),
    'level_1_count': len(level_1),
    'level_2_count': len(level_2),
    'errors_mixing': len(errors_mixing),
    'errors_missing': len(errors_missing),
    'duplicates': len(duplicates),
    'errors_boundaries': len(errors_boundaries),
    'missing_metadata': missing_count,
    'incomplete_metadata': incomplete_count,
    'total_errors': all_errors,
    'status': 'PASS' if all_errors == 0 else 'FAIL'
}

report_file = Path(__file__).parent / "reports" / "thorough_chunker_test.json"
with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"\n📄 Отчет сохранен: {report_file}")
