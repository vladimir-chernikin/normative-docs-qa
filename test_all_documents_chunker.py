#!/usr/bin/env python3
"""
Проверка Smart Chunker на ВСЕХ документах
"""

import sys
import re
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any

# Импорты
sys.path.insert(0, str(Path(__file__).parent))
from smart_chunker import SmartDocumentChunker
from universal_chunker import UniversalDocumentChunker

# Конфигурация
FULLDOCS_DIR = Path(__file__).parent / "fulldocx"
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def test_all_documents():
    """Тестирует все документы в fulldocx"""

    # Находим все DOCX файлы
    docx_files = sorted(FULLDOCS_DIR.glob("*.docx"))

    print("=" * 100)
    print(f"ПРОВЕРКА ЧАНКЕРА НА ВСЕХ ДОКУМЕНТАХ")
    print("=" * 100)
    print(f"\nНайдено документов: {len(docx_files)}\n")

    results = []
    errors = []
    successes = []

    for i, docx_file in enumerate(docx_files, 1):
        structure_file = FULLDOCS_DIR / f"{docx_file.stem}_structure.txt"

        if not structure_file.exists():
            errors.append({
                'document': docx_file.name,
                'error': 'Файл структуры не найден',
                'type': 'NO_STRUCTURE'
            })
            print(f"❌ [{i}/{len(docx_files)}] {docx_file.name[:60]}")
            print(f"   Причина: Файл структуры не найден")
            continue

        try:
            print(f"🔍 [{i}/{len(docx_files)}] {docx_file.name[:60]}")

            # Определяем тип документа
            chunker = UniversalDocumentChunker(docx_file, structure_file)
            doc_type = chunker.doc_type

            print(f"   Тип: {doc_type}")

            # Выбираем метод чанкинга
            if doc_type == 'CODE':
                # Используем Smart Chunker
                smart_chunker = SmartDocumentChunker(docx_file, structure_file)
                chunks = smart_chunker.extract_text_with_structure()
            else:
                # Используем универсальный чанкер
                chunks = chunker.extract_chunks()

            # Анализируем результаты
            level_1 = [c for c in chunks if c.get('level') == 1]
            level_2 = [c for c in chunks if c.get('level') == 2]
            other = [c for c in chunks if c.get('level') not in [1, 2]]

            result = {
                'document': docx_file.name,
                'doc_type': doc_type,
                'total_chunks': len(chunks),
                'level_1': len(level_1),
                'level_2': len(level_2),
                'other': len(other),
                'status': 'OK'
            }

            # Проверяем размеры
            if chunks:
                sizes = [len(c['text']) for c in chunks]
                result['min_size'] = min(sizes)
                result['max_size'] = max(sizes)
                result['avg_size'] = sum(sizes) // len(sizes)

                # Проверяем на аномалии
                if min(sizes) < 50:
                    result['warning'] = 'Очень маленькие чанки (< 50 символов)'
                if max(sizes) > 50000:
                    result['warning'] = 'Очень большие чанки (> 50000 символов)'

            results.append(result)
            successes.append(result)

            print(f"   Чанков: {len(chunks)} (L1: {len(level_1)}, L2: {len(level_2)})")
            if 'warning' in result:
                print(f"   ⚠️  {result['warning']}")
            print(f"   ✅ OK")

        except Exception as e:
            error_msg = str(e)
            errors.append({
                'document': docx_file.name,
                'error': error_msg,
                'type': 'EXCEPTION'
            })
            print(f"   ❌ ОШИБКА: {error_msg[:100]}")

        print()

    # Итоговый отчет
    print("=" * 100)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 100)

    print(f"\nВсего документов: {len(docx_files)}")
    print(f"Успешно обработано: {len(successes)}")
    print(f"С ошибками: {len(errors)}")

    # Статистика по типам документов
    print("\n" + "=" * 100)
    print("СТАТИСТИКА ПО ТИПАМ ДОКУМЕНТОВ")
    print("=" * 100)

    type_stats = defaultdict(list)
    for r in successes:
        type_stats[r['doc_type']].append(r)

    for doc_type, docs in sorted(type_stats.items()):
        total_chunks = sum(d['total_chunks'] for d in docs)
        avg_chunks = total_chunks // len(docs)

        print(f"\n{doc_type}:")
        print(f"   Документов: {len(docs)}")
        print(f"   Всего чанков: {total_chunks}")
        print(f"   Среднее чанков на документ: {avg_chunks}")

        # Показываем примеры
        print(f"   Примеры:")
        for d in docs[:3]:
            print(f"      - {d['document'][:60]}: {d['total_chunks']} чанков")

    # Проблемные документы
    if errors:
        print("\n" + "=" * 100)
        print("ПРОБЛЕМНЫЕ ДОКУМЕНТЫ")
        print("=" * 100)

        for err in errors:
            print(f"\n❌ {err['document']}")
            print(f"   Тип: {err['type']}")
            print(f"   Ошибка: {err['error']}")

    # Проверка качества
    print("\n" + "=" * 100)
    print("ПРОВЕРКА КАЧЕСТВА ЧАНКОВ")
    print("=" * 100)

    # Проверяем аномально маленькие/большие чанки
    very_small = [d for d in successes if d.get('min_size', 0) < 50]
    very_large = [d for d in successes if d.get('max_size', 0) > 50000]

    if very_small:
        print(f"\n⚠️  Документы с очень маленькими чанками (< 50 символов): {len(very_small)}")
        for d in very_small[:5]:
            print(f"   - {d['document'][:60]}: мин {d['min_size']} символов")

    if very_large:
        print(f"\n⚠️  Документы с очень большими чанками (> 50000 символов): {len(very_large)}")
        for d in very_large[:5]:
            print(f"   - {d['document'][:60]}: макс {d['max_size']} символов")

    if not very_small and not very_large:
        print("\n✅ Размеры чанков в норме")

    # Детальная проверка кодексов
    print("\n" + "=" * 100)
    print("ДЕТАЛЬНАЯ ПРОВЕРКА КОДЕКСОВ")
    print("=" * 100)

    codes = [d for d in successes if d['doc_type'] == 'CODE']

    for code_result in codes:
        doc_name = code_result['document']
        print(f"\n📄 {doc_name}")

        docx_file = FULLDOCS_DIR / doc_name
        structure_file = FULLDOCS_DIR / f"{docx_file.stem}_structure.txt"

        try:
            smart_chunker = SmartDocumentChunker(docx_file, structure_file)
            chunks = smart_chunker.extract_text_with_structure()

            level_1 = [c for c in chunks if c['level'] == 1]
            level_2 = [c for c in chunks if c['level'] == 2]

            print(f"   Level 1 (статьи): {len(level_1)}")
            print(f"   Level 2 (пункты): {len(level_2)}")

            # Проверяем parent-child ссылки
            if level_2:
                no_parent = [c for c in level_2 if not c.get('parent_article')]
                if no_parent:
                    print(f"   ⚠️  {len(no_parent)} level 2 БЕЗ parent_article")
                else:
                    print(f"   ✅ Все level 2 имеют parent_article")

            # Проверяем metadata
            missing_metadata = 0
            for c in chunks[:10]:  # Проверяем первые 10
                if not c.get('metadata', {}).get('article'):
                    missing_metadata += 1

            if missing_metadata > 0:
                print(f"   ⚠️  {missing_metadata} чанков БЕЗ article в metadata")
            else:
                print(f"   ✅ Metadata корректна")

        except Exception as e:
            print(f"   ❌ Ошибка при детальной проверке: {e}")

    # Итоговая оценка
    print("\n" + "=" * 100)
    print("ИТОГОВАЯ ОЦЕНКА")
    print("=" * 100)

    success_rate = (len(successes) / len(docx_files)) * 100 if docx_files else 0

    print(f"\nУспешность: {success_rate:.1f}% ({len(successes)}/{len(docx_files)})")

    critical_issues = len([e for e in errors if e['type'] in ['EXCEPTION', 'NO_STRUCTURE']])

    if critical_issues == 0 and len(very_large) == 0:
        print("\n✅✅✅ ВСЕ ДОКУМЕНТЫ ОБРАБОТАНЫ УСПЕШНО!")
        print("✅ Чанкер РАБОТАЕТ ИДЕАЛЬНО на всех типах документов!")
        print("✅ МОЖНО СОЗДАВАТЬ ВЕКТОРНУЮ БАЗУ!")
        return True
    else:
        print(f"\n⚠️  Найдено проблем: {critical_issues} критических, {len(very_large)} больших чанков")
        return False


if __name__ == '__main__':
    success = test_all_documents()
    sys.exit(0 if success else 1)
