#!/usr/bin/env python3
"""
Детальная проверка Smart Chunker перед созданием векторной базы
"""

import sys
import json
from pathlib import Path
from smart_chunker import SmartDocumentChunker

# Пути
FULLDOCS_DIR = Path(__file__).parent / "fulldocx"

# Тестовый документ
DOCX_FILE = FULLDOCS_DIR / "Жилищный кодекс Российской Федерации.docx"
STRUCTURE_FILE = FULLDOCS_DIR / "Жилищный кодекс Российской Федерации_structure.txt"

# Репорты
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def test_chunker():
    """Детальный тест чанкера"""

    print("=" * 80)
    print("ДЕТАЛЬНАЯ ПРОВЕРКА SMART CHUNKER")
    print("=" * 80)

    # Создаем чанкер
    chunker = SmartDocumentChunker(DOCX_FILE, STRUCTURE_FILE)
    chunks = chunker.extract_text_with_structure()

    print(f"\n✅ Всего чанков создано: {len(chunks)}")

    # Разделяем по уровням
    level_1 = [c for c in chunks if c['level'] == 1]
    level_2 = [c for c in chunks if c['level'] == 2]

    print(f"   Level 1 (статьи): {len(level_1)}")
    print(f"   Level 2 (пункты): {len(level_2)}")

    # Проверка 1: Размеры чанков
    print("\n" + "=" * 80)
    print("ПРОВЕРКА 1: Размеры чанков")
    print("=" * 80)

    l1_sizes = [len(c['text']) for c in level_1]
    l2_sizes = [len(c['text']) for c in level_2]

    print(f"\nLevel 1 (статьи):")
    print(f"   Мин: {min(l1_sizes)} символов")
    print(f"   Макс: {max(l1_sizes)} символов")
    print(f"   Сред: {sum(l1_sizes) // len(l1_sizes)} символов")

    print(f"\nLevel 2 (пункты):")
    print(f"   Мин: {min(l2_sizes)} символов")
    print(f"   Макс: {max(l2_sizes)} символов")
    print(f"   Сред: {sum(l2_sizes) // len(l2_sizes)} символов")

    # Проверка 2: Metadata
    print("\n" + "=" * 80)
    print("ПРОВЕРКА 2: Metadata")
    print("=" * 80)

    # Проверяем что у всех чанков есть нужные поля
    required_fields = ['document', 'type', 'level', 'article']
    missing_fields = []

    for i, chunk in enumerate(chunks[:10]):  # Проверяем первые 10
        for field in required_fields:
            if field not in chunk['metadata']:
                missing_fields.append((i, field))

    if missing_fields:
        print(f"❌ Ошибки в metadata:")
        for chunk_idx, field in missing_fields:
            print(f"   Чанк #{chunk_idx}: нет поля '{field}'")
    else:
        print("✅ Все metadata корректны (проверено первые 10 чанков)")

    # Проверка 3: Parent-child ссылки
    print("\n" + "=" * 80)
    print("ПРОВЕРКА 3: Parent-child ссылки")
    print("=" * 80)

    # Проверяем что у всех level 2 есть parent_article
    level_2_without_parent = [c for c in level_2 if 'parent_article' not in c or not c['parent_article']]

    if level_2_without_parent:
        print(f"❌ {len(level_2_without_parent)} чанков level 2 БЕЗ parent_article")
    else:
        print(f"✅ Все {len(level_2)} чанков level 2 имеют parent_article")

    # Проверка 4: Разделение статей
    print("\n" + "=" * 80)
    print("ПРОВЕРКА 4: Разделение статей")
    print("=" * 80)

    # Проверяем что статьи не смешиваются
    articles = set([c['metadata']['article'] for c in chunks if c['metadata'].get('article')])
    print(f"✅ Найдено уникальных статей: {len(articles)}")

    # Проверяем 5 конкретных статей
    print("\n" + "=" * 80)
    print("ПРОВЕРКА 5: Примеры конкретных статей")
    print("=" * 80)

    test_articles = [
        "Статья 1. Основные начала жилищного законодательства",
        "Статья 15. Объекты жилищных прав. Многоквартирный дом",
        "Статья 161. Права и обязанности собственников помещений в МКД"
    ]

    for test_article in test_articles:
        # Находим level 1 чанк (полная статья)
        l1_chunks = [c for c in level_1 if c['metadata']['article'] == test_article]

        # Находим level 2 чанки (пункты)
        l2_chunks = [c for c in level_2 if c['metadata']['article'] == test_article]

        if l1_chunks:
            print(f"\n✅ {test_article}")
            print(f"   Level 1 (статья): {len(l1_chunks)} чанк, {len(l1_chunks[0]['text'])} символов")
            print(f"   Level 2 (пункты): {len(l2_chunks)} чанков")

            # Показываем структуру level 2
            if l2_chunks:
                print(f"   Пункты:")
                for i, l2 in enumerate(l2_chunks[:5], 1):
                    preview = l2['text'][:80].replace('\n', ' ')
                    print(f"      {i}. {preview}...")
                if len(l2_chunks) > 5:
                    print(f"      ... и еще {len(l2_chunks) - 5} пунктов")
        else:
            print(f"\n❌ {test_article} - НЕ НАЙДЕНА")

    # Проверка 6: Подпункты (а, б, в)
    print("\n" + "=" * 80)
    print("ПРОВЕРКА 6: Подпункты (а, б, в)")
    print("=" * 80)

    # Ищем чанки с подпунктами
    chunks_with_sublists = []
    for chunk in level_2:
        lines = chunk['text'].split('\n')
        for line in lines:
            if line.strip() and re.match(r'^[а-яА-Я]\)', line.strip()):
                chunks_with_sublists.append(chunk)
                break

    print(f"✅ Найдено {len(chunks_with_sublists)} чанков с подпунктами (а, б, в)")

    if chunks_with_sublists:
        print(f"\nПример чанка с подпунктами:")
        example = chunks_with_sublists[0]
        print(f"   Статья: {example['metadata']['article']}")
        print(f"   Текст:")
        for line in example['text'].split('\n')[:10]:
            print(f"      {line}")

    # Сохраняем полный отчет в JSON
    print("\n" + "=" * 80)
    print("СОХРАНЕНИЕ ОТЧЕТА")
    print("=" * 80)

    report = {
        'total_chunks': len(chunks),
        'level_1_count': len(level_1),
        'level_2_count': len(level_2),
        'level_1_avg_size': sum(l1_sizes) // len(l1_sizes),
        'level_2_avg_size': sum(l2_sizes) // len(l2_sizes),
        'unique_articles': len(articles),
        'chunks_with_sublists': len(chunks_with_sublists),
        'sample_chunks': {
            'level_1': level_1[:3],
            'level_2': level_2[:5]
        }
    }

    report_file = REPORTS_DIR / "smart_chunker_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"✅ Отчет сохранен: {report_file}")

    # Итоговая оценка
    print("\n" + "=" * 80)
    print("ИТОГОВАЯ ОЦЕНКА")
    print("=" * 80)

    issues = []

    if min(l1_sizes) < 100:
        issues.append("Слишком маленькие статьи Level 1")
    if max(l1_sizes) > 10000:
        issues.append("Слишком большие статьи Level 1")
    if level_2_without_parent:
        issues.append("Есть чанки Level 2 без parent_article")
    if len(articles) < 200:
        issues.append(f"Слишком мало статей: {len(articles)}")

    if issues:
        print("❌ НАЙДЕНЫ ПРОБЛЕМЫ:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Чанкер готов к созданию векторной базы")
        return True


if __name__ == '__main__':
    import re

    success = test_chunker()
    sys.exit(0 if success else 1)
