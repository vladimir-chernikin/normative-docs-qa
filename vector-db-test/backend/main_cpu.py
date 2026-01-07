#!/usr/bin/env python3
"""
Backend API сервер для работы с векторной БД нормативных документов
"""

import sys
import os
from pathlib import Path

# Добавляем корень проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import httpx
import asyncio
import json
from dotenv import load_dotenv

# Импорты для работы с векторной БД
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
# Добавляем parent для доступа к utils
sys.path.insert(0, str(project_root.parent))
from utils.embeddings import SentenceTransformerEmbeddings

# Загружаем переменные окружения из корня проекта
load_dotenv(project_root.parent / ".env")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
VECTORDB_DIR = project_root / "vectordb"
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"

# YandexGPT настройки
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "")


async def reformulate_query(original_query: str) -> tuple[str, int]:
    """
    Переформулирует запрос пользователя в термины нормативных документов ЖКХ
    используя YandexGPT для повышения точности поиска.

    Returns:
        (переформулированный_запрос, количество_токенов)
    """
    if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
        # Если нет API ключа, возвращаем оригинальный запрос
        logger.info("⚠️ Нет Yandex API ключа, используем оригинальный запрос")
        return original_query, 0

    prompt = f"""Ты - эксперт по нормативным документам ЖКХ РФ.
Переформулируй вопрос пользователя в терминах нормативных документов.

ПРАВИЛА:
1. Используй ТОЛЬКО официальную терминологию из ЖК РФ, Правил 354, Правил 491
2. ВСЕГДА приводи разговорные фразы к юридическим терминам:
   - "сменить УК" → "расторжение договора управления многоквартирным домом"
   - "как сменить управляющую компанию" → "расторжение или изменение договора управления"
   - "кто платит" → "обязанность по внесению платы, размер платы"
   - "начисления" → "расчет размера платы"
   - "платить за свет" → "коммунальная услуга по электроснабжению"
   - "мкд" → "многоквартирный дом"
   - "батареи" → "отопление"
   - "протокол собрания" → "протокол общего собрания собственников"
   - "заполняется" → "порядок оформления"
   - "что такое" → "определение, понятие"
   - "что входит" → "состав, перечень, включает в себя"
3. Сохраняй смысл вопроса
4. Используй формулировки из статей и нормативных актов
5. Добавляй синонимы и связанные понятия для улучшения поиска:
   - "общее имущество" → добавляй "помещения общего пользования, конструктивные элементы, несущие конструкции"
   - "права собственника" → добавляй "права собственности, владение, пользование, распоряжение"
   - "коммунальные платежи" → добавляй "размер платы, тарифы, нормативы, расчет"
   - "входит в состав" → добавляй "состав, перечень, включает в себя"
6. КРИТИЧЕСКИ ВАЖНО - Приоритет упомянутых документов:
   ЕСЛИ в запросе УПОМИНАЕТСЯ конкретный документ (Правила 354, ЖК РФ, ПП 491, Правила 306, ГК РФ и т.д.):
   - ДОБАВЬ в начало запроса: "найди в [полное название документа]"
   - Используй ПОЛНОЕ официальное название документа из этого списка:
     * "Правила 354" → "найди в Постановлении Правительства РФ от 06.05.2011 № 354 Правила предоставления коммунальных услуг"
     * "Правила 306" → "найди в Постановлении Правительства РФ от 23.05.2006 № 306 Правила установления нормативов потребления"
     * "Правила 491" → "найди в Постановлении Правительства РФ от 13.08.2006 № 491 Об утверждении Правил содержания общего имущества в МКД"
     * "ПП 290" → "найди в Постановлении Правительства РФ от 03.04.2013 № 290 О минимальном перечне услуг"
     * "ПП 75" → "найди в Постановлении Правительства РФ от 06.02.2006 № 75 Об открытом конкурсе"
     * "ПП 124" → "найди в Постановлении Правительства РФ от 14.02.2012 № 124 О правилах обязательных"
     * "ПП 416" → "найди в Постановлении Правительства РФ от 15.05.2013 № 416 О порядке управления МКД"
     * "ПП 1110" → "найди в Постановлении Правительства РФ от 28.10.2014 № 1110 О лицензировании"
     * "ЖК РФ" → "найди в Жилищном кодексе Российской Федерации"
     * "ГК РФ" или "Гражданский кодекс" → "найди в Гражданском кодексе Российской Федерации"
     * "ФЗ 261" → "найди в Федеральном законе от 23.11.2009 № 261-ФЗ Об энергосбережении"
     * "ФЗ 152" → "найди в Федеральном законе от 27.07.2006 № 152-ФЗ О персональных данных"
     * "ФЗ 190" → "найди в Федеральном законе от 27.07.2010 № 190-ФЗ О теплоснабжении"
     * "Приказ 938" → "найди в Приказе Минстроя РФ от 25.12.2015 № 938 пр Об утверждении Порядка"
     * "Приказ 44" → "найди в Приказе Минстроя РФ от 28.01.2019 № 44 пр Об утверждении Требований"
   - ЕСЛИ упомянутo НЕСКОЛЬКО документов: перечисли ВСЕ через "или"

7. ИСКЛЮЧАЙ разъяснения и письма: если пользователь спрашивает "как рассчитывается по Правилам 354",
   НЕ добавляй в ответ ссылки на Письма Минстроя или другие разъяснительные документы.
   ИЩИ ТОЛЬКО в основном документе, который указан в запросе.

8. Ответ ТОЛЬКО переформулированным вопросом, без объяснений

ВОПРОС ПОЛЬЗОВАТЕЛЯ: {original_query}

УЛУЧШЕННЫЙ ВОПРОС:"""

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": 100
        },
        "messages": [
            {
                "role": "user",
                "text": prompt
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            result = response.json()

            # YandexGPT возвращает result.alternatives[0].message.text
            reformulated = result["result"]["alternatives"][0]["message"]["text"].strip()

            # Убираем возможные кавычки и лишнее
            reformulated = reformulated.strip('"').strip("'").strip()

            # ИСПРАВЛЕНО (2026-01-07): Добавлено получение токенов
            tokens_used = int(result["result"]["usage"]["totalTokens"])

            logger.info(f"🔄 Переформулирование: '{original_query}' → '{reformulated}' ({tokens_used} токенов)")
            return reformulated, tokens_used

    except Exception as e:
        logger.warning(f"⚠️ Ошибка переформулирования: {e}")
        # При ошибке возвращаем оригинальный запрос и 0 токенов
        return original_query, 0


async def validate_results_with_llm(query: str, results_with_scores: list, top_k: int = 3) -> tuple[bool, str]:
    """
    Проверяет содержат ли найденные результаты КОНКРЕТНЫЙ ответ на вопрос.

    Args:
        query: Оригинальный вопрос пользователя
        results_with_scores: Список результатов векторного поиска (doc, score)
        top_k: Сколько топ результатов проверить

    Returns:
        (is_valid, reason) - где is_valid=True если есть конкретный ответ
    """
    if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
        # Если нет API ключа, считаем что валидация пройдена
        return True, "Нет API ключа для валидации"

    # Если результатов мало - проверяем все
    results_to_check = results_with_scores[:min(len(results_with_scores), top_k)]

    if len(results_to_check) == 0:
        return False, "Поиск не нашел документов"

    # Формируем фрагменты для проверки
    fragments_text = ""
    for i, (doc, score) in enumerate(results_to_check, 1):
        similarity = 1.0 / (1.0 + score)
        content_preview = doc.page_content[:800].replace('\n', ' ')
        metadata = doc.metadata
        doc_name = metadata.get('document', 'Неизвестно')
        article = metadata.get('article', '')

        fragments_text += f"\nФрагмент {i} (релевантность: {similarity:.1%}):\n"
        fragments_text += f"Документ: {doc_name}\n"
        if article:
            fragments_text += f"Статья: {article}\n"
        fragments_text += f"Текст: {content_preview}...\n"

    prompt = f"""Ты - эксперт по нормативным документам ЖКХ РФ.
Проанализируй вопрос пользователя и найденные фрагменты документов.

ВОПРОС ПОЛЬЗОВАТЕЛЯ: {query}

НАЙДЕННЫЕ ФРАГМЕНТЫ НОРМАТИВНЫХ ДОКУМЕНТОВ:{fragments_text}

ЗАДАЧА:
Определи, содержат ли эти фрагменты КОНКРЕТНЫЙ ответ на вопрос.

КРИТЕРИИ:
1. ✅ КОНКРЕТНЫЙ ОТВЕТ ЕСТЬ, если фрагмент содержит:
   - Четкое требование/обязанность/правило
   - Порядок действий/алгоритм
   - Конкретные сроки
   - Перечень документов/услуг
   - Определение понятия
   - Адресат действия (кто должен что сделать)

2. ❌ КОНКРЕТНОГО ОТВЕТА НЕТ, если фрагмент содержит:
   - Только упоминание ключевых слов без контекста
   - Косвенную информацию без конкретики
   - Другую тему (хотя бы похожие слова)
   - Общие фразы без практической пользы

ОТВЕТ:
Если конкретный ответ ЕСТЬ - напиши: "ДА: [краткое описание ответа в 1 предложение]"
Если конкретного ответа НЕТ - напиши: "НЕТ: [причина почему нет ответа в 1 предложении]"

Примеры:
- Вопрос: "Где взять справку о семье?"
  Фрагмент: "Граждане снимаются с учета в случае подачи заявления..."
  Ответ: НЕТ: фрагмент содержит процедуру снятия с учета, а не информацию о выдаче справок

- Вопрос: "Как часто проводить собрания?"
  Фрагмент: "Общие собрания проводятся не реже одного раза в год..."
  Ответ: ДА: установлена периодичность проведения общих собраний

Твой ответ:"""

    try:
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "Content-Type": "application/json"
        }

        body = {
            "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.1,  # Низкая температура для детерминированности
                "maxTokens": 50
            },
            "messages": [
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            result = response.json()

        llm_answer = result["result"]["alternatives"][0]["message"]["text"].strip()
        logger.info(f"🤖 Валидация LLM: {llm_answer}")

        # Парсим ответ
        if llm_answer.startswith("ДА:"):
            return True, llm_answer[4:].strip()
        elif llm_answer.startswith("НЕТ:"):
            return False, llm_answer[5:].strip()
        else:
            # Если ответ не по формату, считаем что ответ есть
            logger.warning(f"⚠️ Неожиданный формат ответа LLM: {llm_answer}")
            return True, "Не удалось определить"

    except Exception as e:
        logger.warning(f"⚠️ Ошибка валидации: {e}")
        # При ошибке считаем что валидация пройдена
        return True, f"Ошибка валидации: {e}"


async def rerank_results_with_llm(query: str, results_with_scores: list) -> list:
    """
    Реранжирует результаты через YandexGPT для определения лучшего ответа.

    Args:
        query: Оригинальный запрос пользователя
        results_with_scores: Список кортежей (doc, score)

    Returns:
        Отсортированный список (doc, score) по релевантности
    """
    if not results_with_scores:
        return results_with_scores

    # Если всего 1 результат - нечего реранжировать
    if len(results_with_scores) == 1:
        return results_with_scores

    # Формируем промпт для LLM
    results_text = ""
    for i, (doc, score) in enumerate(results_with_scores, 1):
        similarity = 1 / (1 + score)
        doc_name = doc.metadata.get('document', 'Unknown')
        article = doc.metadata.get('article', '')
        content_preview = doc.page_content[:300].replace('\n', ' ')

        results_text += f"\n{i}. Документ: {doc_name}\n"
        results_text += f"   Статья: {article}\n"
        results_text += f"   Сходство: {similarity:.2%}\n"
        results_text += f"   Текст: {content_preview}...\n"

    prompt = f"""Ты - эксперт по нормативным документам РФ.
Проанализируй, какой из предложенных фрагментов ЛУЧШЕ ВСЕГО отвечает на вопрос пользователя.

ВОПРОС ПОЛЬЗОВАТЕЛЯ:
{query}

НАЙДЕННЫЕ ФРАГМЕНТЫ:
{results_text}

КРИТЕРИИ ОЦЕНКИ:
1. Прямой ответ на вопрос (определение, перечень, порядок)
2. Полнота ответа (чем полнее, тем лучше)
3. Релевантность (не отвечает на соседний вопрос)
4. Официальный источник (статья закона лучше чем письмо)

УКАЖИ НОМЕР ЛУЧШЕГО ФРАГМЕНТА (цифрой от 1 до {len(results_with_scores)}):
"""

    try:
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "Content-Type": "application/json"
        }

        body = {
            "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 50
            },
            "messages": [
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            result = response.json()

            llm_answer = result["result"]["alternatives"][0]["message"]["text"].strip()

            logger.info(f"📝 Ответ YandexGPT: {llm_answer}")

            # Извлекаем номер из ответа LLM
            import re
            match = re.search(r'\b([1-9]|1[0-9]|20)\b', llm_answer)

            if match:
                best_idx = int(match.group(1)) - 1  # Конвертируем в 0-based index
                best_idx = max(0, min(best_idx, len(results_with_scores) - 1))

                # Перемещаем лучший результат на первое место с высокой оценкой
                best_doc, best_score = results_with_scores.pop(best_idx)
                # Даем высокую оценку 0.99 результату выбранному LLM
                results_with_scores.insert(0, (best_doc, 0.99))

                logger.info(f"🎯 LLM реранжинг: выбран результат #{best_idx + 1} как наиболее релевантный (ошибка обновлена: {best_score:.3f} -> 0.99)")
            else:
                logger.warning(f"⚠️ LLM не вернул корректный номер: '{llm_answer}'")

    except Exception as e:
        logger.warning(f"⚠️ Ошибка LLM реранжинга: {e}")

    return results_with_scores


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class SearchResult(BaseModel):
    document: str
    article: str
    content: str
    metadata: Dict[str, Any]
    similarity: float  # Добавлено поле схожести


class SearchResponse(BaseModel):
    results: List[SearchResult]
    reformulated_query: str  # Уточненный запрос от YandexGPT
    original_query: str  # Оригинальный запрос пользователя
    tokens_used: int = 0  # ИСПРАВЛЕНО (2026-01-07): Добавлено поле токенов


class SimplifyRequest(BaseModel):
    """Запрос на упрощение текста"""
    text: str
    max_length: Optional[int] = 300


class SimplifyResult(BaseModel):
    """Результат упрощения текста"""
    original_text: str
    simplified_text: str
    tokens_used: int


# Создаем приложение FastAPI
app = FastAPI(
    title="Normative Documents QA API",
    description="API для поиска по нормативным документам ЖКХ",
    version="1.0.0",
    default_response_class=JSONResponse
)


class NumpyEncoder(json.JSONEncoder):
    """Кастомный encoder для numpy типов"""
    def default(self, obj):
        if hasattr(obj, 'item'):
            return obj.item()
        elif hasattr(obj, 'tolist'):
            return obj.tolist()
        return super().default(obj)


# Кастомный response handler
async def custom_response(request, response):
    """Конвертирует numpy типы в JSON"""
    response.media_type = "application/json"
    response.body = json.dumps(
        response.body,
        cls=NumpyEncoder,
        ensure_ascii=False
    ).encode('utf-8')
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные переменные
vectorstores: List[FAISS] = []  # Список всех 18 векторных баз
document_names: List[str] = []  # Список названий документов
model: Optional[SentenceTransformer] = None


@app.on_event("startup")
async def startup_event():
    """Загрузка всех векторных БД при старте"""
    global vectorstores, document_names, model

    logger.info("🚀 Запуск Backend API сервера...")

    if not VECTORDB_DIR.exists():
        logger.error(f"❌ Директория не найдена: {VECTORDB_DIR}")
        raise RuntimeError(f"Vector DB dir not found: {VECTORDB_DIR}")

    try:
        logger.info(f"📦 Загрузка модели: {EMBEDDING_MODEL}")
        model = SentenceTransformer(EMBEDDING_MODEL)
        embeddings = SentenceTransformerEmbeddings(model)

        # Загружаем все 18 отдельных баз
        db_dirs = sorted([d for d in VECTORDB_DIR.iterdir()
                         if d.is_dir()
                         and not d.name.startswith('.')
                         and not d.name.startswith('unified')])  # Пропускаем unified

        logger.info(f"📁 Найдено {len(db_dirs)} векторных БД")

        total_vectors = 0
        for i, db_dir in enumerate(db_dirs, 1):
            try:
                logger.info(f"[{i}/{len(db_dirs)}] Загрузка: {db_dir.name}")
                vs = FAISS.load_local(str(db_dir), embeddings, allow_dangerous_deserialization=True)
                vectorstores.append(vs)
                # Сохраняем название документа (замена _ на пробел для читаемости)
                doc_name = db_dir.name.replace('_', ' ')
                document_names.append(doc_name)
                count = vs.index.ntotal
                total_vectors += count
                logger.info(f"  ├─ Векторов: {count}")
            except Exception as e:
                logger.warning(f"  ⚠️ Ошибка загрузки {db_dir.name}: {e}")

        logger.info(f"✅ Загружено {len(vectorstores)} БД, всего {total_vectors} векторов")
        logger.info("✅ Backend API сервер готов к работе!")
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        raise


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "Normative Documents QA API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья"""
    return {
        "status": "healthy" if len(vectorstores) > 0 else "uninitialized",
        "model": EMBEDDING_MODEL,
        "vectordb": str(VECTORDB_DIR),
        "databases_loaded": len(vectorstores)
    }


@app.get("/stats")
async def get_stats():
    """Получить статистику векторной БД"""
    if len(vectorstores) == 0:
        raise HTTPException(status_code=503, detail="Vector database not loaded")

    try:
        # Подсчитываем общее количество векторов во всех базах
        total_chunks = sum(vs.index.ntotal for vs in vectorstores)

        # Получаем уникальные документы из метаданных
        # Для этого нужно загрузить все документы или хранить список отдельно
        # Простой способ - попробуем получить из сохраненных данных
        documents = set()
        # Берем пример из метаданных (если есть доступ)
        # В реальном случае лучше хранить список документов при создании БД

        return {
            "documents_count": 18,  # Известно из создания БД
            "chunks_count": total_chunks,
            "model": EMBEDDING_MODEL
        }
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")


@app.get("/documents")
async def get_documents():
    """Получить список всех документов в БД"""
    if len(vectorstores) == 0:
        raise HTTPException(status_code=503, detail="Vector database not loaded")

    try:
        # Возвращаем реальные названия загруженных документов
        return {"documents": document_names}
    except Exception as e:
        logger.error(f"❌ Ошибка получения документов: {e}")
        raise HTTPException(status_code=500, detail=f"Documents error: {str(e)}")


@app.post("/search", response_model=List[SearchResult])
async def search_documents(request: QueryRequest):
    """
    Поиск по всем нормативным документам (18 баз)

    Args:
        request: Запрос с текстом и количеством результатов

    Returns:
        Список найденных документов
    """
    if len(vectorstores) == 0:
        raise HTTPException(status_code=503, detail="Vector databases not loaded")

    try:
        import time
        total_start = time.time()

        # Шаг 1: Переформулируем запрос через YandexGPT для повышения точности
        reformulate_start = time.time()
        # ИСПРАВЛЕНО (2026-01-07): Получаем токены от reformulate_query
        reformulated_query, reformulate_tokens = await reformulate_query(request.query)
        reformulate_time = time.time() - reformulate_start
        logger.info(f"⏱️ Переформулирование: {reformulate_time:.2f} сек")

        # Шаг 2: Выполняем поиск по всем 18 базам с реальными скорами
        all_results = []
        per_db_k = 5  # Берем топ-5 из каждой базы (оптимизация производительности)

        logger.info(f"🔍 Поиск по {len(vectorstores)} базам (k={per_db_k} из каждой)")

        for i, vs in enumerate(vectorstores):
            try:
                # Используем similarity_search_with_score с обработкой ошибок
                docs_with_scores = vs.similarity_search_with_score(reformulated_query, k=per_db_k)
                for doc, score in docs_with_scores:
                    all_results.append((doc, float(score)))
            except KeyError as e:
                # Пропускаем базы с ошибками индекса
                logger.warning(f"⚠️ Ошибка индекса в базе {i}: {e}")
                continue
            except Exception as e:
                logger.warning(f"⚠️ Ошибка поиска в базе {i}: {e}")
                continue

        logger.info(f"✅ Всего найдено: {len(all_results)} кандидатов")
        search_time = time.time() - total_start
        logger.info(f"⏱️ Поиск по базам: {search_time:.2f} сек")

        # Шаг 3: Первичная сортировка по score
        all_results.sort(key=lambda x: x[1])

        # Шаг 3.5: Дедупликация результатов
        dedup_start = time.time()
        seen_contents = {}
        unique_results = []
        duplicates_count = 0

        for doc, score in all_results:
            # Создаем ключ для дедупликации по содержимому документа
            # Используем больше символов для точности (первые 500)
            content_key = doc.page_content[:500] if len(doc.page_content) > 500 else doc.page_content
            if content_key not in seen_contents:
                seen_contents[content_key] = True
                unique_results.append((doc, score))
            else:
                duplicates_count += 1

        dedup_time = time.time() - dedup_start
        if duplicates_count > 0:
            logger.info(f"🗑️ Убрано дубликатов: {duplicates_count} (за {dedup_time:.3f} сек)")
        else:
            logger.info(f"✅ Дубликатов нет (за {dedup_time:.3f} сек)")

        # Берем топ-20 для реранжинга
        candidates_for_rerank = unique_results[:min(len(unique_results), 20)]

        # Шаг 4: Реранжинг через YandexGPT - ОТКЛЮЧЕНО (плохая работа)
        # Результаты векторного поиска точнее чем LLM-реранжинга
        # logger.info(f"🔄 Реранжинг {len(candidates_for_rerank)} кандидатов через YandexGPT...")
        # results_with_scores = await rerank_results_with_llm(request.query, candidates_for_rerank)

        # Шаг 4.5: Группировка по (document, article) - показывать все части одной статьи
        # Если найдено несколько чанков из одной статьи, показать все
        grouped_by_article = {}
        for doc, score in candidates_for_rerank:
            metadata = doc.metadata
            document = metadata.get('document', 'Unknown')
            article = metadata.get('article', '')

            # Ключ группировки
            key = (document, article)

            if key not in grouped_by_article:
                grouped_by_article[key] = []
            grouped_by_article[key].append((doc, score))

        # Разворачиваем группы: берем все чанки из найденных статей
        results_with_scores = []
        for key, chunks in grouped_by_article.items():
            # Сортируем чанки внутри статьи по score
            chunks.sort(key=lambda x: x[1])
            # Добавляем все чанки статьи
            results_with_scores.extend(chunks)

        # Логируем группировку
        articles_found = len(grouped_by_article)
        total_chunks = len(results_with_scores)
        logger.info(f"📊 Найдено статей: {articles_found}, чанков: {total_chunks}")

        # Ограничиваем top_k (но теперь это может быть больше чанков из-за группировки)
        if len(results_with_scores) > request.top_k:
            results_with_scores = results_with_scores[:request.top_k]

        # Валидация LLM ОТКЛЮЧЕНА - возвращает все результаты векторного поиска
        # Причина: LLM слишком строгий и блокирует правильные ответы

        # Форматируем результаты
        formatted_results = []
        for doc, score in results_with_scores:
            try:
                metadata = doc.metadata
                # Конвертируем numpy типы
                clean_metadata = {}
                for key, value in metadata.items():
                    if hasattr(value, 'item'):
                        clean_metadata[key] = value.item()
                    elif isinstance(value, (int, float, str, bool, list, dict, type(None))):
                        clean_metadata[key] = value
                    else:
                        clean_metadata[key] = str(value)

                # Косинусное сходство из L2 расстояния FAISS
                # Для нормализованных векторов: cosine = 1 - (distance^2) / 2
                cosine_similarity = 1 - (float(score) ** 2) / 2
                # Ограничиваем диапазон [0, 1]
                similarity = max(0.0, min(1.0, cosine_similarity))
                formatted_results.append(SearchResult(
                    document=str(clean_metadata.get('document', 'Unknown')),
                    article=str(clean_metadata.get('article', '')),
                    content=str(doc.page_content),
                    metadata=clean_metadata,
                    similarity=round(similarity, 4)
                ))
            except Exception as e:
                logger.error(f"Ошибка форматирования: {e}")
                continue

        logger.info(f"🔍 Поиск: '{request.query[:50]}...' -> {len(formatted_results)} результатов")

        # Создаем ответ с переформулированным запросом и токенами
        # ИСПРАВЛЕНО (2026-01-07): Добавлены токены в ответ
        response = SearchResponse(
            results=formatted_results,
            reformulated_query=reformulated_query,
            original_query=request.query,
            tokens_used=reformulate_tokens
        )

        # Замеряем общее время
        total_time = time.time() - total_start
        logger.info(f"⏱️ ОБЩЕЕ ВРЕМЯ: {total_time:.2f} сек (переформулирование: {reformulate_time:.2f}s, поиск: {search_time:.2f}s, дедупликация: {dedup_time:.3f}s)")

        # Возвращаем JSON
        return JSONResponse(
            content=response.model_dump()
        )

    except Exception as e:
        import traceback
        logger.error(f"❌ Ошибка поиска: {e}")
        logger.error(f"TRACEBACK:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

async def simplify_text_with_llm(text: str, max_length: int = 300) -> tuple[str, int]:
    """
    Упрощает канцелярский текст нормативных документов на простой язык

    Args:
        text: Исходный текст для упрощения
        max_length: Максимальное количество токенов для генерации (по умолчанию 300)

    Returns:
        (упрощенный_текст, количество_токенов)
    """
    if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
        logger.warning("⚠️ Нет Yandex API ключа, возвращаем оригинальный текст")
        return text, 0

    # ИСПРАВЛЕНО (2026-01-07): Увеличен лимит до 3000 символов для лучшего понимания контекста
    text_for_prompt = text[:3000] if len(text) > 3000 else text

    # ИСПРАВЛЕНО (2026-01-07): Промпт с СУПЕР КРИТИЧЕСКИМ акцентом на ВСЕ даты
    prompt = f"""Ты - эксперт по объяснению юридических текстов простым языком.

⚠️⚠️⚠️ СВЕРХКРИТИЧЕСКИ ВАЖНО: СОХРАНИТЬ ВСЕ ДАТЫ, ГОДЫ, СРОКИ ⚠️⚠️⚠️

ПРАВИЛА (выполняются ТОЧНО):
1. ВСЕ даты и сроки ДОЛЖНЫ остаться в ответе:
   - Все года: 2021, 2022, 2023, 2024, 2025, 2026, 2027, etc.
   - Все месяцы и дни
   - Все часы: "24 часа", "48 часов"
   - Все проценты: "7 процентов", "14 процентов", "20 процентов"
   - Все суммы: "3000 ₽", "10 копеек"

2. ЕСЛИ В ТЕКСТЕ ЕСТЬ ШТРАФНЫЕ САНКЦИИ (даты 2025-2027) - ОБЯЗАТЕЛЬНО включи их в раздел **Сроки**!

3. Указывай КТО за что отвечает

4. Структура ответа:
   **Главное:** [суть в 1-2 предложениях]
   **Сроки:** [перечисли ВСЕ даты, сроки, проценты]
   **Ответственность:** [кто за что отвечает]
   **Плюс:** [важные детали]

5. Используй простые слова

ПРИМЕР ПРАВИЛЬНОГО ОТВЕТА:
**Главное:** гарантирующий поставщик обязан установить приборы учета
**Сроки:**
- не позднее 6 месяцев
- до 31 декабря 2023 г.
- до 31 декабря 2021 г.
- штрафы: с 1 января 2025 г. - 7%, с 1 января 2026 г. - 14%, с 1 января 2027 г. - 20%
**Ответственность:** гарантирующий поставщик

Текст для упрощения:
{text_for_prompt}

Упрощенный текст:"""

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # ИСПРАВЛЕНО (2026-01-07): Понижена температура до 0.3 для более стабильных ответов
    body = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": max_length
        },
        "messages": [
            {
                "role": "user",
                "text": prompt
            }
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            result = response.json()

            # ИСПРАВЛЕНО (2026-01-07): Правильная структура ответа Yandex API
            # Было: result["choices"][0]["message"]["text"] (старая структура OpenAI)
            # Стало: result["result"]["alternatives"][0]["message"]["text"]
            simplified_text = result["result"]["alternatives"][0]["message"]["text"].strip()
            tokens_used = int(result["result"]["usage"].get("totalTokens", 0))

            logger.info(f"✅ Текст упрощен: {len(text)} -> {len(simplified_text)} символов, токенов: {tokens_used}")
            return simplified_text, tokens_used

    except Exception as e:
        logger.error(f"❌ Ошибка упрощения текста: {e}")
        return text, 0



@app.post("/simplify", response_model=SimplifyResult)
async def simplify_text(request: SimplifyRequest):
    """
    Упрощает канцелярский текст нормативных документов на простой язык
    
    Args:
        request: Запрос с текстом для упрощения
        
    Returns:
        Упрощенный текст с информацией о использованных токенах
    """
    try:
        simplified_text, tokens_used = await simplify_text_with_llm(
            request.text, 
            request.max_length
        )
        
        return SimplifyResult(
            original_text=request.text[:200] + "..." if len(request.text) > 200 else request.text,
            simplified_text=simplified_text,
            tokens_used=tokens_used
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка endpoint simplify: {e}")
        raise HTTPException(status_code=500, detail=f"Simplification error: {str(e)}")




def main():
    """Главная функция для запуска сервера"""
    import uvicorn
    
    logger.info("=" * 80)
    logger.info("ЗАПУСК BACKEND API СЕРВЕРА")
    logger.info("=" * 80)
    logger.info(f"📍 API endpoint: http://0.0.0.0:8001")
    logger.info(f"📚 Документация: http://0.0.0.0:8001/docs")
    logger.info("=" * 80)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )


if __name__ == "__main__":
    main()
