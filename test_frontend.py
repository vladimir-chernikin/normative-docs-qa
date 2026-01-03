#!/usr/bin/env python3
"""
Автоматическое тестирование фронтенда API
"""

import requests
import json
from typing import Dict, List

FRONTEND_URL = "http://localhost:8080"
API_URL = "http://localhost:8001"

def test_frontend_page() -> bool:
    """Тест загрузки главной страницы"""
    print("🧪 ТЕСТ 1: Загрузка главной страницы")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        assert response.status_code == 200, f"Ожидается 200, получено {response.status_code}"
        # Проверяем по ключевым элементам
        has_qa = "QA" in response.text or "Система" in response.text
        has_search = "search-input" in response.text or "searchQuery" in response.text
        has_button = "search-button" in response.text or "searchButton" in response.text
        has_title = "Нормативных Документов" in response.text

        assert has_qa, "Заголовок не найден"
        assert has_search, "Поле поиска не найдено"
        assert has_button, "Кнопка поиска не найдена"
        assert has_title, "Заголовок страницы не найден"

        print("   ✅ PASSED: Главная страница загружена\n")
        return True
    except Exception as e:
        print(f"   ❌ FAILED: {e}\n")
        return False


def test_api_root() -> bool:
    """Тест корневого API endpoint"""
    print("🧪 ТЕСТ 2: API Root endpoint")
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "QA System for Housing Documents"
        assert data["status"] == "ready"
        print("   ✅ PASSED: API root отвечает корректно\n")
        return True
    except Exception as e:
        print(f"   ❌ FAILED: {e}\n")
        return False


def test_api_health() -> bool:
    """Тест health check endpoint"""
    print("🧪 ТЕСТ 3: Health check")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] == True
        assert data["database_loaded"] == True
        print("   ✅ PASSED: Health check OK\n")
        return True
    except Exception as e:
        print(f"   ❌ FAILED: {e}\n")
        return False


def test_api_stats() -> bool:
    """Тест статистики"""
    print("🧪 ТЕСТ 4: Статистика БД")
    try:
        response = requests.get(f"{API_URL}/stats", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["documents_count"] == 18
        assert data["chunks_count"] == 2078
        assert data["embedding_dimension"] == 384
        assert data["size_mb"] == 11
        print(f"   ✅ PASSED: Статистика корректна")
        print(f"      - Документов: {data['documents_count']}")
        print(f"      - Чанков: {data['chunks_count']}")
        print(f"      - Размер: {data['size_mb']} MB\n")
        return True
    except Exception as e:
        print(f"   ❌ FAILED: {e}\n")
        return False


def test_api_documents() -> bool:
    """Тест списка документов"""
    print("🧪 ТЕСТ 5: Список документов")
    try:
        response = requests.get(f"{API_URL}/documents", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 10  # Хотя бы 10 документов
        assert len(data["documents"]) == data["count"]
        assert any("Гражданский" in doc for doc in data["documents"])
        print(f"   ✅ PASSED: Список документов загружен ({data['count']} шт)\n")
        return True
    except Exception as e:
        print(f"   ❌ FAILED: {e}\n")
        return False


def test_api_search_basic() -> bool:
    """Тест базового поиска"""
    print("🧪 ТЕСТ 6: Базовый поиск")
    try:
        payload = {
            "query": "Что такое юридическое лицо?",
            "k": 3
        }
        response = requests.post(f"{API_URL}/search", json=payload, timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "document" in data[0]
        assert "content" in data[0]
        assert "similarity" in data[0]
        assert data[0]["similarity"] > 0.7  # Высокая схожесть
        print(f"   ✅ PASSED: Поиск работает")
        print(f"      - Найдено результатов: {len(data)}")
        print(f"      - Схожесть top-1: {data[0]['similarity']:.4f}")
        print(f"      - Документ: {data[0]['document'][:50]}...\n")
        return True
    except Exception as e:
        print(f"   ❌ FAILED: {e}\n")
        return False


def test_api_search_with_filter() -> bool:
    """Тест поиска с фильтром"""
    print("🧪 ТЕСТ 7: Поиск с фильтром по документу")
    try:
        # Используем запрос, который точно найдет в ЖК
        payload = {
            "query": "многоквартирный дом",
            "k": 2,
            "filter_document": "Жилищный"
        }
        response = requests.post(f"{API_URL}/search", json=payload, timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0, "Не найдено результатов"
        # Проверяем, что все результаты содержат "жилищ" (без учета регистра)
        for result in data:
            doc_lower = result["document"].lower()
            assert "жилищ" in doc_lower or "жк" in doc_lower, f"Неверный документ: {result['document']}"
        print(f"   ✅ PASSED: Фильтрация работает")
        print(f"      - Найдено результатов: {len(data)}")
        print(f"      - Документ: {data[0]['document'][:60]}...\n")
        return True
    except Exception as e:
        print(f"   ❌ FAILED: {e}\n")
        return False


def test_api_search_complex() -> bool:
    """Тест сложного поиска"""
    print("🧪 ТЕСТ 8: Сложный поиск по коммунальным услугам")
    try:
        payload = {
            "query": "расчет платы за коммунальные услуги",
            "k": 3
        }
        response = requests.post(f"{API_URL}/search", json=payload, timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        # Проверяем, что есть релевантные результаты
        found_relevant = any("коммунал" in result["document"].lower() or
                            "354" in result["document"] or
                            "расчет" in result["content"].lower() or
                            "плат" in result["content"].lower()
                            for result in data)
        assert found_relevant, "Не найдено релевантных результатов"
        print(f"   ✅ PASSED: Сложный поиск работает")
        print(f"      - Найдено результатов: {len(data)}")
        print(f"      - Точность top-1: {data[0]['similarity']:.4f}\n")
        return True
    except Exception as e:
        print(f"   ❌ FAILED: {e}\n")
        return False


def run_all_tests() -> Dict[str, bool]:
    """Запуск всех тестов"""
    print("\n" + "=" * 70)
    print("🚀 АВТОМАТИЧЕСКОЕ ТЕСТИРОВАНИЕ ФРОНТЕНДА И API")
    print("=" * 70)
    print(f"📍 Фронтенд: {FRONTEND_URL}")
    print(f"🔗 API: {API_URL}")
    print("=" * 70 + "\n")

    tests = [
        ("Загрузка главной страницы", test_frontend_page),
        ("API Root", test_api_root),
        ("Health Check", test_api_health),
        ("Статистика БД", test_api_stats),
        ("Список документов", test_api_documents),
        ("Базовый поиск", test_api_search_basic),
        ("Поиск с фильтром", test_api_search_with_filter),
        ("Сложный поиск", test_api_search_complex),
    ]

    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()

    # Итоги
    print("=" * 70)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    print("=" * 70)
    print(f"Всего тестов: {total}")
    print(f"Пройдено: {passed}")
    print(f"Провалено: {total - passed}")
    print(f"Успех: {passed / total * 100:.1f}%")
    print("=" * 70 + "\n")

    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!\n")
    else:
        print(f"⚠️  {total - passed} тест(ов) провалено\n")

    return results


if __name__ == "__main__":
    run_all_tests()
