#!/usr/bin/env python3
"""
Умный чанкер для кодексов и федеральных законов
Мультиуровневый подход с parent-child ссылками (золотой стандарт RAG)

Уровень 1: Полная статья (все пункты вместе) - для контекста
Уровень 2: Отдельные пункты с подпунктами - для точного поиска
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from docx import Document

logger = logging.getLogger(__name__)


class SmartDocumentChunker:
    """Умный чанкер для кодексов (ГК РФ, ЖК РФ, ФЗ) с мультиуровневым подходом"""

    def __init__(self, docx_file: Path, structure_file: Path):
        self.docx_file = docx_file
        self.structure_file = structure_file
        self.structure = self._parse_structure()
        self.doc_text = self._read_docx()

    def _parse_structure(self) -> List[Dict[str, Any]]:
        """Парсит файл структуры и извлекает иерархию элементов"""

        content = self.structure_file.read_text(encoding='utf-8')
        lines = content.split('\n')

        structure = []
        current_section = None
        current_chapter = None

        for line in lines:
            line = line.rstrip()
            if not line or line.startswith('---'):
                continue

            # Определяем уровень вложенности по количеству пробелов в начале
            indent = len(line) - len(line.lstrip())
            text = line.strip()

            # Раздел I, II, III и т.д. (римские цифры)
            if re.match(r'^Раздел\s+[IVXLCDM]+', text, re.IGNORECASE):
                current_section = text
                structure.append({
                    'type': 'section',
                    'title': text,
                    'level': 0
                })
                current_chapter = None
                continue

            # Глава 1, 2, 3 и т.д.
            if re.match(r'^Глава\s+\d+', text, re.IGNORECASE):
                current_chapter = text
                structure.append({
                    'type': 'chapter',
                    'title': text,
                    'section': current_section,
                    'level': 1
                })
                continue

            # Статья 1, 2, 3 и т.д.
            if re.match(r'^Статья\s+[\d.]+', text, re.IGNORECASE):
                structure.append({
                    'type': 'article',
                    'title': text,
                    'chapter': current_chapter,
                    'section': current_section,
                    'level': 2
                })
                continue

            # Приложения (для постановлений)
            if re.match(r'^Приложение', text, re.IGNORECASE):
                structure.append({
                    'type': 'appendix',
                    'title': text,
                    'level': 0
                })
                continue

        logger.info(f"Парсинг структуры: найдено {len(structure)} элементов")
        return structure

    def _read_docx(self) -> List[str]:
        """Читает DOCX и возвращает список параграфов"""

        doc = Document(str(self.docx_file))
        paragraphs = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)

        logger.info(f"Прочитано {len(paragraphs)} параграфов из DOCX")
        return paragraphs

    def extract_text_with_structure(self) -> List[Dict[str, Any]]:
        """Извлекает мультиуровневые чанки с parent-child ссылками"""

        chunks = []
        article_chunks = {}  # Для хранения level 1 чанков (полные статьи)

        current_article_title = None
        current_article_lines = []
        current_point_number = None
        current_point_lines = []

        current_metadata = {
            'document': self.docx_file.stem,
            'type': 'Кодекс',
            'section': None,
            'chapter': None,
            'article': None,
            'level': 2
        }

        # Создаем множество заголовков из структуры для быстрого поиска
        structure_items = {item['title']: item for item in self.structure}

        for line in self.doc_text:
            # Проверяем, является ли строка заголовком статьи
            if line in structure_items and structure_items[line]['type'] == 'article':
                # Сохраняем предыдущий пункт
                if current_point_lines:
                    point_chunk = {
                        'text': '\n'.join(current_point_lines),
                        'metadata': current_metadata.copy(),
                        'level': 2,
                        'parent_article': current_article_title
                    }
                    chunks.append(point_chunk)

                # Сохраняем предыдущую статью целиком (level 1)
                if current_article_lines and current_article_title:
                    article_chunks[current_article_title] = {
                        'text': '\n'.join(current_article_lines),
                        'metadata': {
                            'document': self.docx_file.stem,
                            'type': 'Кодекс',
                            'section': current_metadata.get('section'),
                            'chapter': current_metadata.get('chapter'),
                            'article': current_article_title,
                            'level': 1
                        },
                        'level': 1,
                        'article_id': current_article_title
                    }

                # Начинаем новую статью
                struct_item = structure_items[line]
                current_article_title = line
                current_article_lines = [line]
                current_point_number = None
                current_point_lines = []

                # Обновляем метаданные
                current_metadata = {
                    'document': self.docx_file.stem,
                    'type': 'Кодекс',
                    'section': struct_item.get('section'),
                    'chapter': struct_item.get('chapter'),
                    'article': line,
                    'level': 2
                }
                continue

            # Проверяем пункт (цифры в начале)
            point_match = re.match(r'^(\d+)\.\s+(.+)', line)
            if point_match and current_article_title:
                # Сохраняем предыдущий пункт
                if current_point_lines:
                    point_chunk = {
                        'text': '\n'.join(current_point_lines),
                        'metadata': current_metadata.copy(),
                        'level': 2,
                        'parent_article': current_article_title
                    }
                    chunks.append(point_chunk)

                # Начинаем новый пункт
                current_point_number = point_match.group(1)
                current_point_lines = [line]

                # Добавляем к статье
                current_article_lines.append(line)
                continue

            # Проверяем подпункт (а, б, в, г и т.д.)
            sublist_match = re.match(r'^([а-яА-Яa-zA-Z]\))\s+(.+)', line)
            if sublist_match:
                # Добавляем к текущему пункту
                current_point_lines.append(line)
                current_article_lines.append(line)
                continue

            # Обычный текст - добавляем везде
            if current_article_title:
                current_article_lines.append(line)
                if current_point_lines:
                    current_point_lines.append(line)

        # Сохраняем последний пункт
        if current_point_lines:
            point_chunk = {
                'text': '\n'.join(current_point_lines),
                'metadata': current_metadata.copy(),
                'level': 2,
                'parent_article': current_article_title
            }
            chunks.append(point_chunk)

        # Сохраняем последнюю статью
        if current_article_lines and current_article_title:
            article_chunks[current_article_title] = {
                'text': '\n'.join(current_article_lines),
                'metadata': {
                    'document': self.docx_file.stem,
                    'type': 'Кодекс',
                    'section': current_metadata.get('section'),
                    'chapter': current_metadata.get('chapter'),
                    'article': current_article_title,
                    'level': 1
                },
                'level': 1,
                'article_id': current_article_title
            }

        # Добавляем level 1 чанки (полные статьи) в начало списка
        all_chunks = []
        for article_title, article_chunk in article_chunks.items():
            all_chunks.append(article_chunk)

        # Добавляем level 2 чанки (пункты)
        all_chunks.extend(chunks)

        logger.info(f"Создано {len(article_chunks)} чанков level 1 (статьи)")
        logger.info(f"Создано {len(chunks)} чанков level 2 (пункты)")
        logger.info(f"Всего чанков: {len(all_chunks)}")

        return all_chunks


# Тестовый запуск
if __name__ == '__main__':
    import sys
    from config import FULLDOCS_DIR

    if len(sys.argv) > 1:
        docx_path = Path(sys.argv[1])
        structure_path = Path(str(docx_path).replace('.docx', '_structure.txt'))
    else:
        # Тест по умолчанию на Жилищном кодексе
        docx_path = FULLDOCS_DIR / "Жилищный кодекс Российской Федерации.docx"
        structure_path = FULLDOCS_DIR / "Жилищный кодекс Российской Федерации_structure.txt"

    if not docx_path.exists():
        logger.error(f"Файл не найден: {docx_path}")
        sys.exit(1)

    if not structure_path.exists():
        logger.error(f"Файл структуры не найден: {structure_path}")
        sys.exit(1)

    logger.info(f"Обработка: {docx_path.name}")
    logger.info(f"Структура: {structure_path.name}")

    chunker = SmartDocumentChunker(docx_path, structure_path)
    chunks = chunker.extract_text_with_structure()

    logger.info(f"Создано {len(chunks)} чанков")

    # Показываем примеры level 1 (статьи)
    logger.info("\n" + "=" * 80)
    logger.info("ПРИМЕРЫ ЧАНКОВ LEVEL 1 (ПОЛНЫЕ СТАТЬИ):")
    logger.info("=" * 80)
    level_1_count = 0
    for i, chunk in enumerate(chunks, 1):
        if chunk['level'] == 1:
            level_1_count += 1
            logger.info(f"\nЧАНК LEVEL 1 #{level_1_count}")
            logger.info(f"Article ID: {chunk.get('article_id', 'N/A')}")
            logger.info(f"Метаданные: {chunk['metadata']}")
            logger.info(f"Размер: {len(chunk['text'])} символов")
            logger.info(f"Текст (первые 300 символов): {chunk['text'][:300]}...")
            logger.info("-" * 80)
            if level_1_count >= 2:
                break

    # Показываем примеры level 2 (пункты)
    logger.info("\n" + "=" * 80)
    logger.info("ПРИМЕРЫ ЧАНКОВ LEVEL 2 (ПУНКТЫ):")
    logger.info("=" * 80)
    level_2_count = 0
    for i, chunk in enumerate(chunks, 1):
        if chunk['level'] == 2:
            level_2_count += 1
            logger.info(f"\nЧАНК LEVEL 2 #{level_2_count}")
            logger.info(f"Parent Article: {chunk.get('parent_article', 'N/A')}")
            logger.info(f"Метаданные: {chunk['metadata']}")
            logger.info(f"Размер: {len(chunk['text'])} символов")
            logger.info(f"Текст (первые 300 символов): {chunk['text'][:300]}...")
            logger.info("-" * 80)
            if level_2_count >= 5:
                break

    # Статистика
    level_1_total = sum(1 for c in chunks if c['level'] == 1)
    level_2_total = sum(1 for c in chunks if c['level'] == 2)

    logger.info("\n" + "=" * 80)
    logger.info("СТАТИСТИКА:")
    logger.info("=" * 80)
    logger.info(f"Level 1 (статьи): {level_1_total}")
    logger.info(f"Level 2 (пункты): {level_2_total}")
    logger.info(f"Всего: {len(chunks)}")
