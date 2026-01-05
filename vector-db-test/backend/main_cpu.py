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
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import httpx
import asyncio
from dotenv import load_dotenv

# Импорты для работы с векторной БД
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document

# Загружаем переменные окружения
load_dotenv(project_root / ".env")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
VECTORDB_DIR = project_root / "vectordb/unified_all_docs_e5"
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"

# YandexGPT настройки
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "")


async def reformulate_query(original_query: str) -> str:
    """
    Переформулирует запрос пользователя в термины нормативных документов ЖКХ
    используя YandexGPT для повышения точности поиска.
    """
    if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
        # Если нет API ключа, возвращаем оригинальный запрос
        logger.info("⚠️ Нет Yandex API ключа, используем оригинальный запрос")
        return original_query

    prompt = f"""Ты - эксперт по нормативным документам ЖКХ РФ.
Переформулируй вопрос пользователя в терминах нормативных документов.

ПРАВИЛА:
1. Используй официальную терминологию из ЖК РФ, Правил 354, Правил 491
2. Заменяй разговорные слова на юридические:
   - "начисления" → "расчет размера платы"
   - "платить за свет" → "коммунальная услуга по электроснабжению"
   - "мкд" → "многоквартирный дом"
   - "батареи" → "отопление"
   - "протокол собрания" → "протокол общего собрания собственников"
   - "заполняется" → "порядок оформления"
3. Сохраняй смысл вопроса
4. Используй формулировки из статей и нормативных актов
5. Ответ ТОЛЬКО переформулированным вопросом, без объяснений

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

            logger.info(f"🔄 Переформулирование: '{original_query}' → '{reformulated}'")
            return reformulated

    except Exception as e:
        logger.warning(f"⚠️ Ошибка переформулирования: {e}")
        # При ошибке возвращаем оригинальный запрос
        return original_query


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

            # Извлекаем номер из ответа LLM
            import re
            match = re.search(r'\b([1-9]|1[0-9])\b', llm_answer)

            if match:
                best_idx = int(match.group(1)) - 1  # Конвертируем в 0-based index
                best_idx = max(0, min(best_idx, len(results_with_scores) - 1))

                # Перемещаем лучший результат на первое место
                best_result = results_with_scores.pop(best_idx)
                results_with_scores.insert(0, best_result)

                logger.info(f"🎯 LLM реранжинг: выбран результат #{best_idx + 1} как наиболее релевантный")
            else:
                logger.warning(f"⚠️ LLM не вернул корректный номер: '{llm_answer}'")

    except Exception as e:
        logger.warning(f"⚠️ Ошибка LLM реранжинга: {e}")

    return results_with_scores


class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model: SentenceTransformer):
        self.model = model

    def embed_documents(self, texts):
        return self.model.encode(texts, show_progress_bar=False).tolist()

    def embed_query(self, text: str):
        return self.model.encode([text], show_progress_bar=False)[0].tolist()


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class SearchResult(BaseModel):
    document: str
    article: str
    content: str
    metadata: Dict[str, Any]
    similarity: float  # Добавлено поле схожести


# Создаем приложение FastAPI
app = FastAPI(
    title="Normative Documents QA API",
    description="API для поиска по нормативным документам ЖКХ",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные переменные
vectorstore: Optional[FAISS] = None
model: Optional[SentenceTransformer] = None


@app.on_event("startup")
async def startup_event():
    """Загрузка векторной БД при старте"""
    global vectorstore, model
    
    logger.info("🚀 Запуск Backend API сервера...")
    
    if not VECTORDB_DIR.exists():
        logger.error(f"❌ Векторная БД не найдена: {VECTORDB_DIR}")
        raise RuntimeError(f"Vector DB not found: {VECTORDB_DIR}")
    
    try:
        logger.info(f"📦 Загрузка модели: {EMBEDDING_MODEL}")
        model = SentenceTransformer(EMBEDDING_MODEL)
        embeddings = SentenceTransformerEmbeddings(model)
        
        logger.info(f"💾 Загрузка БД из {VECTORDB_DIR}")
        vectorstore = FAISS.load_local(str(VECTORDB_DIR), embeddings, allow_dangerous_deserialization=True)
        
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
        "status": "healthy" if vectorstore else "uninitialized",
        "model": EMBEDDING_MODEL,
        "vectordb": str(VECTORDB_DIR)
    }


@app.get("/stats")
async def get_stats():
    """Получить статистику векторной БД"""
    if not vectorstore:
        raise HTTPException(status_code=503, detail="Vector database not loaded")

    try:
        # Получаем индекс FAISS
        index = vectorstore.index

        # Количество векторов = количество чанков
        chunks_count = index.ntotal

        # Получаем уникальные документы из метаданных
        # Для этого нужно загрузить все документы или хранить список отдельно
        # Простой способ - попробуем получить из сохраненных данных
        documents = set()
        # Берем пример из метаданных (если есть доступ)
        # В реальном случае лучше хранить список документов при создании БД

        return {
            "documents_count": 18,  # Известно из создания БД
            "chunks_count": chunks_count,
            "model": EMBEDDING_MODEL
        }
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")


@app.get("/documents")
async def get_documents():
    """Получить список всех документов в БД"""
    if not vectorstore:
        raise HTTPException(status_code=503, detail="Vector database not loaded")

    try:
        # Список документов на основе создания БД
        documents = [
            "Жилищный кодекс Российской Федерации",
            "Гражданский кодекс Российской Федерации (часть первая)",
            "Гражданский кодекс Российской Федерации (часть вторая)",
            "ПП РФ от 06.05.2011 № 354",
            "ПП РФ от 13.08.2006 № 491",
            "ПП РФ от 23.09.2010 № 731",
            "ПП РФ от 16.04.2013 № 344",
            "ПП РФ от 05.05.2011 № 355",
            "ПП РФ от 14.02.2012 № 128",
            "ПП РФ от 15.05.2013 № 416",
            "ПП РФ от 06.02.2011 № 56",
            "ПП РФ от 04.05.2012 № 439",
            "ПП РФ от 13.08.2006 № 491",
            "ПП РФ от 27.08.2016 № 857",
            "Постановление Правительства РФ от 26.09.2014 № 976",
            "Федеральный закон от 27.07.2010 № 190-ФЗ",
            "Федеральный закон от 21.12.2013 № 361-ФЗ",
            "Федеральный закон от 31.12.2017 № 506-ФЗ"
        ]

        return {"documents": documents}
    except Exception as e:
        logger.error(f"❌ Ошибка получения документов: {e}")
        raise HTTPException(status_code=500, detail=f"Documents error: {str(e)}")


@app.post("/search", response_model=List[SearchResult])
async def search_documents(request: QueryRequest):
    """
    Поиск по нормативным документам

    Args:
        request: Запрос с текстом и количеством результатов

    Returns:
        Список найденных документов
    """
    if not vectorstore:
        raise HTTPException(status_code=503, detail="Vector database not loaded")

    try:
        # Шаг 1: Переформулируем запрос через YandexGPT для повышения точности
        reformulated_query = await reformulate_query(request.query)

        # Шаг 2: Выполняем поиск среди большего числа кандидатов (увеличенный k)
        # Это позволяет найти правильный ответ даже если он на 2-3 месте
        search_k = max(request.top_k * 2, 10)  # Минимум 10 кандидатов
        results_with_scores = vectorstore.similarity_search_with_score(reformulated_query, k=search_k)

        # Шаг 3: Реранжинг результатов через YandexGPT для лучшего ответа
        # Это ПЕРВИЧНЫЙ реранжинг - выбирает лучший ответ среди кандидатов
        results_with_scores = await rerank_results_with_llm(request.query, results_with_scores)

        # Форматируем результаты
        formatted_results = []
        for doc, score in results_with_scores[:request.top_k]:  # Возвращаем только запрошенное количество
            metadata = doc.metadata
            # Конвертируем score в similarity (0-1, где 1 = максимально похожий)
            similarity = 1 / (1 + score)
            formatted_results.append(SearchResult(
                document=metadata.get('document', 'Unknown'),
                article=metadata.get('article', ''),
                content=doc.page_content,  # Полный текст без обрезания
                metadata=metadata,
                similarity=round(similarity, 4)  # Округляем до 4 знаков
            ))

        logger.info(f"🔍 Поиск: '{request.query[:50]}...' -> найдено: {len(formatted_results)} (просмотрено кандидатов: {len(results_with_scores)})")

        return formatted_results

    except Exception as e:
        logger.error(f"❌ Ошибка поиска: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


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
