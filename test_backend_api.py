#!/usr/bin/env python3
"""
Тестовый FastAPI бэкенд для единой векторной БД
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
import uvicorn

# Модель для запроса
class SearchRequest(BaseModel):
    query: str
    k: Optional[int] = 5
    filter_document: Optional[str] = None

# Модель для ответа
class SearchResult(BaseModel):
    document: str
    article: Optional[str] = ""
    chapter: Optional[str] = ""
    content: str
    similarity: float

# Обертка для модели
class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model: SentenceTransformer):
        self.model = model

    def embed_documents(self, texts):
        return self.model.encode(texts, show_progress_bar=False).tolist()

    def embed_query(self, text: str):
        return self.model.encode([text], show_progress_bar=False)[0].tolist()


# Загружаем модель и БД при старте
print("📦 Загрузка модели...")
model = SentenceTransformer("intfloat/multilingual-e5-small")
embeddings = SentenceTransformerEmbeddings(model)

print("📂 Загрузка векторной БД...")
vectordb_path = Path("/home/olga/normativ_docs/Волков/vector-db-test/vectordb/unified_all_docs_e5")
vectorstore = FAISS.load_local(str(vectordb_path), embeddings=embeddings, allow_dangerous_deserialization=True)
print("✅ БД загружена")

# Создаем FastAPI приложение
app = FastAPI(
    title="QA System API",
    description="API для вопрос-ответ системы по нормативным документам ЖКХ",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "QA System for Housing Documents",
        "version": "1.0.0",
        "model": "intfloat/multilingual-e5-small",
        "database": "unified_all_docs_e5",
        "status": "ready"
    }


@app.get("/health")
async def health():
    """Проверка здоровья"""
    return {
        "status": "healthy",
        "model_loaded": True,
        "database_loaded": True
    }


@app.post("/search", response_model=List[SearchResult])
async def search(request: SearchRequest):
    """
    Поиск релевантных фрагментов

    - **query**: Вопрос или запрос
    - **k**: Количество результатов (по умолчанию 5)
    - **filter_document**: Фильтр по названию документа (опционально)
    """
    try:
        # Если есть фильтр по документу - ищем больше результатов
        # чтобы после фильтрации осталось достаточно
        search_k = request.k * 10 if request.filter_document else request.k
        search_k = max(search_k, 50)  # Минимум 50 результатов при фильтрации

        # Выполняем поиск
        results_with_scores = vectorstore.similarity_search_with_score(request.query, k=search_k)

        response = []
        for doc, score in results_with_scores:
            # Фильтрация по документу
            if request.filter_document:
                doc_name = doc.metadata.get('document', '')
                if request.filter_document.lower() not in doc_name.lower():
                    continue

            # Конвертируем score в сходство
            similarity = 1 / (1 + score)

            response.append(SearchResult(
                document=doc.metadata.get('document', 'Неизвестно'),
                article=doc.metadata.get('article', ''),
                chapter=doc.metadata.get('chapter', ''),
                content=doc.page_content[:500],
                similarity=round(similarity, 4)
            ))

        # Возвращаем только первые k результатов
        return response[:request.k]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents():
    """Список всех документов в БД"""
    # Примерный список на основе README
    documents = [
        "Гражданский кодекс Российской Федерации (часть первая)",
        "Гражданский кодекс Российской Федерации (часть вторая)",
        "Жилищный кодекс Российской Федерации",
        "Федеральный закон от 21.12.2004 N 190-ФЗ",
        "Федеральный закон от 27.07.2006 N 152-ФЗ",
        "Федеральный закон от 23.11.2009 N 261-ФЗ",
        "Постановление Правительства РФ от 23.09.2010 N 731",
        "Постановление Правительства РФ от 06.05.2011 N 354",
        "Постановление Правительства РФ от 03.04.2013 N 315",
        "Постановление Правительства РФ от 23.09.2010 N 730",
        "Постановление Правительства РФ от 16.07.2016 N 671",
        "Приказ Минстроя РФ от 19.02.2015 N 116/пр",
        "Приказ Минстроя РФ от 04.04.2017 N 912/пр",
        "Письмо Минстроя РФ от 26.04.2017 N 12046-ОГ/04",
        "Письмо Минстроя РФ от 29.04.2015 N 11343-ОГ/04"
    ]
    return {"count": len(documents), "documents": documents}


@app.get("/stats")
async def stats():
    """Статистика БД"""
    return {
        "database_path": str(vectordb_path),
        "model": "intfloat/multilingual-e5-small",
        "embedding_dimension": 384,
        "documents_count": 18,
        "chunks_count": 2078,
        "size_mb": 11
    }


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 ЗАПУСК QA SYSTEM API")
    print("=" * 60)
    print("📍 URL: http://localhost:8001")
    print("📖 Docs: http://localhost:8001/docs")
    print("⚡ Health: http://localhost:8001/health")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8001)
