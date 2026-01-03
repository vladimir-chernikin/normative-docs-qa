#!/usr/bin/env python3
"""
Минимальный пример для проверки работы FAISS напрямую, без LangChain
"""

import os
import sys
import numpy as np
import faiss
from pathlib import Path

# Добавляем путь к корневой директории проекта
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def main():
    """Основная функция для отладки"""
    print("FAISS Minimal Test")
    print(f"FAISS version: {faiss.__version__}")
    print(f"FAISS available methods: {dir(faiss)}")
    
    # Создаем тестовые данные
    print("\nСоздание тестовых данных...")
    
    # Создаем numpy массив с float32
    dimension = 128
    num_vectors = 10
    np_array = np.random.rand(num_vectors, dimension).astype(np.float32)
    print(f"Numpy array: shape={np_array.shape}, dtype={np_array.dtype}")
    
    # Проверяем, что массив непрерывный (C-contiguous)
    print(f"C-contiguous: {np_array.flags.c_contiguous}")
    
    # Создаем индекс FAISS
    print("\nСоздание индекса FAISS...")
    try:
        # Используем более низкоуровневый интерфейс
        index = faiss.IndexFlatL2(dimension)
        print(f"Размерность индекса: {index.d}")
        print(f"Это обучаемый индекс: {index.is_trained}")
        
        # Добавляем векторы в индекс
        print("\nДобавление векторов в индекс...")
        
        # Проверяем, что массив правильного типа и формы
        print(f"Тип массива: {type(np_array)}")
        print(f"Форма массива: {np_array.shape}")
        print(f"Тип элементов: {np_array.dtype}")
        
        # Пробуем использовать низкоуровневый интерфейс
        try:
            print("\nПробуем использовать IndexFlatL2_add:")
            faiss.IndexFlatL2_add(index, np_array)
            print(f"✅ Успешно добавлены векторы в индекс через IndexFlatL2_add")
            print(f"Количество векторов в индексе: {index.ntotal}")
        except Exception as e1:
            print(f"❌ Ошибка при использовании IndexFlatL2_add: {e1}")
            
            try:
                print("\nПробуем использовать add_with_ids:")
                ids = np.arange(num_vectors, dtype=np.int64)
                index.add_with_ids(np_array, ids)
                print(f"✅ Успешно добавлены векторы в индекс через add_with_ids")
                print(f"Количество векторов в индексе: {index.ntotal}")
            except Exception as e2:
                print(f"❌ Ошибка при использовании add_with_ids: {e2}")
                
                try:
                    print("\nПробуем использовать альтернативный индекс IndexIDMap:")
                    index2 = faiss.IndexIDMap(faiss.IndexFlatL2(dimension))
                    index2.add_with_ids(np_array, ids)
                    print(f"✅ Успешно добавлены векторы в индекс IndexIDMap")
                    print(f"Количество векторов в индексе: {index2.ntotal}")
                except Exception as e3:
                    print(f"❌ Ошибка при использовании IndexIDMap: {e3}")
        
        # Выполняем поиск
        print("\nВыполнение поиска...")
        k = 3  # Ищем 3 ближайших соседа
        query = np.random.rand(1, dimension).astype(np.float32)
        
        try:
            distances, indices = index.search(query, k)
            print(f"Результаты поиска:")
            print(f"  Расстояния: {distances}")
            print(f"  Индексы: {indices}")
        except Exception as e:
            print(f"❌ Ошибка при поиске: {e}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 