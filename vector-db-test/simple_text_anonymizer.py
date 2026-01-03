#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой анонимизатор текста для маскирования персональных данных.
Основан на коде из refac202.md для извлечения функциональности анонимизации.
"""

import re
from typing import List, Tuple, Dict

class TextAnonymizer:
    """
    Класс для анонимизации персональных данных в тексте
    """
    
    def __init__(self):
        # Счетчик для генерации уникальных плейсхолдеров
        self.placeholder_counter = 1
        # Словарь для сопоставления плейсхолдеров с типами данных
        self.pii_mapping = {}
        # Словарь для обратного преобразования (если потребуется)
        self.reverse_mapping = {}
    
    def reset_state(self):
        """Сбрасывает состояние анонимизатора"""
        self.placeholder_counter = 1
        self.pii_mapping.clear()
        self.reverse_mapping.clear()
    
    def _create_placeholder(self, pii_type: str) -> str:
        """Создает новый плейсхолдер для указанного типа данных"""
        placeholder = f"[ДАННЫЕ_{self.placeholder_counter}]"
        self.pii_mapping[placeholder] = pii_type
        self.placeholder_counter += 1
        return placeholder
    
    def _mask_phones(self, text: str) -> str:
        """Маскирует номера телефонов"""
        # Российские номера телефонов в различных форматах
        phone_patterns = [
            r'\+7[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}',  # +7(999)999-99-99
            r'8[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}',    # 8(999)999-99-99
            r'\b\d{3}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}\b',             # 999-999-99-99
            r'\b\d{11}\b',                                              # 89999999999
        ]
        
        for pattern in phone_patterns:
            def replace_phone(match):
                placeholder = self._create_placeholder('номер телефона')
                self.reverse_mapping[placeholder] = match.group()
                return placeholder
            
            text = re.sub(pattern, replace_phone, text)
        
        return text
    
    def _mask_names(self, text: str) -> str:
        """Маскирует имена, фамилии и отчества"""
        # Паттерны для русских ФИО
        name_patterns = [
            # Полное ФИО (3 слова с заглавными буквами)
            r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\b',
            # Фамилия И.О.
            r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.',
            # Обращается ФИО (учитываем контекст)
            r'(?:обращается|от)\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?',
        ]
        
        for pattern in name_patterns:
            def replace_name(match):
                # Для контекстных паттернов сохраняем начальное слово
                matched_text = match.group()
                if matched_text.lower().startswith(('обращается', 'от')):
                    prefix_match = re.match(r'(обращается|от)\s+', matched_text, re.IGNORECASE)
                    if prefix_match:
                        prefix = prefix_match.group()
                        placeholder = self._create_placeholder('ФИО')
                        self.reverse_mapping[placeholder] = matched_text[len(prefix):]
                        return prefix + placeholder
                
                placeholder = self._create_placeholder('ФИО')
                self.reverse_mapping[placeholder] = matched_text
                return placeholder
            
            text = re.sub(pattern, replace_name, text, flags=re.IGNORECASE)
        
        return text
    
    def _mask_addresses(self, text: str) -> str:
        """Маскирует адреса"""
        address_patterns = [
            # Улица, дом, квартира
            r'\b(?:ул\.|улица)\s*[А-ЯЁа-яё\s]+,?\s*(?:д\.|дом)\s*\d+[а-я]?(?:,?\s*(?:кв\.|квартира)\s*\d+)?',
            # Город, улица
            r'\bг\.\s*[А-ЯЁ][а-яё-]+(?:\s+[А-ЯЁа-яё-]+)*',
            # Почтовый индекс
            r'\b\d{6}\b',
        ]
        
        for pattern in address_patterns:
            def replace_address(match):
                placeholder = self._create_placeholder('адрес')
                self.reverse_mapping[placeholder] = match.group()
                return placeholder
            
            text = re.sub(pattern, replace_address, text, flags=re.IGNORECASE)
        
        return text
    
    def _mask_dates(self, text: str) -> str:
        """Маскирует даты"""
        date_patterns = [
            r'\b\d{1,2}\.\d{1,2}\.\d{4}\b',          # 01.01.2024
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',            # 01/01/2024
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',            # 2024-01-01
        ]
        
        for pattern in date_patterns:
            def replace_date(match):
                placeholder = self._create_placeholder('дата')
                self.reverse_mapping[placeholder] = match.group()
                return placeholder
            
            text = re.sub(pattern, replace_date, text)
        
        return text
    
    def _mask_car_numbers(self, text: str) -> str:
        """Маскирует автомобильные номера"""
        car_patterns = [
            r'\b[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}\b',  # А123БВ123
            r'\b\d{4}[АВЕКМНОРСТУХ]{2}\d{2,3}\b',                # 1234АВ123
            r'\b[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2}\b',    # А123БВ12 (без региона)
        ]
        
        for pattern in car_patterns:
            def replace_car(match):
                placeholder = self._create_placeholder('автомобильный номер')
                self.reverse_mapping[placeholder] = match.group()
                return placeholder
            
            text = re.sub(pattern, replace_car, text)
        
        return text
    
    def _mask_emails(self, text: str) -> str:
        """Маскирует email адреса"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        def replace_email(match):
            placeholder = self._create_placeholder('email')
            self.reverse_mapping[placeholder] = match.group()
            return placeholder
        
        return re.sub(email_pattern, replace_email, text)
    
    def _mask_birth_years(self, text: str) -> str:
        """Маскирует годы рождения"""
        # Ищем контекст "года рождения" и связанные числа
        birth_year_pattern = r'\b(19\d{2}|20\d{2})\s*года?\s*рождения|\b(?:рожден[а-я]*|года?\s*рождения)\s*(19\d{2}|20\d{2})'
        
        def replace_birth_year(match):
            placeholder = self._create_placeholder('год рождения')
            self.reverse_mapping[placeholder] = match.group()
            return placeholder
        
        return re.sub(birth_year_pattern, replace_birth_year, text, flags=re.IGNORECASE)
    
    def anonymize_text(self, text: str) -> str:
        """
        Основная функция анонимизации текста
        
        Args:
            text: Исходный текст для анонимизации
            
        Returns:
            Анонимизированный текст с плейсхолдерами
        """
        if not text or not isinstance(text, str):
            return text
        
        # Применяем все методы маскирования
        masked_text = text
        masked_text = self._mask_phones(masked_text)
        masked_text = self._mask_names(masked_text) 
        masked_text = self._mask_addresses(masked_text)
        masked_text = self._mask_dates(masked_text)
        masked_text = self._mask_car_numbers(masked_text)
        masked_text = self._mask_emails(masked_text)
        masked_text = self._mask_birth_years(masked_text)
        
        return masked_text
    
    def get_pii_mapping(self) -> Dict[str, str]:
        """Возвращает словарь плейсхолдеров и их типов"""
        return self.pii_mapping.copy()
    
    def get_pii_explanation(self) -> str:
        """
        Создает объяснение замен для LLM в том же формате, что и в оригинальном коде
        """
        if not self.pii_mapping:
            return (
                "Личные данные в предоставленном тексте не были автоматически "
                "замаскированы или не найдены.\n"
            )
        
        explanation = (
            "В следующем тексте некоторые личные данные были заменены плейсхолдерами. "
            "Если нужно будет сослаться на эти данные, используйте плейсхолдеры "
            "точно в таком виде, как они даны.\n"
            "Список замен (плейсхолдер: тип данных):\n"
        )
        
        # Сортируем плейсхолдеры по номеру
        sorted_placeholders = sorted(
            self.pii_mapping.items(),
            key=lambda x: int(x[0].split('_')[1][:-1])
        )
        
        for placeholder, pii_type in sorted_placeholders:
            explanation += f"- {placeholder}: ({pii_type})\n"
        
        return explanation


