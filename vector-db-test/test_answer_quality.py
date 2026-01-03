"""
Автоматические тесты качества ответов AI для нормативных документов

Проверяет:
1. Релевантность ответов (на вопрос отвечает по существу)
2. Полноту ответов (достаточно ли информации)
3. Наличие источников (есть ли ссылки на документы)
4. Стоимость (соответствует ли ожидаемой)
"""

import asyncio
import sys
import os
import logging
from typing import List, Dict, Tuple
from datetime import datetime

# Добавляем путь к модулю backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from backend.question_classifier import question_classifier

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ТЕСТОВЫЕ ВОПРОСЫ С ЭТАЛОННЫМИ КРИТЕРИЯМИ
# ============================================================================

TEST_QUESTIONS = [
    {
        "id": 1,
        "question": "Какова температура горячей воды в жилом помещении?",
        "category": "технические требования",
        "must_contain": ["60", "75", "градус", "°C", "температур"],
        "must_not_contain": ["не знаю", "нет информации"],
        "min_length": 50,
        "should_have_source": True
    },
    {
        "id": 2,
        "question": "Кто должен платить за капитальный ремонт?",
        "category": "оплата",
        "must_contain": ["собственник", "владелец", "плата", "обязан"],
        "must_not_contain": ["некто", "неясно"],
        "min_length": 80,
        "should_have_source": True
    },
    {
        "id": 3,
        "question": "Какой срок давности по коммунальным долгам?",
        "category": "юридические сроки",
        "must_contain": ["3 год", "три года", "исковая давность"],
        "must_not_contain": [],
        "min_length": 60,
        "should_have_source": True
    },
    {
        "id": 4,
        "question": "Что такое общедомовое имущество?",
        "category": "определения",
        "must_contain": ["многоквартирный дом", "общее", "имущество", "собственность"],
        "must_not_contain": [],
        "min_length": 100,
        "should_have_source": True
    },
    {
        "id": 5,
        "question": "Можно ли проводить перерасчет платы за ЖКУ?",
        "category": "перерасчет",
        "must_contain": ["да", "можно", "перерасчет", "услуга"],
        "must_not_contain": ["нельзя", "запрещено"],
        "min_length": 70,
        "should_have_source": True
    },
    {
        "id": 6,
        "question": "Кто отвечает за содержание общего имущества?",
        "category": "обязанности",
        "must_contain": ["управляющая", "компания", "УК", "собственник", "ТСЖ"],
        "must_not_contain": [],
        "min_length": 60,
        "should_have_source": True
    },
    {
        "id": 7,
        "question": "Каковы права собственника помещения?",
        "category": "права",
        "must_contain": ["собственник", "право", "владеть", "пользоваться", "распоряжаться"],
        "must_not_contain": [],
        "min_length": 100,
        "should_have_source": True
    },
    {
        "id": 8,
        "question": "Что входит в содержание жилого помещения?",
        "category": "содержание",
        "must_contain": ["ремонт", "обслуживание", "инженер", "коммуникация"],
        "must_not_contain": [],
        "min_length": 80,
        "should_have_source": True
    },
    {
        "id": 9,
        "question": "Как отключить коммунальные услуги?",
        "category": "отключение",
        "must_contain": ["долг", "неуплата", "уведомление", "суд", "приказ"],
        "must_not_contain": [],
        "min_length": 100,
        "should_have_source": True
    },
    {
        "id": 10,
        "question": "В чем разница между капитальным и текущим ремонтом?",
        "category": "ремонт",
        "must_contain": ["капитальный", "текущий", "ремонт", "срок", "служба"],
        "must_not_contain": [],
        "min_length": 120,
        "should_have_source": True
    }
]


# ============================================================================
# КЛАСС ДЛЯ ТЕСТИРОВАНИЯ
# ============================================================================

