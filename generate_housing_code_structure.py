#!/usr/bin/env python3
"""
Генератор полной структуры Жилищного кодекса РФ
Парсит DOCX и создает файл структуры в формате как для ГК РФ
"""

import re
from pathlib import Path
from docx import Document
from typing import List, Dict, Any

# Пути
FULLDOCS_DIR = Path(__file__).parent / "fulldocx"
OUTPUT_FILE = FULLDOCS_DIR / "Жилищный кодекс Российской Федерации_structure.txt"

# DOCX файл
DOCX_FILE = FULLDOCS_DIR / "Жилищный кодекс Российской Федерации.docx"


def generate_structure() -> List[str]:
    """Генерирует структуру ЖК РФ из DOCX"""

    doc = Document(str(DOCX_FILE))

    structure_lines = []
    structure_lines.append("--- Структура для документа: Жилищный кодекс Российской Федерации.docx ---")
    structure_lines.append("")

    current_section = None
    current_chapter = None
    content_lines = []  # Для накопления текста внутри статьи

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # Определяем уровень по отступам (первый символ с лева)
        indent_level = _get_indent_level(para)

        # Раздел (римские цифры)
        if re.match(r'^Раздел\s+[IVXLCDM]+', text, re.IGNORECASE):
            current_section = text
            structure_lines.append(f"  {text}")
            current_chapter = None
            continue

        # Глава
        if re.match(r'^Глава\s+\d+', text, re.IGNORECASE):
            current_chapter = text
            # Добавляем отступ в 2 пробела
            structure_lines.append(f"    {text}")
            continue

        # Статья
        if re.match(r'^Статья\s+[\d.]+', text, re.IGNORECASE):
            # Добавляем статью с отступом 4 пробела
            structure_lines.append(f"      {text}")
            continue

        # Пункты (цифры)
        if re.match(r'^\d+\.\s+', text):
            # Добавляем пункт с отступом 6 пробелов
            structure_lines.append(f"        {text}")
            continue

        # Подпункты (а, б, в)
        if re.match(r'^[а-яА-Я]\)\s+', text):
            # Добавляем подпункт с отступом 8 пробелов
            structure_lines.append(f"          {text}")
            continue

    return structure_lines


def _get_indent_level(paragraph) -> int:
    """Определяет уровень отступа параграфа"""
    # В DOCX отступы могут быть в разных форматах
    if paragraph.style and paragraph.style.name:
        # Проверяем стили
        style_name = paragraph.style.name.lower()
        if 'heading' in style_name or 'заголовок' in style_name:
            return 0

    # Проверяем отступы в параграфе
    if paragraph.paragraph_format and paragraph.paragraph_format.first_line_indent:
        indent_pt = paragraph.paragraph_format.first_line_indent.pt
        if indent_pt > 0:
            return int(indent_pt / 12)  # Приблизительно

    return 0


def main():
    """Главная функция"""

    print(f"Чтение: {DOCX_FILE}")
    print(f"Запись: {OUTPUT_FILE}")

    if not DOCX_FILE.exists():
        print(f"❌ Файл не найден: {DOCX_FILE}")
        return

    # Генерируем структуру
    structure = generate_structure()

    # Добавляем информацию о начале и конце документа
    final_output = [
        "--- Структура для документа: Жилищный кодекс Российской Федерации.docx ---",
        "",
        "НАЧАЛО ДОКУМЕНТА:",
    ]
    final_output.extend(structure)
    final_output.append("")
    final_output.append("КОНЕЦ ДОКУМЕНТА:")

    # Записываем в файл
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_output))

    print(f"✅ Создано строк: {len(final_output)}")
    print(f"✅ Файл сохранен: {OUTPUT_FILE}")

    # Статистика
    sections = sum(1 for line in final_output if 'Раздел' in line)
    chapters = sum(1 for line in final_output if 'Глава' in line and 'Раздел' not in line)
    articles = sum(1 for line in final_output if 'Статья' in line and 'Глава' not in line)

    print(f"\n📊 Статистика:")
    print(f"   Разделов: {sections}")
    print(f"   Глав: {chapters}")
    print(f"   Статей: {articles}")


if __name__ == '__main__':
    main()