def anonymize_message(message: str) -> Tuple[str, str]:
    """
    Простая функция для анонимизации сообщения
    
    Args:
        message: Исходное сообщение
        
    Returns:
        Tuple из (анонимизированного текста, объяснения замен)
    """
    anonymizer = TextAnonymizer()
    anonymized_text = anonymizer.anonymize_text(message)
    explanation = anonymizer.get_pii_explanation()
    
    return anonymized_text, explanation


if __name__ == "__main__":
    # Пример использования
    test_message = """
    Добрый день! Обращается Иванов Петр Сергеевич из организации ООО "Рога и копыта". 
    Мой номер телефона +7(999)123-45-67. Проживаю по адресу г. Москва, ул. Ленина, д. 10, кв. 25.
    Родился 15.03.1985 года. Мой автомобиль А123БВ99. 
    Электронная почта: test@example.com.
    
    07.05.2025 г. с номера телефона 8(901)234-56-78 заказов на прибытие автомобиля не поступало.
    """
    
    print("=== ТЕСТИРОВАНИЕ АНОНИМИЗАТОРА ===\n")
    print("Исходный текст:")
    print(test_message)
    print("\n" + "="*50 + "\n")
    
    anonymized, explanation = anonymize_message(test_message)
    
    print("Анонимизированный текст:")
    print(anonymized)
    print("\n" + "="*50 + "\n")
    
    print("Объяснение замен:")
    print(explanation)
