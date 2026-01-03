#!/usr/bin/env python3
"""
Отладочный скрипт для проверки работы FAISS с разными типами входных данных
"""

import os
import sys
import numpy as np
import faiss
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

def test_faiss_with_array(array, name):
    """Тестирует совместимость массива с FAISS"""
    print(f"\nТест FAISS с {name}:")
    print(f"  Тип: {type(array)}")
    
    try:
        print(f"  Форма: {array.shape if hasattr(array, 'shape') else 'Нет атрибута shape'}")
        print(f"  Тип элементов: {array.dtype if hasattr(array, 'dtype') else 'Нет атрибута dtype'}")
        print(f"  Непрерывность данных: {array.flags.c_contiguous if hasattr(array, 'flags') else 'Нет атрибута flags'}")
    except Exception as e:
        print(f"  Ошибка при получении атрибутов: {e}")
    
    try:
        # Создаем индекс FAISS
        dimension = array.shape[1] if hasattr(array, 'shape') and len(array.shape) > 1 else len(array[0])
        index = faiss.IndexFlatL2(dimension)
        
        # Пробуем добавить векторы в индекс
        try:
            index.add(array)
            print(f"  ✅ Успешно добавлены векторы в FAISS индекс")
            return True
        except Exception as e:
            print(f"  ❌ Ошибка при добавлении векторов в FAISS индекс: {e}")
            
            # Пробуем преобразовать к numpy массиву
            try:
                array_np = np.array(array, dtype=np.float32)
                print(f"  После преобразования: тип={type(array_np)}, форма={array_np.shape}, dtype={array_np.dtype}")
                index.add(array_np)
                print(f"  ✅ Успешно добавлены векторы после преобразования к np.float32")
                return True
            except Exception as e2:
                print(f"  ❌ Ошибка после преобразования: {e2}")
                return False
    except Exception as e:
        print(f"  ❌ Ошибка при создании индекса: {e}")
        return False

def main():
    """Основная функция для отладки"""
    # Создаем тестовые данные разных типов
    
    # 1. Создаем numpy массив напрямую
    print("Создание тестовых данных...")
    np_array = np.random.rand(10, 128).astype(np.float32)
    
    # 2. Загружаем модель SentenceTransformer
    model_name = "cointegrated/rubert-tiny2"
    print(f"Загрузка модели: {model_name}")
    model = SentenceTransformer(model_name)
    
    # 3. Создаем тестовые тексты
    texts = [
        "Это первый тестовый текст",
        "Это второй тестовый текст с немного другим содержанием"
    ]
    
    # 4. Получаем эмбеддинги с разными параметрами
    st_array1 = model.encode(texts, convert_to_tensor=False)  # numpy array
    st_array2 = model.encode(texts, convert_to_tensor=True).cpu().numpy()  # torch tensor -> numpy
    
    # 5. Создаем список списков
    list_of_lists = [[float(x) for x in row] for row in np_array[:2]]
    
    # 6. Создаем массив из списка списков
    array_from_list = np.array(list_of_lists, dtype=np.float32)
    
    # Тестируем все типы данных с FAISS
    test_faiss_with_array(np_array, "numpy массив")
    test_faiss_with_array(st_array1, "SentenceTransformer embeddings (convert_to_tensor=False)")
    test_faiss_with_array(st_array2, "SentenceTransformer embeddings (convert_to_tensor=True -> numpy)")
    
    # Тестируем список списков
    print("\nТест FAISS со списком списков:")
    print(f"  Тип: {type(list_of_lists)}")
    try:
        # Создаем индекс FAISS
        dimension = len(list_of_lists[0])
        index = faiss.IndexFlatL2(dimension)
        
        # Пробуем добавить векторы в индекс
        try:
            index.add(list_of_lists)
            print(f"  ✅ Успешно добавлены векторы в FAISS индекс")
        except Exception as e:
            print(f"  ❌ Ошибка при добавлении векторов в FAISS индекс: {e}")
            
            # Пробуем преобразовать к numpy массиву
            try:
                list_as_np = np.array(list_of_lists, dtype=np.float32)
                index.add(list_as_np)
                print(f"  ✅ Успешно добавлены векторы после преобразования к np.float32")
            except Exception as e:
                print(f"  ❌ Ошибка после преобразования: {e}")
    except Exception as e:
        print(f"  ❌ Ошибка при создании индекса: {e}")
    
    # Тестируем массив из списка списков
    test_faiss_with_array(array_from_list, "numpy массив из списка списков")
    
    # Тестируем LangChain FAISS
    print("\nТест с LangChain FAISS:")
    try:
        from langchain_community.vectorstores import FAISS as LangChainFAISS
        
        class SimpleEmbeddings:
            def embed_documents(self, texts):
                return [[float(i) for i in range(10)] for _ in range(len(texts))]
                
            def embed_query(self, text):
                return [float(i) for i in range(10)]
        
        embeddings = SimpleEmbeddings()
        texts = ["Test text 1", "Test text 2"]
        
        print("  Создание LangChain FAISS из текстов...")
        try:
            vector_store = LangChainFAISS.from_texts(texts=texts, embedding=embeddings)
            print("  ✅ Успешно создан LangChain FAISS индекс")
            
            # Проверяем тип эмбеддингов, которые возвращает наша обертка
            print("\n  Проверка типов данных в LangChain FAISS:")
            test_embeddings = embeddings.embed_documents(texts)
            print(f"  Тип эмбеддингов: {type(test_embeddings)}")
            print(f"  Тип первого эмбеддинга: {type(test_embeddings[0])}")
            
        except Exception as e:
            print(f"  ❌ Ошибка при создании LangChain FAISS: {e}")
    except ImportError:
        print("  LangChain FAISS не установлен")

if __name__ == "__main__":
    main() 