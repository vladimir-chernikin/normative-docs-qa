#!/usr/bin/env python3
"""
Проверка качества чанков (БЕЗ гистограмм)
Анализирует размеры чанков и сообщает о проблемах
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter


def load_chunks(json_file: Path) -> List[Dict[str, Any]]:
    """Загружает чанки из JSON файла"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_chunk_quality(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Проверяет качество чанков и возвращает отчет"""

    if not chunks:
        return {
            'status': 'ERROR',
            'message': 'Нет чанков для анализа',
            'total_chunks': 0
        }

    # Анализируем размеры
    sizes = [len(chunk.get('text', '')) for chunk in chunks]

    # Основные метрики
    total = len(chunks)
    min_size = min(sizes)
    max_size = max(sizes)
    avg_size = sum(sizes) / len(sizes)
    median_size = sorted(sizes)[len(sizes) // 2]

    # Категории размеров
    tiny_chunks = sum(1 for s in sizes if s < 50)
    small_chunks = sum(1 for s in sizes if 50 <= s < 200)
    optimal_chunks = sum(1 for s in sizes if 200 <= s < 1000)
    large_chunks = sum(1 for s in sizes if 1000 <= s < 2000)
    huge_chunks = sum(1 for s in sizes if s >= 2000)

    # Проблемы
    problems = []

    if tiny_chunks > 0:
        problems.append(f"❌ Слишком мелкие чанки (< 50 символов): {tiny_chunks} шт. ({tiny_chunks/total*100:.1f}%)")

    if huge_chunks > 0:
        problems.append(f"❌ Слишком крупные чанки (> 2000 символов): {huge_chunks} шт. ({huge_chunks/total*100:.1f}%)")

    if min_size < 20:
        problems.append(f"⚠️ Минимальный размер слишком мал: {min_size} символов")

    if max_size > 3000:
        problems.append(f"⚠️ Максимальный размер слишком велик: {max_size} символов")

    if avg_size < 200:
        problems.append(f"⚠️ Средний размер слишком мал: {avg_size:.0f} символов (рекомендуется 300-800)")

    if avg_size > 1500:
        problems.append(f"⚠️ Средний размер слишком велик: {avg_size:.0f} символов (рекомендуется 300-800)")

    # Общая оценка
    if tiny_chunks == 0 and huge_chunks == 0 and 200 <= avg_size <= 1000:
        status = "✅ ОТЛИЧНО"
        status_emoji = "✅"
    elif tiny_chunks < total * 0.05 and huge_chunks < total * 0.05:
        status = "✓ ХОРОШО"
        status_emoji = "✓"
    elif tiny_chunks < total * 0.15 and huge_chunks < total * 0.15:
        status = "⚠ ДОСТАТОЧНО"
        status_emoji = "⚠"
    else:
        status = "❌ ПЛОХО"
        status_emoji = "❌"

    return {
        'status': status,
        'status_emoji': status_emoji,
        'total_chunks': total,
        'min_size': min_size,
        'max_size': max_size,
        'avg_size': round(avg_size, 1),
        'median_size': median_size,
        'distribution': {
            'tiny': tiny_chunks,      # < 50
            'small': small_chunks,    # 50-200
            'optimal': optimal_chunks, # 200-1000
            'large': large_chunks,    # 1000-2000
            'huge': huge_chunks      # > 2000
        },
        'problems': problems,
        'recommendations': generate_recommendations(tiny_chunks, huge_chunks, avg_size)
    }


def generate_recommendations(tiny: int, huge: int, avg: float) -> List[str]:
    """Генерирует рекомендации на основе проблем"""

    recommendations = []

    if tiny > 0:
        recommendations.append("• Увеличьте минимальный размер чанка в чанкере")
        recommendations.append("• Объединяйте мелкие чанки с соседними")

    if huge > 0:
        recommendations.append("• Уменьшите максимальный размер чанка")
        recommendations.append("• Разбивайте крупные чанки по подпунктам")

    if avg < 200:
        recommendations.append("• Средний размер слишком мал, возможна потеря контекста")

    if avg > 1500:
        recommendations.append("• Средний размер слишком велик, возможны проблемы с LLM")

    if not recommendations:
        recommendations.append("• Качество чанков отличное, рекомендаций нет")

    return recommendations


def print_report(quality_report: Dict[str, Any], document_name: str = "Документ"):
    """Печатает красивый отчет о качестве"""

    print("=" * 80)
    print(f"ОТЧЕТ О КАЧЕСТВЕ ЧАНКОВ: {document_name}")
    print("=" * 80)
    print()

    # Общий статус
    print(f"Статус: {quality_report['status']}")
    print()

    # Основные метрики
    print(f"Всего чанков: {quality_report['total_chunks']}")
    print(f"Мин. размер: {quality_report['min_size']} символов")
    print(f"Макс. размер: {quality_report['max_size']} символов")
    print(f"Средний: {quality_report['avg_size']} символов")
    print(f"Медиана: {quality_report['median_size']} символов")
    print()

    # Распределение
    dist = quality_report['distribution']
    total = quality_report['total_chunks']

    print("Распределение по размерам:")
    print(f"  Мелкие (< 50):      {dist['tiny']:4d} ({dist['tiny']/total*100:5.1f}%)")
    print(f"  Малые (50-200):    {dist['small']:4d} ({dist['small']/total*100:5.1f}%)")
    print(f"  Оптимальные (200-1000): {dist['optimal']:4d} ({dist['optimal']/total*100:5.1f}%)")
    print(f"  Крупные (1000-2000): {dist['large']:4d} ({dist['large']/total*100:5.1f}%)")
    print(f"  Огромные (> 2000): {dist['huge']:4d} ({dist['huge']/total*100:5.1f}%)")
    print()

    # Проблемы
    if quality_report['problems']:
        print("ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ:")
        for problem in quality_report['problems']:
            print(f"  {problem}")
        print()

    # Рекомендации
    if quality_report['recommendations']:
        print("РЕКОМЕНДАЦИИ:")
        for rec in quality_report['recommendations']:
            print(f"  {rec}")
        print()

    print("=" * 80)


def check_document_chunks(chunks: List[Dict[str, Any]], document_name: str) -> bool:
    """
    Проверяет качество чанков и возвращает True если качество хорошее
    """
    quality = check_chunk_quality(chunks)
    print_report(quality, document_name)

    # Возвращаем True если качество хорошее или отличное
    return quality['status_emoji'] in ['✅', '✓']


def main():
    """Точка входа для командной строки"""

    if len(sys.argv) < 2:
        print("Использование: python check_chunk_quality.py <chunks.json> [имя_документа]")
        print()
        print("Примеры:")
        print("  python check_chunk_quality.py chunks.json")
        print("  python check_chunk_quality.py chunks.json 'Жилищный кодекс'")
        sys.exit(1)

    json_file = Path(sys.argv[1])

    if not json_file.exists():
        print(f"❌ Файл не найден: {json_file}")
        sys.exit(1)

    # Имя документа
    doc_name = sys.argv[2] if len(sys.argv) > 2 else json_file.stem

    # Загружаем чанки
    chunks = load_chunks(json_file)

    # Проверяем качество
    quality_ok = check_document_chunks(chunks, doc_name)

    # Код выхода
    sys.exit(0 if quality_ok else 1)


if __name__ == "__main__":
    main()
