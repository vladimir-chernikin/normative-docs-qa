#!/usr/bin/env python3
"""
Обертка для embedding моделей для совместимости с LangChain FAISS
"""

import torch
from typing import List, Union, Tuple
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoTokenizer
import numpy as np


class LangChainSentenceTransformersEmbeddings(Embeddings):
    """Обертка для SentenceTransformer для работы с LangChain FAISS"""
    
    def __init__(self, model: Union[SentenceTransformer, Tuple[AutoModel, AutoTokenizer]]):
        """
        Инициализация обертки
        
        Args:
            model: Загруженная модель SentenceTransformer или кортеж (AutoModel, AutoTokenizer)
        """
        self.model = model
        # Определяем тип модели
        self.is_sentence_transformer = isinstance(model, SentenceTransformer)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Создает embeddings для списка документов
        
        Args:
            texts: Список текстов для векторизации
            
        Returns:
            Список векторов (embeddings)
        """
        if self.is_sentence_transformer:
            # Для SentenceTransformer используем стандартный метод encode
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings
        else:
            # Для моделей Transformers
            model, tokenizer = self.model
            all_embeddings = []
            
            # Обрабатываем каждый текст отдельно для экономии памяти
            for text in texts:
                inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True)
                
                # Переносим на GPU, если модель там
                if next(model.parameters()).is_cuda:
                    inputs = {k: v.cuda() for k, v in inputs.items()}
                
                # Получаем эмбеддинги
                with torch.no_grad():
                    outputs = model(**inputs)
                    # Используем среднее значение последнего скрытого слоя
                    embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()[0]
                    all_embeddings.append(embedding.tolist())
            
            return all_embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """
        Создает embedding для одного запроса
        
        Args:
            text: Текст запроса
            
        Returns:
            Вектор (embedding) для запроса
        """
        if self.is_sentence_transformer:
            embedding = self.model.encode([text], convert_to_tensor=False)
            return embedding[0].tolist()
        else:
            # Для моделей Transformers
            model, tokenizer = self.model
            inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True)
            
            # Переносим на GPU, если модель там
            if next(model.parameters()).is_cuda:
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Получаем эмбеддинги
            with torch.no_grad():
                outputs = model(**inputs)
                # Используем среднее значение последнего скрытого слоя
                embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()[0]
                return embedding.tolist() 