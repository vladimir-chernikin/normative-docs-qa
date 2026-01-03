#!/usr/bin/env python3
"""
Интегратор для векторизации документов
Обрабатывает все 5 моделей с возможностью выбора базы данных
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Автоматический переход в корневую директорию проекта vector-db-test
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

# Выполняем переход в нужную директорию перед импортом модулей проекта
ensure_correct_directory()

# Добавляем путь к корневой директории проекта
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.document_processor import DocumentProcessor, DocumentChunk
from scripts.embedding_model_loader import EmbeddingModelLoader, GPUMonitor
from scripts.langchain_embeddings_wrapper import LangChainSentenceTransformersEmbeddings
from langchain_community.vectorstores import FAISS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vectorization_integrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VectorizeIntegrator:
    """Класс для интеграции векторизации документов для всех моделей"""
    
    def __init__(self, config_path: str = "config/config.json", database: str = "current"):
        """
        Инициализация интегратора
        
        Args:
            config_path: Путь к файлу конфигурации
            database: Имя базы данных для индексации ('current' или 'new')
        """
        self.config_path = config_path
        self.database = database
        self.config = self._load_config()
        self.document_processor = DocumentProcessor()
        self.embedding_loader = EmbeddingModelLoader()
        self.gpu_monitor = GPUMonitor()
        
        # Все рабочие модели (5 моделей)
        self.working_models = [
            "rubert-tiny2",
            "multilingual-e5-small", 
            "paraphrase-multilingual-MiniLM-L12-v2",
            "labse",
            "frida"
        ]
        
        # Настраиваем пути для выбранной базы данных
        self._setup_database_paths()
        
    def _load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию из файла"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {config_file}")
            
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _setup_database_paths(self):
        """Настраивает пути для выбранной базы данных"""
        # Проверяем, есть ли секция databases в конфигурации
        if "databases" in self.config and self.database in self.config["databases"]:
            # Используем пути из секции databases
            db_config = self.config["databases"][self.database]
            self.source_dir = db_config["source_documents"]
            self.vector_db_dir = db_config["vector_databases"]
            self.db_name = db_config["name"]
            logger.info(f"Настроены пути для базы данных '{self.db_name}':")
        else:
            # Используем старый подход с суффиксами
            # Базовые пути из конфигурации
            base_source_dir = self.config["data_paths"]["source_documents"]
            base_vector_dir = self.config["data_paths"]["vector_databases"]
            
            # Если выбрана новая база данных, добавляем суффикс к путям
            if self.database == "new":
                self.source_dir = self.config["data_paths"].get("source_documents_new", f"{base_source_dir}_new")
                self.vector_db_dir = self.config["data_paths"].get("vector_databases_new", f"{base_vector_dir}_new")
                self.db_name = "Новая база"
                logger.info(f"Настроены пути для новой базы данных:")
            else:
                self.source_dir = base_source_dir
                self.vector_db_dir = base_vector_dir
                self.db_name = "Текущая база"
                logger.info(f"Настроены пути для текущей базы данных:")
            
        logger.info(f"  → Исходные документы: {self.source_dir}")
        logger.info(f"  → Векторные базы: {self.vector_db_dir}")
        
        # Создаем директорию для векторных баз, если она не существует
        Path(self.vector_db_dir).mkdir(exist_ok=True, parents=True)
    
    def _get_model_config(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Получает конфигурацию модели по имени"""
        for model in self.config["models"]:
            if model["name"] == model_name:
                return model
        return None
    
    def load_and_process_documents(self) -> List[DocumentChunk]:
        """Загружает и обрабатывает все документы"""
        logger.info("Начинаю загрузку и обработку документов...")
        
        source_dir = Path(self.source_dir)
        if not source_dir.exists():
            raise FileNotFoundError(f"Директория с документами не найдена: {source_dir}")
        
        all_chunks = []
        markdown_files = list(source_dir.glob("*.md"))
        
        logger.info(f"Найдено {len(markdown_files)} файлов Markdown для обработки")
        
        for file_path in markdown_files:
            logger.info(f"Обрабатываю файл: {file_path.name}")
            try:
                chunks = self.document_processor.process_document(str(file_path))
                all_chunks.extend(chunks)
                logger.info(f"  → Создано {len(chunks)} чанков")
            except Exception as e:
                logger.error(f"Ошибка при обработке {file_path.name}: {e}")
                continue
        
        logger.info(f"Всего обработано {len(all_chunks)} чанков из {len(markdown_files)} документов")
        return all_chunks
    
    def prepare_texts_and_metadata(self, chunks: List[DocumentChunk]) -> tuple:
        """Подготавливает тексты и метаданные для векторизации"""
        texts = []
        metadatas = []
        
        for chunk in chunks:
            texts.append(chunk.content)
            
            # Создаем полные метаданные для FAISS
            metadata = {
                "source_file": chunk.source_file,
                "document_path": chunk.document_path,
                "hierarchy_path": chunk.hierarchy_path,
                "header_1": chunk.header_1,
                "header_2": chunk.header_2, 
                "header_3": chunk.header_3,
                "header_4": chunk.header_4,
                "chunk_number": chunk.chunk_number,
                "total_chunks_in_section": chunk.total_chunks_in_section,
                "text_length": chunk.text_length,
                "split_method": chunk.split_method,
                "chunk_id": chunk.chunk_id
            }
            metadatas.append(metadata)
        
        return texts, metadatas
    
    def create_faiss_index(self, model_name: str, texts: List[str], metadatas: List[Dict]) -> bool:
        """
        Создает FAISS индекс для указанной модели
        
        Args:
            model_name: Имя модели
            texts: Список текстов для векторизации
            metadatas: Список метаданных
            
        Returns:
            bool: True если индекс создан успешно
        """
        model_config = self._get_model_config(model_name)
        if not model_config:
            logger.error(f"Конфигурация модели {model_name} не найдена")
            return False
        
        logger.info(f"Создаю FAISS индекс для модели: {model_name}")
        logger.info(f"  → Модель: {model_config['model_path']}")
        logger.info(f"  → Размерность: {model_config['embedding_size']}")
        logger.info(f"  → Ожидаемое использование VRAM: {model_config['estimated_vram_mb']} MB")
        
        try:
            # Запускаем мониторинг GPU
            self.gpu_monitor.start_monitoring()
            
            # Загружаем модель
            start_time = time.time()
            
            # Для FRIDA используем специальную обработку
            if model_name == "frida":
                return self._create_frida_index(model_config, texts, metadatas)
            
            # Для остальных моделей используем стандартный подход
            model = self.embedding_loader.load_model(model_config)
            if model is None:
                logger.error(f"Не удалось загрузить модель {model_name}")
                return False
            
            # Создаем обертку для LangChain совместимости
            embeddings_model = LangChainSentenceTransformersEmbeddings(model)
            
            load_time = time.time() - start_time
            logger.info(f"  → Модель загружена за {load_time:.1f} секунд")
            
            # Создаем FAISS векторную базу
            vectorization_start = time.time()
            
            # Батчевая обработка для больших объемов данных
            batch_size = 50  # Обрабатываем по 50 текстов за раз
            logger.info(f"  → Начинаю векторизацию {len(texts)} текстов (батчи по {batch_size})")
            
            vector_store = None
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                batch_metadatas = metadatas[i:i+batch_size]
                
                logger.info(f"    Обрабатываю батч {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1} "
                          f"({len(batch_texts)} текстов)")
                
                try:
                    if vector_store is None:
                        # Создаем новую векторную базу
                        vector_store = FAISS.from_texts(
                            texts=batch_texts,
                            embedding=embeddings_model,
                            metadatas=batch_metadatas
                        )
                    else:
                        # Добавляем к существующей базе
                        additional_store = FAISS.from_texts(
                            texts=batch_texts,
                            embedding=embeddings_model,
                            metadatas=batch_metadatas
                        )
                        vector_store.merge_from(additional_store)
                except Exception as e:
                    import traceback
                    logger.error(f"Ошибка при создании FAISS индекса: {e}")
                    logger.error(f"Стек вызовов: {traceback.format_exc()}")
                    raise
            
            vectorization_time = time.time() - vectorization_start
            logger.info(f"  → Векторизация завершена за {vectorization_time:.1f} секунд")
            
            # Сохраняем FAISS индекс
            vector_db_dir = Path(self.vector_db_dir)
            vector_db_dir.mkdir(exist_ok=True)
            
            save_path = vector_db_dir / f"{model_name}-faiss"
            save_start = time.time()
            
            vector_store.save_local(str(save_path))
            
            save_time = time.time() - save_start
            total_time = time.time() - start_time
            
            logger.info(f"  → FAISS индекс сохранен в: {save_path}")
            logger.info(f"  → Время сохранения: {save_time:.1f} секунд")
            logger.info(f"  → Общее время: {total_time:.1f} секунд")
            
            # Остановить мониторинг GPU
            self.gpu_monitor.stop_monitoring()
            
            # Статистика
            logger.info(f"  → Статистика:")
            logger.info(f"    - Всего векторов: {vector_store.index.ntotal}")
            logger.info(f"    - Размерность: {vector_store.index.d}")
            logger.info(f"    - Среднее время на текст: {vectorization_time/len(texts):.3f} сек")
            
            return True
            
        except Exception as e:
            import traceback
            logger.error(f"Ошибка при создании FAISS индекса для {model_name}: {e}")
            logger.error(f"Стек вызовов: {traceback.format_exc()}")
            self.gpu_monitor.stop_monitoring()
            return False
    
    def _create_frida_index(self, model_config: Dict[str, Any], texts: List[str], metadatas: List[Dict]) -> bool:
        """
        Создает FAISS индекс для модели FRIDA
        
        Args:
            model_config: Конфигурация модели
            texts: Список текстов для векторизации
            metadatas: Список метаданных
            
        Returns:
            bool: True если индекс создан успешно
        """
        try:
            from transformers import AutoModel, AutoTokenizer
            import torch
            import numpy as np
            from tqdm import tqdm
            
            logger.info("Загрузка модели FRIDA...")
            
            # Определяем устройство
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Используемое устройство: {device}")
            
            # Загружаем модель и токенизатор
            start_time = time.time()
            
            try:
                if device == "cuda":
                    # Пробуем загрузить с accelerate
                    try:
                        logger.info("Загрузка модели с device_map='auto'")
                        model = AutoModel.from_pretrained(model_config["model_path"], device_map='auto')
                    except Exception as e:
                        logger.warning(f"Ошибка загрузки с device_map: {e}")
                        logger.info("Пробуем загрузить без device_map")
                        model = AutoModel.from_pretrained(model_config["model_path"]).to(device)
                else:
                    model = AutoModel.from_pretrained(model_config["model_path"])
                    
                tokenizer = AutoTokenizer.from_pretrained(model_config["model_path"])
                logger.info("Модель FRIDA успешно загружена")
            except Exception as e:
                logger.error(f"Ошибка загрузки модели FRIDA: {e}")
                raise
            
            load_time = time.time() - start_time
            logger.info(f"  → Модель загружена за {load_time:.1f} секунд")
            
            # Создаем функцию для получения эмбеддингов
            def get_embeddings(batch_texts):
                # Токенизируем тексты
                inputs = tokenizer(batch_texts, return_tensors='pt', 
                                  truncation=True, padding=True, max_length=512)
                
                # Переносим на GPU, если доступен
                if device == "cuda":
                    inputs = {k: v.to(device) for k, v in inputs.items()}
                
                # Получаем эмбеддинги
                with torch.no_grad():
                    # Для моделей T5 нужно указать decoder_input_ids
                    decoder_input_ids = torch.zeros((len(batch_texts), 1), dtype=torch.long)
                    if device == "cuda":
                        decoder_input_ids = decoder_input_ids.to(device)
                    
                    # Передаем как encoder_inputs, так и decoder_input_ids
                    outputs = model(**inputs, decoder_input_ids=decoder_input_ids)
                    
                    # Используем последний скрытый слой энкодера для эмбеддингов
                    embeddings = outputs.encoder_last_hidden_state.mean(dim=1).cpu().numpy()
                    
                return embeddings
            
            # Создаем класс-обертку для совместимости с LangChain
            class FridaEmbeddingsWrapper:
                def embed_documents(self, texts):
                    all_embeddings = []
                    batch_size = 8
                    
                    for i in range(0, len(texts), batch_size):
                        batch_texts = texts[i:i+batch_size]
                        embeddings = get_embeddings(batch_texts)
                        
                        for embedding in embeddings:
                            all_embeddings.append(embedding.tolist())
                    
                    return all_embeddings
                
                def embed_query(self, text):
                    return get_embeddings([text])[0].tolist()
            
            # Создаем экземпляр обертки
            embeddings_model = FridaEmbeddingsWrapper()
            
            # Создаем FAISS векторную базу
            vectorization_start = time.time()
            
            # Батчевая обработка для больших объемов данных
            batch_size = 50  # Обрабатываем по 50 текстов за раз
            logger.info(f"  → Начинаю векторизацию {len(texts)} текстов (батчи по {batch_size})")
            
            vector_store = None
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                batch_metadatas = metadatas[i:i+batch_size]
                
                logger.info(f"    Обрабатываю батч {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1} "
                          f"({len(batch_texts)} текстов)")
                
                if vector_store is None:
                    # Создаем новую векторную базу
                    vector_store = FAISS.from_texts(
                        texts=batch_texts,
                        embedding=embeddings_model,
                        metadatas=batch_metadatas
                    )
                else:
                    # Добавляем к существующей базе
                    additional_store = FAISS.from_texts(
                        texts=batch_texts,
                        embedding=embeddings_model,
                        metadatas=batch_metadatas
                    )
                    vector_store.merge_from(additional_store)
            
            vectorization_time = time.time() - vectorization_start
            logger.info(f"  → Векторизация завершена за {vectorization_time:.1f} секунд")
            
            # Сохраняем FAISS индекс
            vector_db_dir = Path(self.vector_db_dir)
            vector_db_dir.mkdir(exist_ok=True)
            
            save_path = vector_db_dir / "frida-faiss"
            save_start = time.time()
            
            vector_store.save_local(str(save_path))
            
            save_time = time.time() - save_start
            total_time = time.time() - start_time
            
            logger.info(f"  → FAISS индекс сохранен в: {save_path}")
            logger.info(f"  → Время сохранения: {save_time:.1f} секунд")
            logger.info(f"  → Общее время: {total_time:.1f} секунд")
            
            # Статистика
            logger.info(f"  → Статистика:")
            logger.info(f"    - Всего векторов: {vector_store.index.ntotal}")
            logger.info(f"    - Размерность: {vector_store.index.d}")
            logger.info(f"    - Среднее время на текст: {vectorization_time/len(texts):.3f} сек")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при создании FAISS индекса для FRIDA: {e}")
            return False
    
    def vectorize_all_documents(self):
        """Векторизует все документы для всех рабочих моделей"""
        logger.info("=" * 80)
        logger.info(f"НАЧИНАЮ ВЕКТОРИЗАЦИЮ ДОКУМЕНТОВ ДЛЯ БАЗЫ: {self.db_name}")
        logger.info("=" * 80)
        
        # Загружаем и обрабатываем документы
        chunks = self.load_and_process_documents()
        if not chunks:
            logger.error("Не удалось загрузить документы")
            return
        
        texts, metadatas = self.prepare_texts_and_metadata(chunks)
        
        logger.info(f"Подготовлено {len(texts)} текстов для векторизации")
        
        logger.info(f"Будут созданы FAISS индексы для {len(self.working_models)} моделей")
        
        # Результаты векторизации
        results = {}
        total_start_time = time.time()
        
        for model_name in self.working_models:
            logger.info(f"\n{'-' * 60}")
            logger.info(f"ВЕКТОРИЗАЦИЯ МОДЕЛИ: {model_name.upper()}")
            logger.info(f"{'-' * 60}")
            
            success = self.create_faiss_index(model_name, texts, metadatas)
            results[model_name] = success
            
            if success:
                logger.info(f"✅ Модель {model_name} успешно обработана")
            else:
                logger.error(f"❌ Ошибка при обработке модели {model_name}")
        
        total_time = time.time() - total_start_time
        
        # Итоговый отчет
        logger.info("\n" + "=" * 80)
        logger.info(f"ИТОГОВЫЙ ОТЧЕТ ВЕКТОРИЗАЦИИ ДЛЯ БАЗЫ: {self.db_name}")
        logger.info("=" * 80)
        
        successful_models = [model for model, success in results.items() if success]
        failed_models = [model for model, success in results.items() if not success]
        
        logger.info(f"Общее время векторизации: {total_time:.1f} секунд ({total_time/60:.1f} минут)")
        logger.info(f"Обработано документов: {len(set(chunk.source_file for chunk in chunks))}")
        logger.info(f"Создано текстовых чанков: {len(texts)}")
        logger.info(f"Успешно созданных индексов: {len(successful_models)}/{len(self.working_models)}")
        
        if successful_models:
            logger.info("\n✅ УСПЕШНО СОЗДАННЫЕ ИНДЕКСЫ:")
            for model in successful_models:
                config = self._get_model_config(model)
                logger.info(f"  → {model} ({config['embedding_size']} dim)")
        
        if failed_models:
            logger.info("\n❌ НЕУДАЧНЫЕ МОДЕЛИ:")
            for model in failed_models:
                logger.info(f"  → {model}")
        
        # Проверяем созданные директории
        vector_db_dir = Path(self.vector_db_dir)
        created_dirs = [d.name for d in vector_db_dir.iterdir() if d.is_dir()]
        
        logger.info(f"\nСозданные директории FAISS:")
        for dir_name in created_dirs:
            logger.info(f"  → {dir_name}")
        
        logger.info("=" * 80)


def main():
    """Главная функция"""
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description='Интегратор для векторизации документов')
    parser.add_argument('--database', type=str, default='current', choices=['current', 'new', 'zayavki'],
                        help='База данных для индексации (current или new или zayavki)')
    parser.add_argument('--config', type=str, default='config/config.json',
                        help='Путь к файлу конфигурации')
    parser.add_argument('--models', type=str, nargs='+',
                        help='Список моделей для обработки (по умолчанию все)')
    
    args = parser.parse_args()
    
    try:
        # Создаем и запускаем интегратор
        integrator = VectorizeIntegrator(config_path=args.config, database=args.database)
        
        # Если указаны конкретные модели, обрабатываем только их
        if args.models:
            integrator.working_models = [model for model in args.models if model in integrator.working_models]
            logger.info(f"Обработка выбранных моделей: {integrator.working_models}")
        
        integrator.vectorize_all_documents()
        
    except KeyboardInterrupt:
        logger.info("\nВекторизация прервана пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    main() 

# python scripts/vectorize_integrator.py --database zayavki    