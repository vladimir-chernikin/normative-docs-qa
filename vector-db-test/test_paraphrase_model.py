#!/usr/bin/env python3
"""
Быстрый тест модели paraphrase-multilingual-MiniLM-L12-v2
"""

from sentence_transformers import SentenceTransformer
import numpy as np

print("=" * 80)
print("ТЕСТИРОВАНИЕ paraphrase-multilingual-MiniLM-L12-v2")
print("=" * 80)
print()

# Загрузка модели
print("⏳ Загрузка модели...")
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
print(f"✅ Модель загружена")
print(f"   Размерность: {model.get_sentence_embedding_dimension()}")
print()

# Тест 1: Кодирование предложений
print("ТЕСТ 1: Кодирование предложений")
print("-" * 80)

sentences = [
    "Как отключить отопление в квартире?",
    "Процедура отключения системы теплоснабжения",
    "Кто платит за капитальный ремонт?",
    "Распределение расходов на ремонтные работы"
]

print(f"Кодирую {len(sentences)} предложений...")
embeddings = model.encode(sentences)
print(f"✅ Получено эмбеддингов: {embeddings.shape}")
print()

# Тест 2: Сравнение перефразов
print("ТЕСТ 2: Сравнение перефразов (косинусное сходство)")
print("-" * 80)

test_pairs = [
    ("Как отключить отопление?", "Процедура отключения системы теплоснабжения"),
    ("Кто платит за ремонт?", "Распределение расходов на ремонтные работы"),
    ("Выбор управляющей компании", "Конкурс на управление многоквартирным домом"),
    ("Отопление", "Холодильник"),  # Непохожие
]

for q1, q2 in test_pairs:
    v1 = model.encode(q1)
    v2 = model.encode(q2)
    
    # Косинусное сходство
    similarity = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    
    marker = "✅" if similarity > 0.7 else "❌" if similarity < 0.3 else "⚠️"
    print(f"{marker} Сходство: {similarity:.4f} | '{q1}' ↔ '{q2}'")

print()
print("=" * 80)
print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
print("=" * 80)
