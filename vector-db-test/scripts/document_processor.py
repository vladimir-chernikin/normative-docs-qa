"""
Модуль обработки документов для проекта векторного тестирования.

Этот модуль реализует Этап 2: Разработка системы обработки документов
- Анализ структуры Markdown документов с MarkdownHeaderTextSplitter
- Интеллектуальное разбиение текста
- Создание системы метаданных по документам
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter, CharacterTextSplitter

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Структура данных для хранения информации о чанке документа"""
    content: str
    source_file: str
    document_path: str
    hierarchy_path: str
    header_1: Optional[str] = None
    header_2: Optional[str] = None 
    header_3: Optional[str] = None
    header_4: Optional[str] = None
    chunk_number: int = 1
    total_chunks_in_section: int = 1
    text_length: int = 0
    split_method: str = "MarkdownHeaderTextSplitter"
    chunk_id: str = ""

    def __post_init__(self):
        self.text_length = len(self.content)
        if not self.chunk_id:
            # Создаем уникальный ID чанка
            base_name = Path(self.source_file).stem.replace(" ", "_").replace("(", "").replace(")", "")
            self.chunk_id = f"{base_name}_chunk{self.chunk_number}"


class DocumentProcessor:
    """Класс для обработки документов"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """Инициализация процессора документов"""
        self.config = self._load_config(config_path)
        self.setup_splitters()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Загрузка конфигурации"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Ошибка загрузки конфигурации: {e}. Используем настройки по умолчанию.")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Настройки по умолчанию"""
        return {
            "document_processing": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "headers_to_split_on": [
                    ["#", "Header 1"],
                    ["##", "Header 2"],
                    ["###", "Header 3"],
                    ["####", "Header 4"]
                ]
            }
        }
    
    def setup_splitters(self):
        """Настройка разделителей текста"""
        config = self.config.get("document_processing", {})
        
        # Настройки разбиения
        self.chunk_size = config.get("chunk_size", 1000)
        self.chunk_overlap = config.get("chunk_overlap", 200)
        
        # Настройка заголовков для разбиения
        self.headers_to_split_on = config.get("headers_to_split_on", [
            ["#", "Header 1"],
            ["##", "Header 2"],
            ["###", "Header 3"],
            ["####", "Header 4"]
        ])
        
        # Создаем разделители
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on
        )
        
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        self.character_splitter = CharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        logger.info(f"Настроены разделители: chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}")
    
    def _clean_text(self, text: str) -> str:
        """
        Очистка текста от лишних пробелов и переносов строк
        
        Args:
            text: Исходный текст
            
        Returns:
            Очищенный текст
        """
        # Объединяем строки, разделенные переносами внутри слов
        lines = text.split('\n')
        cleaned_text = ""
        for i, line in enumerate(lines):
            if i > 0 and line and line[0].islower() and not line[0].isspace():
                # Если строка начинается с маленькой буквы и без пробела, 
                # значит это продолжение предыдущей строки
                cleaned_text = cleaned_text.rstrip() + line
            else:
                if cleaned_text:
                    cleaned_text += '\n'
                cleaned_text += line
        
        # Удаляем лишние пробелы в начале и конце каждой строки
        cleaned_lines = [line.strip() for line in cleaned_text.split('\n')]
        return '\n'.join(cleaned_lines)
    
    def analyze_document_structure(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Анализ структуры документа с использованием MarkdownHeaderTextSplitter
        
        Args:
            file_path: Путь к markdown файлу
            
        Returns:
            Список документов с метаданными
        """
        try:
            # Чтение файла
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Очищаем текст от лишних пробелов и переносов
            content = self._clean_text(content)
            
            # Разбиение по заголовкам
            header_docs = self.markdown_splitter.split_text(content)
            
            logger.info(f"Анализ структуры документа {os.path.basename(file_path)}: "
                      f"{len(header_docs)} секций")
            
            # Обогащаем метаданными
            enriched_docs = []
            for doc in header_docs:
                metadata = doc.metadata.copy()
                metadata.update({
                    'source_file': os.path.basename(file_path),
                    'document_path': file_path,
                    'text_length': len(doc.page_content),
                    'split_method': 'MarkdownHeaderTextSplitter'
                })
                
                enriched_docs.append({
                    'content': doc.page_content,
                    'metadata': metadata
                })
            
            return enriched_docs
            
        except Exception as e:
            logger.error(f"Ошибка анализа документа {file_path}: {e}")
            return []
    
    def create_intelligent_chunks(self, documents):
        """
        ОПТИМИЗИРОВАННАЯ ВЕРСИЯ метода create_intelligent_chunks
        
        Интеллектуальное разбиение документов на чанки с сохранением метаданных.
        Использует только RecursiveCharacterTextSplitter с настроенными разделителями.
        
        Args:
            documents: Список документов с метаданными
            
        Returns:
            Список объектов DocumentChunk
        """
        all_chunks = []
        
        # Создаем оптимизированный сплиттер с размером чанка 1500 и перекрытием 150
        optimized_splitter = RecursiveCharacterTextSplitter(
            # Разделители в порядке приоритета: сначала попробует разделить по переносам строк,
            # затем по точкам с пробелом, затем по запятым, и т.д.
            separators=["\n\n", "\n", ". ", ", ", " ", ""],
            chunk_size=1500,
            chunk_overlap=150
        )
        
        for doc_idx, doc in enumerate(documents):
            content = doc['content']
            metadata = doc['metadata']
            content_length = len(content)
            
            logger.info(f"Обработка секции {doc_idx + 1}, длина: {content_length} символов")
            
            # Используем оптимизированный сплиттер для всех секций
            chunks = optimized_splitter.split_text(content)
            split_method = "MarkdownHeaderTextSplitter+RecursiveCharacterTextSplitter"
            logger.info(f"Использован RecursiveCharacterTextSplitter: {len(chunks)} чанков")
            
            # Создаем объекты DocumentChunk для каждого чанка
            section_chunks = []
            for chunk_idx, chunk_content in enumerate(chunks):
                # Очищаем текст чанка от лишних пробелов и переносов
                clean_chunk_content = self._clean_text(chunk_content)
                
                # Формируем путь иерархии
                hierarchy_parts = []
                for level in ["Header 1", "Header 2", "Header 3", "Header 4"]:
                    if level in metadata and metadata[level]:
                        hierarchy_parts.append(metadata[level])
                
                hierarchy_path = " > ".join(hierarchy_parts) if hierarchy_parts else "ROOT"
                
                # Создаем DocumentChunk
                doc_chunk = DocumentChunk(
                    content=clean_chunk_content,
                    source_file=metadata.get('source_file', ''),
                    document_path=metadata.get('document_path', ''),
                    hierarchy_path=hierarchy_path,
                    header_1=metadata.get('Header 1'),
                    header_2=metadata.get('Header 2'),
                    header_3=metadata.get('Header 3'),
                    header_4=metadata.get('Header 4'),
                    chunk_number=chunk_idx + 1,
                    total_chunks_in_section=len(chunks),
                    split_method=split_method
                )
                
                section_chunks.append(doc_chunk)
            
            all_chunks.extend(section_chunks)
        
        logger.info(f"Создано {len(all_chunks)} итоговых чанков")
        return all_chunks
    
    def create_zayavki_chunks(self, documents):
        """
        СПЕЦИАЛЬНАЯ ВЕРСИЯ для базы данных zayavki (Q&A формат)
        
        Агрегирует документы с одинаковыми тремя уровнями заголовков,
        затем разбивает их на чанки размером до 1500 символов с перекрытием 150.
        Если документ не агрегируется - остается маленьким чанком.
        
        Args:
            documents: Список документов с метаданными (результат работы MarkdownHeaderTextSplitter)
            
        Returns:
            Список объектов DocumentChunk
        """
        logger.info("🎯 Использую специальную обработку для базы zayavki")
        
        # Группируем документы по одинаковым трем уровням заголовков
        grouped_docs = {}
        
        for doc in documents:
            metadata = doc['metadata']
            # Создаем ключ из трех уровней заголовков
            header_key = (
                metadata.get('Header 1', ''),
                metadata.get('Header 2', ''),
                metadata.get('Header 3', '')
            )
            
            if header_key not in grouped_docs:
                grouped_docs[header_key] = []
            grouped_docs[header_key].append(doc)
        
        logger.info(f"📊 Сгруппировано в {len(grouped_docs)} уникальных категорий")
        
        # Создаем сплиттер для разбиения агрегированных групп
        zayavki_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", ", ", " ", ""],
            chunk_size=1500,
            chunk_overlap=150
        )
        
        all_chunks = []
        
        for header_key, docs_group in grouped_docs.items():
            header_1, header_2, header_3 = header_key
            
            if len(docs_group) == 1:
                # Одиночный документ - создаем маленький чанк как есть
                doc = docs_group[0]
                logger.info(f"📄 Одиночный Q&A: {header_1}/{header_2}/{header_3} - {len(doc['content'])} символов")
                
                # Формируем путь иерархии
                hierarchy_parts = [h for h in [header_1, header_2, header_3] if h]
                hierarchy_path = " > ".join(hierarchy_parts) if hierarchy_parts else "ROOT"
                
                # Создаем единственный чанк
                doc_chunk = DocumentChunk(
                    content=self._clean_text(doc['content']),
                    source_file=doc['metadata'].get('source_file', ''),
                    document_path=doc['metadata'].get('document_path', ''),
                    hierarchy_path=hierarchy_path,
                    header_1=header_1 if header_1 else None,
                    header_2=header_2 if header_2 else None,
                    header_3=header_3 if header_3 else None,
                    header_4=doc['metadata'].get('Header 4'),
                    chunk_number=1,
                    total_chunks_in_section=1,
                    split_method="MarkdownHeaderTextSplitter+ZayavkiSingle"
                )
                all_chunks.append(doc_chunk)
                
            else:
                # Несколько документов с одинаковыми заголовками - агрегируем
                aggregated_content = "\n\n".join([doc['content'] for doc in docs_group])
                logger.info(f"📦 Агрегация {len(docs_group)} Q&A: {header_1}/{header_2}/{header_3} - {len(aggregated_content)} символов")
                
                # Разбиваем агрегированный контент на чанки
                chunks = zayavki_splitter.split_text(aggregated_content)
                logger.info(f"   → Создано {len(chunks)} чанков")
                
                # Используем метаданные первого документа как базовые
                base_metadata = docs_group[0]['metadata']
                
                # Формируем путь иерархии
                hierarchy_parts = [h for h in [header_1, header_2, header_3] if h]
                hierarchy_path = " > ".join(hierarchy_parts) if hierarchy_parts else "ROOT"
                
                # Создаем чанки для агрегированной группы
                for chunk_idx, chunk_content in enumerate(chunks):
                    doc_chunk = DocumentChunk(
                        content=self._clean_text(chunk_content),
                        source_file=base_metadata.get('source_file', ''),
                        document_path=base_metadata.get('document_path', ''),
                        hierarchy_path=hierarchy_path,
                        header_1=header_1 if header_1 else None,
                        header_2=header_2 if header_2 else None,
                        header_3=header_3 if header_3 else None,
                        header_4=base_metadata.get('Header 4'),
                        chunk_number=chunk_idx + 1,
                        total_chunks_in_section=len(chunks),
                        split_method="MarkdownHeaderTextSplitter+ZayavkiAggregated"
                    )
                    all_chunks.append(doc_chunk)
        
        logger.info(f"✅ Создано {len(all_chunks)} итоговых чанков для базы zayavki")
        return all_chunks
    
    def process_document(self, file_path: str) -> List[DocumentChunk]:
        """
        Полная обработка одного документа.
        
        Args:
            file_path: Путь к markdown файлу
            
        Returns:
            Список обработанных чанков
        """
        logger.info(f"🔄 Начало обработки документа: {os.path.basename(file_path)}")
        
        # Шаг 1: Анализ структуры
        documents = self.analyze_document_structure(file_path)
        if not documents:
            logger.warning(f"Не удалось проанализировать структуру: {file_path}")
            return []
        
        # Шаг 2: Интеллектуальное разбиение
        chunks = self.create_intelligent_chunks(documents)
        
        logger.info(f"✅ Обработка завершена. Создано {len(chunks)} чанков")
        return chunks
    
    def process_zayavki_document(self, file_path: str) -> List[DocumentChunk]:
        """
        Полная обработка одного документа в формате zayavki (Q&A).
        Использует специальную логику агрегации по одинаковым заголовкам.
        
        Args:
            file_path: Путь к markdown файлу базы zayavki
            
        Returns:
            Список обработанных чанков с агрегацией по заголовкам
        """
        logger.info(f"🎯 Начало обработки документа zayavki: {os.path.basename(file_path)}")
        
        # Шаг 1: Анализ структуры
        documents = self.analyze_document_structure(file_path)
        if not documents:
            logger.warning(f"Не удалось проанализировать структуру: {file_path}")
            return []
        
        # Шаг 2: Специальное разбиение для zayavki
        chunks = self.create_zayavki_chunks(documents)
        
        logger.info(f"✅ Обработка zayavki завершена. Создано {len(chunks)} чанков")
        return chunks
    
    def process_directory(self, source_dir: str, output_dir: str = None) -> Dict[str, List[DocumentChunk]]:
        """
        Обработка всех markdown файлов в директории.
        
        Args:
            source_dir: Директория с исходными файлами
            output_dir: Директория для сохранения результатов (опционально)
            
        Returns:
            Словарь {имя_файла: список_чанков}
        """
        source_path = Path(source_dir)
        if not source_path.exists():
            logger.error(f"Директория не найдена: {source_dir}")
            return {}
        
        markdown_files = list(source_path.glob("*.md"))
        logger.info(f"📁 Найдено {len(markdown_files)} markdown файлов")
        
        all_results = {}
        
        for file_path in markdown_files:
            try:
                chunks = self.process_document(str(file_path))
                if chunks:
                    all_results[file_path.name] = chunks
                    
                    # Сохранение метаданных в JSON (если указана выходная директория)
                    if output_dir:
                        self._save_chunks_metadata(chunks, file_path.stem, output_dir)
                        
            except Exception as e:
                logger.error(f"Ошибка обработки файла {file_path}: {e}")
        
        logger.info(f"🎉 Обработка завершена! Обработано {len(all_results)} файлов")
        return all_results
    
    def _save_chunks_metadata(self, chunks: List[DocumentChunk], file_stem: str, output_dir: str):
        """Сохранение метаданных чанков в JSON файл"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        metadata_file = output_path / f"{file_stem}_metadata.json"
        
        # Конвертируем dataclass в dict для JSON сериализации
        chunks_data = [asdict(chunk) for chunk in chunks]
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Метаданные сохранены в: {metadata_file}")

def test_document_processing():
    """Тестирование системы обработки документов на небольшом примере"""
    processor = DocumentProcessor()
    
    # Тестируем на 2-3 документах для проверки корректности
    source_dir = "data/markdown_with_headers0"
    
    if not os.path.exists(source_dir):
        logger.error(f"Директория с тестовыми данными не найдена: {source_dir}")
        return
    
    # Берем первые 2 файла для тестирования
    test_files = []
    for file_name in os.listdir(source_dir):
        if file_name.endswith('.md') and len(test_files) < 2:
            test_files.append(os.path.join(source_dir, file_name))
    
    logger.info(f"🧪 Тестирование на файлах: {[os.path.basename(f) for f in test_files]}")
    
    for test_file in test_files:
        logger.info(f"\n" + "="*60)
        chunks = processor.process_document(test_file)
        
        if chunks:
            logger.info(f"📊 Статистика для {os.path.basename(test_file)}:")
            logger.info(f"   - Всего чанков: {len(chunks)}")
            logger.info(f"   - Средняя длина чанка: {sum(c.text_length for c in chunks) // len(chunks)}")
            
            # Показываем примеры иерархии
            unique_hierarchies = set(c.hierarchy_path for c in chunks[:5])
            logger.info(f"   - Примеры иерархии:")
            for hierarchy in list(unique_hierarchies)[:3]:
                logger.info(f"     • {hierarchy}")

if __name__ == "__main__":
    test_document_processing() 