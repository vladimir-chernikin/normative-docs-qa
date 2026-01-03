#!/usr/bin/env python3
"""
Отладочный скрипт для проверки типа данных, возвращаемого методом encode модели SentenceTransformer
"""

import os
import sys
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Добавляем путь к корневой директории проекта
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Настраиваем корректную директорию
def ensure_correct_directory():
    """Проверяет и устанавливает корректную рабочую директорию для скрипта"""
    current_dir = os.getcwd()
    target_dir = "/home/sawa/GitHub/stazh_aspect/vector-db-test"
    
    # Проверяем, находимся ли мы уже в нужной директории
    if current_dir != target_dir:
        print(f"Текущая директория: {current_dir}")
        print(f"Переход в директорию проекта: {target_dir}")
        os.chdir(target_dir)
        print(f"Новая текущая директория: {os.getcwd()}")
    
    # Проверка активированного conda окружения
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env not in ['stzh311', 'stzh311cpu']:
        print("\n" + "="*80)
        print("ПРЕДУПРЕЖДЕНИЕ: Не активировано нужное окружение conda!")
        print("Для GPU: conda activate stzh311")
        print("Для CPU: conda activate stzh311cpu")
        print("="*80 + "\n")

# Вызываем функцию для проверки директории
ensure_correct_directory()

def main():
    """Основная функция для отладки"""
    # Загружаем модель
    model_name = "cointegrated/rubert-tiny2"
    print(f"Загрузка модели: {model_name}")
    
    model = SentenceTransformer(model_name)
    
    # Создаем тестовые тексты
    texts = [
        "Это первый тестовый текст",
        "Это второй тестовый текст с немного другим содержанием"
    ]
    
    print(f"Тексты для векторизации: {texts}")
    
    # Получаем эмбеддинги с разными параметрами
    print("\nТест 1: convert_to_tensor=False (по умолчанию)")
    embeddings1 = model.encode(texts, convert_to_tensor=False)
    print(f"Тип данных: {type(embeddings1)}")
    print(f"Форма: {embeddings1.shape if hasattr(embeddings1, 'shape') else 'Нет атрибута shape'}")
    print(f"Тип элементов: {embeddings1.dtype if hasattr(embeddings1, 'dtype') else 'Нет атрибута dtype'}")
    
    print("\nТест 2: convert_to_tensor=True")
    embeddings2 = model.encode(texts, convert_to_tensor=True)
    print(f"Тип данных: {type(embeddings2)}")
    print(f"Тип после .cpu().numpy(): {type(embeddings2.cpu().numpy())}")
    print(f"Форма после .cpu().numpy(): {embeddings2.cpu().numpy().shape}")
    
    print("\nТест 3: convert_to_numpy=True")
    embeddings3 = model.encode(texts, convert_to_numpy=True)
    print(f"Тип данных: {type(embeddings3)}")
    print(f"Форма: {embeddings3.shape if hasattr(embeddings3, 'shape') else 'Нет атрибута shape'}")
    
    # Проверка совместимости с FAISS
    print("\nПроверка совместимости с FAISS")
    try:
        import faiss
        print("FAISS успешно импортирован")
        
        # Создаем индекс FAISS
        dimension = embeddings1.shape[1]
        index = faiss.IndexFlatL2(dimension)
        
        # Пробуем добавить векторы в индекс
        try:
            index.add(embeddings1)
            print("✅ Успешно добавлены векторы в FAISS индекс (embeddings1)")
        except Exception as e:
            print(f"❌ Ошибка при добавлении векторов в FAISS индекс (embeddings1): {e}")
            
            # Пробуем преобразовать к нужному типу
            try:
                embeddings1_np = np.array(embeddings1, dtype=np.float32)
                index.add(embeddings1_np)
                print(f"✅ Успешно добавлены векторы после преобразования к np.float32")
            except Exception as e:
                print(f"❌ Ошибка после преобразования: {e}")
        
    except ImportError:
        print("FAISS не установлен")

if __name__ == "__main__":
    main() 