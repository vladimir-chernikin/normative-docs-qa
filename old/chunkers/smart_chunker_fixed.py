#!/usr/bin/env python3
"""
Умный чанкер с фильтрацией по размеру
Исправленная версия с устранением проблем
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any

# Импортируем оригинальный чанкер
import sys
sys.path.insert(0, str(Path(__file__).parent))
from smart_chunker import SmartDocumentChunker

logger = logging.getLogger(__name__)


class FixedSmartDocumentChunker:
    """Чанкер с исправлением проблем размера"""
    
    def __init__(self, docx_file: Path, structure_file: Path):
        self.docx_file = docx_file
        self.structure_file = structure_file
        self.chunker = SmartDocumentChunker(docx_file, structure_file)
        
        # Настройки фильтрации
        self.MIN_CHUNK_SIZE = 100  # Минимальный размер (было 50)
        self.MAX_CHUNK_SIZE = 1500  # Максимальный размер (было 2000+)
    
    def extract_chunks(self) -> List[Dict[str, Any]]:
        """Извлекает чанки с исправлением размера"""
        
        # Получаем исходные чанки
        raw_chunks = self.chunker.extract_text_with_structure()
        logger.info(f"Получено {len(raw_chunks)} исходных чанков")
        
        # Фильтруем и исправляем
        fixed_chunks = self._fix_chunk_sizes(raw_chunks)
        logger.info(f"После исправления: {len(fixed_chunks)} чанков")
        
        return fixed_chunks
    
    def _fix_chunk_sizes(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Исправляет размеры чанков"""
        
        fixed = []
        i = 0
        
        while i < len(chunks):
            chunk = chunks[i]
            text = chunk['text']
            text_len = len(text)
            
            # Слишком мелкий - пытаемся объединить со следующим
            if text_len < self.MIN_CHUNK_SIZE:
                if i + 1 < len(chunks):
                    # Объединяем с следующим
                    next_chunk = chunks[i + 1]
                    combined_text = text + '\n\n' + next_chunk['text']
                    
                    # Проверяем не превышает ли максимум
                    if len(combined_text) <= self.MAX_CHUNK_SIZE:
                        # Создаем объединенный чанк
                        merged_chunk = {
                            'text': combined_text,
                            'metadata': chunk['metadata'].copy(),
                            'level': chunk['level'],
                            'merged': True
                        }
                        fixed.append(merged_chunk)
                        i += 2  # Пропускаем оба чанка
                        continue
            
            # Слишком крупный - разбиваем
            if text_len > self.MAX_CHUNK_SIZE:
                split_chunks = self._split_large_chunk(chunk)
                fixed.extend(split_chunks)
            else:
                # Нормальный размер
                fixed.append(chunk)
            
            i += 1
        
        return fixed
    
    def _split_large_chunk(self, chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Разбивает крупный чанк на части"""
        
        text = chunk['text']
        paragraphs = text.split('\n')
        
        result = []
        current_part = []
        current_len = 0
        
        for para in paragraphs:
            para_len = len(para)
            
            # Если один параграф слишком большой - разбиваем по предложениям
            if para_len > self.MAX_CHUNK_SIZE:
                if current_part:
                    result.append(self._create_chunk('\n'.join(current_part), chunk['metadata']))
                    current_part = []
                    current_len = 0
                
                # Разбиваем параграф по предложениям
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sent in sentences:
                    if current_len + len(sent) > self.MAX_CHUNK_SIZE and current_part:
                        result.append(self._create_chunk('\n'.join(current_part), chunk['metadata']))
                        current_part = []
                        current_len = 0
                    
                    current_part.append(sent)
                    current_len += len(sent) + 1
            else:
                # Проверяем место
                if current_len + para_len > self.MAX_CHUNK_SIZE and current_part:
                    result.append(self._create_chunk('\n'.join(current_part), chunk['metadata']))
                    current_part = []
                    current_len = 0
                
                current_part.append(para)
                current_len += para_len + 1
        
        # Добавляем последнюю часть
        if current_part:
            result.append(self._create_chunk('\n'.join(current_part), chunk['metadata']))
        
        logger.info(f"Разбит крупный чанк на {len(result)} частей")
        return result
    
    def _create_chunk(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Создает чанк с копией метаданных"""
        return {
            'text': text,
            'metadata': metadata.copy(),
            'level': metadata.get('level', 2)
        }


if __name__ == '__main__':
    # Тест
    chunker = FixedSmartDocumentChunker(
        Path("fulldocx/Гражданский кодекс Российской Федерации (часть вторая).docx"),
        Path("fulldocx/Гражданский кодекс Российской Федерации (часть вторая)_structure.txt")
    )
    chunks = chunker.extract_chunks()
    print(f"Создано {len(chunks)} чанков")
