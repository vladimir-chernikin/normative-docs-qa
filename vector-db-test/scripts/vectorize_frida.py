#!/usr/bin/env python3
"""
Специализированный скрипт для векторизации документов с использованием модели FRIDA
"""

import os
import sys
import json
import time
import logging
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm

# Добавляем путь к корневой директории проекта
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Импортируем необходимые компоненты
from scripts.document_processor import DocumentProcessor, DocumentChunk
from langchain_community.vectorstores import FAISS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('frida_vectorization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Класс для мониторинга GPU
class GPUMonitor:
    """Класс для мониторинга GPU памяти в реальном времени"""
    
    def __init__(self):
        self.monitoring = False
        self.device_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
        self.gpu_available = self.device_count > 0
        
    def start_monitoring(self):
        """Запускает мониторинг GPU"""
        if not self.gpu_available:
            logger.warning("GPU недоступен для мониторинга")
            return
            
        logger.info("GPU мониторинг запущен")
        self.print_gpu_info()
        
    def print_gpu_info(self):
        """Выводит информацию о GPU"""
        if not self.gpu_available:
            return
            
        for i in range(self.device_count):
            free_mem = torch.cuda.get_device_properties(i).total_memory - torch.cuda.memory_allocated(i)
            free_mem_mb = free_mem / (1024 * 1024)
            total_mem_mb = torch.cuda.get_device_properties(i).total_memory / (1024 * 1024)
            used_mem_mb = total_mem_mb - free_mem_mb
            
            logger.info(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            logger.info(f"  Память: {used_mem_mb:.0f}/{total_mem_mb:.0f} MB ({used_mem_mb/total_mem_mb*100:.1f}%)")
        
    def stop_monitoring(self):
        """Останавливает мониторинг GPU"""
        if self.gpu_available:
            self.print_gpu_info()
        logger.info("GPU мониторинг остановлен")

# Обертка для совместимости с LangChain
class FridaEmbeddingsWrapper:
    """Обертка для модели FRIDA для работы с LangChain"""
    
    def __init__(self, model_path="ai-forever/FRIDA"):
        """
        Инициализация обертки
        
        Args:
            model_path: Путь к модели
        """
        from transformers import AutoModel, AutoTokenizer, EncoderDecoderCache
        
        logger.info(f"Загрузка модели FRIDA из {model_path}")
        
        # Определяем устройство
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Используемое устройство: {self.device}")
        
        # Загружаем модель и токенизатор
        try:
            if self.device == "cuda":
                # Пробуем загрузить с accelerate
                try:
                    logger.info("Загрузка модели с device_map='auto'")
                    self.model = AutoModel.from_pretrained(model_path, device_map='auto')
                except Exception as e:
                    logger.warning(f"Ошибка загрузки с device_map: {e}")
                    logger.info("Пробуем загрузить без device_map")
                    self.model = AutoModel.from_pretrained(model_path).to(self.device)
            else:
                self.model = AutoModel.from_pretrained(model_path)
                
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            # Сохраняем класс EncoderDecoderCache для использования в методах
            self.EncoderDecoderCache = EncoderDecoderCache
            logger.info("Модель FRIDA успешно загружена")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели FRIDA: {e}")
            raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Создает embeddings для списка документов
        
        Args:
            texts: Список текстов для векторизации
            
        Returns:
            Список векторов (embeddings)
        """
        all_embeddings = []
        
        # Обрабатываем тексты батчами для экономии памяти
        batch_size = 8
        for i in tqdm(range(0, len(texts), batch_size), desc="Батчи"):
            batch_texts = texts[i:i+batch_size]
            
            # Токенизируем тексты
            inputs = self.tokenizer(batch_texts, return_tensors='pt', 
                                   truncation=True, padding=True, max_length=512)
            
            # Переносим на GPU, если доступен
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Получаем эмбеддинги
            with torch.no_grad():
                # Для моделей T5 нужно указать decoder_input_ids
                # Используем пустой входной тензор для декодера
                decoder_input_ids = torch.zeros((len(batch_texts), 1), dtype=torch.long)
                if self.device == "cuda":
                    decoder_input_ids = decoder_input_ids.to(self.device)
                
                # Создаем экземпляр EncoderDecoderCache вместо использования устаревшего past_key_values
                # Передаем как encoder_inputs, так и decoder_input_ids
                outputs = self.model(**inputs, decoder_input_ids=decoder_input_ids)
                
                # Используем последний скрытый слой энкодера для эмбеддингов
                # T5 возвращает last_hidden_state в encoder_last_hidden_state
                embeddings = outputs.encoder_last_hidden_state.mean(dim=1).cpu().numpy()
                
                for embedding in embeddings:
                    all_embeddings.append(embedding.tolist())
        
        return all_embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """
        Создает embedding для одного запроса
        
        Args:
            text: Текст запроса
            
        Returns:
            Вектор (embedding) для запроса
        """
        # Токенизируем текст
        inputs = self.tokenizer(text, return_tensors='pt', 
                               truncation=True, padding=True, max_length=512)
        
        # Переносим на GPU, если доступен
        if self.device == "cuda":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Получаем эмбеддинг
        with torch.no_grad():
            # Для моделей T5 нужно указать decoder_input_ids
            decoder_input_ids = torch.zeros((1, 1), dtype=torch.long)
            if self.device == "cuda":
                decoder_input_ids = decoder_input_ids.to(self.device)
            
            # Создаем экземпляр EncoderDecoderCache вместо использования устаревшего past_key_values
            # Передаем как encoder_inputs, так и decoder_input_ids
            outputs = self.model(**inputs, decoder_input_ids=decoder_input_ids)
            
            # Используем последний скрытый слой энкодера для эмбеддингов
            embedding = outputs.encoder_last_hidden_state.mean(dim=1).cpu().numpy()[0]
            
        return embedding.tolist()

def load_config(config_path="config/config.json") -> Dict[str, Any]:
    """Загружает конфигурацию из файла"""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Файл конфигурации не найден: {config_file}")
        
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_and_process_documents(config: Dict[str, Any]) -> List[DocumentChunk]:
    """Загружает и обрабатывает все документы"""
    logger.info("Начинаю загрузку и обработку документов...")
    
    source_dir = Path(config["data_paths"]["source_documents"])
    if not source_dir.exists():
        raise FileNotFoundError(f"Директория с документами не найдена: {source_dir}")
    
    document_processor = DocumentProcessor()
    all_chunks = []
    markdown_files = list(source_dir.glob("*.md"))
    
    logger.info(f"Найдено {len(markdown_files)} файлов Markdown для обработки")
    
    for file_path in markdown_files:
        logger.info(f"Обрабатываю файл: {file_path.name}")
        try:
            chunks = document_processor.process_document(str(file_path))
            all_chunks.extend(chunks)
            logger.info(f"  → Создано {len(chunks)} чанков")
        except Exception as e:
            logger.error(f"Ошибка при обработке {file_path.name}: {e}")
            continue
    
    logger.info(f"Всего обработано {len(all_chunks)} чанков из {len(markdown_files)} документов")
    return all_chunks

def prepare_texts_and_metadata(chunks: List[DocumentChunk]) -> tuple:
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

def create_faiss_index(config: Dict[str, Any], texts: List[str], metadatas: List[Dict]) -> bool:
    """
    Создает FAISS индекс для модели FRIDA
    
    Args:
        config: Конфигурация проекта
        texts: Список текстов для векторизации
        metadatas: Список метаданных
        
    Returns:
        bool: True если индекс создан успешно
    """
    logger.info("=" * 80)
    logger.info("СОЗДАЮ FAISS ИНДЕКС ДЛЯ МОДЕЛИ FRIDA")
    logger.info("=" * 80)
    
    # Параметры модели FRIDA
    model_name = "frida"
    model_path = "ai-forever/FRIDA"
    embedding_size = 1536  # Размерность эмбеддингов FRIDA (равна d_model)
    estimated_vram_mb = 1500
    
    logger.info(f"Создаю FAISS индекс для модели: {model_name}")
    logger.info(f"  → Модель: {model_path}")
    logger.info(f"  → Размерность: {embedding_size}")
    logger.info(f"  → Ожидаемое использование VRAM: {estimated_vram_mb} MB")
    
    try:
        # Запускаем мониторинг GPU
        gpu_monitor = GPUMonitor()
        gpu_monitor.start_monitoring()
        
        # Загружаем модель
        start_time = time.time()
        model = FridaEmbeddingsWrapper(model_path)
        
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
                    embedding=model,
                    metadatas=batch_metadatas
                )
            else:
                # Добавляем к существующей базе
                additional_store = FAISS.from_texts(
                    texts=batch_texts,
                    embedding=model,
                    metadatas=batch_metadatas
                )
                vector_store.merge_from(additional_store)
        
        vectorization_time = time.time() - vectorization_start
        logger.info(f"  → Векторизация завершена за {vectorization_time:.1f} секунд")
        
        # Сохраняем FAISS индекс
        vector_db_dir = Path(config["data_paths"]["vector_databases"])
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
        gpu_monitor.stop_monitoring()
        
        # Статистика
        logger.info(f"  → Статистика:")
        logger.info(f"    - Всего векторов: {vector_store.index.ntotal}")
        logger.info(f"    - Размерность: {vector_store.index.d}")
        logger.info(f"    - Среднее время на текст: {vectorization_time/len(texts):.3f} сек")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при создании FAISS индекса для {model_name}: {e}")
        if gpu_monitor:
            gpu_monitor.stop_monitoring()
        return False

def main():
    """Главная функция"""
    try:
        # Загружаем конфигурацию
        config = load_config()
        
        # Загружаем и обрабатываем документы
        chunks = load_and_process_documents(config)
        if not chunks:
            logger.error("Не удалось загрузить документы")
            return
        
        # Подготавливаем тексты и метаданные
        texts, metadatas = prepare_texts_and_metadata(chunks)
        logger.info(f"Подготовлено {len(texts)} текстов для векторизации")
        
        # Создаем FAISS индекс
        success = create_faiss_index(config, texts, metadatas)
        
        if success:
            logger.info("✅ Векторизация с моделью FRIDA успешно завершена")
        else:
            logger.error("❌ Ошибка при векторизации с моделью FRIDA")
            
    except KeyboardInterrupt:
        logger.info("\nВекторизация прервана пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main() 