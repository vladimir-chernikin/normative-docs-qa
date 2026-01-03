#!/usr/bin/env python3
"""
Скрипт векторизации документов с GPU мониторингом
Создает FAISS индексы для всех рабочих embedding моделей
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

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
        logging.FileHandler('vectorization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DocumentVectorizer:
    """Класс для векторизации документов и создания FAISS индексов"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        Инициализация векторизатора
        
        Args:
            config_path: Путь к файлу конфигурации
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.document_processor = DocumentProcessor()
        self.embedding_loader = EmbeddingModelLoader()
        self.gpu_monitor = GPUMonitor()
        
        # Рабочие модели (согласно плану, 4 модели прошли тестирование)
        self.working_models = [
            "rubert-tiny2",
            "multilingual-e5-small", 
            "paraphrase-multilingual-MiniLM-L12-v2",
            "labse",
            "frida"  # Добавляем модель FRIDA
        ]
        
    def _load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию из файла"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {config_file}")
            
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_model_config(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Получает конфигурацию модели по имени"""
        for model in self.config["models"]:
            if model["name"] == model_name:
                return model
        return None
    
    def load_and_process_documents(self) -> List[DocumentChunk]:
        """Загружает и обрабатывает все документы"""
        logger.info("Начинаю загрузку и обработку документов...")
        
        source_dir = Path(self.config["data_paths"]["source_documents"])
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
            vector_db_dir = Path(self.config["data_paths"]["vector_databases"])
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
            logger.error(f"Ошибка при создании FAISS индекса для {model_name}: {e}")
            self.gpu_monitor.stop_monitoring()
            return False
    
    def vectorize_all_documents(self):
        """Векторизует все документы для всех рабочих моделей"""
        logger.info("=" * 80)
        logger.info("НАЧИНАЮ ВЕКТОРИЗАЦИЮ ДОКУМЕНТОВ")
        logger.info("=" * 80)
        
        # Загружаем и обрабатываем документы
        chunks = self.load_and_process_documents()
        if not chunks:
            logger.error("Не удалось загрузить документы")
            return
        
        texts, metadatas = self.prepare_texts_and_metadata(chunks)
        
        logger.info(f"Подготовлено {len(texts)} текстов для векторизации")
        
        # Отфильтруем модель FRIDA из списка рабочих моделей
        models_to_process = [model for model in self.working_models if model != "frida"]
        
        # Выведем сообщение о необходимости использования специального скрипта для FRIDA
        if "frida" in self.working_models:
            logger.warning(f"\n{'!' * 60}")
            logger.warning(f"ВНИМАНИЕ: Модель FRIDA требует специального скрипта для индексации")
            logger.warning(f"Для индексации FRIDA используйте: python scripts/vectorize_frida.py")
            logger.warning(f"Эта модель будет пропущена в текущем процессе индексации")
            logger.warning(f"{'!' * 60}\n")
        
        logger.info(f"Будут созданы FAISS индексы для {len(models_to_process)} моделей")
        
        # Результаты векторизации
        results = {}
        total_start_time = time.time()
        
        for model_name in models_to_process:
            logger.info(f"\n{'-' * 60}")
            logger.info(f"ВЕКТОРИЗАЦИЯ МОДЕЛИ: {model_name.upper()}")
            logger.info(f"{'-' * 60}")
            
            success = self.create_faiss_index(model_name, texts, metadatas)
            results[model_name] = success
            
            if success:
                logger.info(f"✅ Модель {model_name} успешно обработана")
            else:
                logger.error(f"❌ Ошибка при обработке модели {model_name}")
        
        # Добавляем FRIDA в список неудачных моделей с причиной
        if "frida" in self.working_models:
            results["frida"] = False
        
        total_time = time.time() - total_start_time
        
        # Итоговый отчет
        logger.info("\n" + "=" * 80)
        logger.info("ИТОГОВЫЙ ОТЧЕТ ВЕКТОРИЗАЦИИ")
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
                if model == "frida":
                    logger.info(f"  → {model} (требуется специальный скрипт: python scripts/vectorize_frida.py)")
                else:
                    logger.info(f"  → {model}")
        
        # Проверяем созданные директории
        vector_db_dir = Path(self.config["data_paths"]["vector_databases"])
        created_dirs = [d.name for d in vector_db_dir.iterdir() if d.is_dir()]
        
        logger.info(f"\nСозданные директории FAISS:")
        for dir_name in created_dirs:
            logger.info(f"  → {dir_name}")
        
        logger.info("=" * 80)


def main():
    """Главная функция"""
    try:
        vectorizer = DocumentVectorizer()
        vectorizer.vectorize_all_documents()
        
    except KeyboardInterrupt:
        logger.info("\nВекторизация прервана пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    main() 