class AnswerQualityTester:
    """Тестировщик качества ответов AI"""

    def __init__(self, api_url: str = "http://localhost:8008"):
        self.api_url = api_url
        self.results = []

    async def test_preview_cost(self, question: str, model: str = "yandexgpt") -> Dict:
        """Тест предпросмотра стоимости"""
        try:
            tokens = question_classifier.estimate_tokens(question, model)
            cost = question_classifier.calculate_cost(question, model)

            return {
                "success": True,
                "cost": cost,
                "tokens": tokens,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "cost": None,
                "tokens": None,
                "error": str(e)
            }

    def check_relevance(self, answer: str, test_case: Dict) -> Tuple[bool, List[str]]:
        """Проверка релевантности ответа"""
        issues = []

        # Проверяем обязательные ключевые слова
        answer_lower = answer.lower()
        for keyword in test_case.get("must_contain", []):
            if keyword.lower() not in answer_lower:
                issues.append(f"Отсутствует ключевое слово: '{keyword}'")

        # Проверяем запрещенные слова
        for forbidden in test_case.get("must_not_contain", []):
            if forbidden.lower() in answer_lower:
                issues.append(f"Присутствует запрещенное слово: '{forbidden}'")

        # Проверяем минимальную длину
        if len(answer) < test_case.get("min_length", 0):
            issues.append(f"Ответ слишком короткий: {len(answer)} < {test_case['min_length']}")

        return len(issues) == 0, issues

    def format_test_result(self, test_id: int, passed: bool, message: str) -> str:
        """Форматирование результата теста"""
        status = "✅ PASS" if passed else "❌ FAIL"
        return f"{status} | Test #{test_id:02d} | {message}"

    async def run_single_test(self, test_case: Dict) -> Dict:
        """Запуск одного теста"""
        logger.info(f"\n{'='*80}")
        logger.info(f"ТЕСТ #{test_case['id']}: {test_case['question']}")
        logger.info(f"Категория: {test_case['category']}")
        logger.info(f"{'='*80}")

        result = {
            "test_id": test_case['id'],
            "question": test_case['question'],
            "category": test_case['category'],
            "passed": False,
            "issues": [],
            "preview_cost": None,
            "actual_answer": None,
            "execution_time": 0
        }

        # 1. Тест предпросмотра стоимости
        logger.info("Шаг 1: Проверка предпросмотра стоимости...")
        preview = await self.test_preview_cost(test_case['question'])

        if not preview['success']:
            result['issues'].append(f"Ошибка preview: {preview['error']}")
            logger.error(f"❌ Preview не работает: {preview['error']}")
        else:
            result['preview_cost'] = preview['cost']
            logger.info(f"✅ Preview: {preview['cost']} ({preview['tokens']['total_tokens_avg']} токенов)")

        # 2. Проверка ответа (если был бы реальный API вызов)
        # TODO: Добавить реальный вызов API когда будет доступен
        logger.info("Шаг 2: Проверка ответа (SIMULATED)...")
        logger.info("⚠️  Реальный API вызов не реализован в тестах")
        logger.info("💡 Для полноценных тестов нужно добавить HTTP запрос к /llm-search")

        return result

    async def run_all_tests(self) -> Dict:
        """Запуск всех тестов"""
        logger.info("\n" + "="*80)
        logger.info("ЗАПУСК АВТОМАТИЧЕСКИХ ТЕСТОВ КАЧЕСТВА ОТВЕТОВ")
        logger.info(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Всего тестов: {len(TEST_QUESTIONS)}")
        logger.info("="*80 + "\n")

        start_time = datetime.now()
        results = {
            "total": len(TEST_QUESTIONS),
            "passed": 0,
            "failed": 0,
            "tests": []
        }

        for test_case in TEST_QUESTIONS:
            result = await self.run_single_test(test_case)
            results['tests'].append(result)

            if result['passed']:
                results['passed'] += 1
            else:
                results['failed'] += 1

        end_time = datetime.now()
        results['execution_time'] = (end_time - start_time).total_seconds()

        # Печатаем отчет
        self.print_report(results)

        return results

    def print_report(self, results: Dict):
        """Печать отчета о тестах"""
        logger.info("\n" + "="*80)
        logger.info("ОТЧЕТ О ТЕСТИРОВАНИИ")
        logger.info("="*80)

        logger.info(f"\n📊 СТАТИСТИКА:")
        logger.info(f"   Всего тестов: {results['total']}")
        logger.info(f"   ✅ Прошло: {results['passed']} ({results['passed']/results['total']*100:.1f}%)")
        logger.info(f"   ❌ Пало: {results['failed']} ({results['failed']/results['total']*100:.1f}%)")
        logger.info(f"   ⏱️  Время: {results['execution_time']:.2f} сек")

        logger.info(f"\n📋 ДЕТАЛИ ПО КАТЕГОРИЯМ:")
        categories = {}
        for test in results['tests']:
            cat = test['category']
            if cat not in categories:
                categories[cat] = {"passed": 0, "failed": 0}
            if test['passed']:
                categories[cat]['passed'] += 1
            else:
                categories[cat]['failed'] += 1

        for cat, stats in categories.items():
            total = stats['passed'] + stats['failed']
            pct = stats['passed'] / total * 100 if total > 0 else 0
            logger.info(f"   {cat}: {stats['passed']}/{total} ({pct:.0f}%)")

        logger.info(f"\n❌ ПАДАЮЩИЕ ТЕСТЫ:")
        failed_tests = [t for t in results['tests'] if not t['passed']]
        if failed_tests:
            for test in failed_tests:
                logger.info(f"\n   Тест #{test['test_id']}: {test['question'][:60]}...")
                for issue in test['issues']:
                    logger.info(f"   - {issue}")
        else:
            logger.info("   Все тесты прошли успешно!")

        logger.info("\n" + "="*80)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Главная функция"""
    tester = AnswerQualityTester()

    try:
        results = await tester.run_all_tests()

        # Код выхода: 0 если все прошло, 1 если есть падающие тесты
        if results['failed'] > 0:
            logger.error(f"\n❌ {results['failed']} тест(ов) не прошли")
            sys.exit(1)
        else:
            logger.info(f"\n✅ Все {results['total']} тестов прошли успешно!")
            sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Ошибка при запуске тестов: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
