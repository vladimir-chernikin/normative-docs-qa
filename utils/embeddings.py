#!/usr/bin/env python3
"""
Утилиты для работы с эмбеддингами
Общие классы и функции для использования во всех скриптах
"""

from typing import List
from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings


class SentenceTransformerEmbeddings(Embeddings):
    """
    Обертка для SentenceTransformer с совместимостью LangChain

    Используется для создания эмбеддингов текстов с помощью моделей
    из библиотеки sentence-transformers с интеграцией в LangChain
    """

    def __init__(self, model: SentenceTransformer):
        """
        Инициализация обертки

        Args:
            model: Экземпляр модели SentenceTransformer
        """
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Создать эмбеддинги для списка документов

        Args:
            texts: Список текстов для эмбеддинга

        Returns:
            Список векторов (эмбеддингов)
        """
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """
        Создать эмбеддинг для одного запроса

        Args:
            text: Текст запроса

        Returns:
            Вектор (эмбеддинг) запроса
        """
        embedding = self.model.encode([text], show_progress_bar=False)[0]
        return embedding.tolist()
