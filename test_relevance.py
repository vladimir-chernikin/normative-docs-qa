#!/usr/bin/env python3
"""
Детальное тестирование релевантности поиска по нормативным документам
"""

import json
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document

from config import VECTORDB_DIR, EMBEDDING_MODEL

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model: SentenceTransformer):
        self.model = model

    def embed_documents(self, texts):
        return self.model.encode(texts, show_progress_bar=False).tolist()

    def embed_query(self, text: str):
        return self.model.encode([text], show_progress_bar=False)[0].tolist()


def load_vector_db():
    """Загружает векторную БД"""
    db_path = VECTORDB_DIR / "unified_all_docs_e5"
    
    if not db_path.exists():
        logger.error(f"❌ БД не найдена: {db_path}")
        return None
    
    logger.info(f"📦 Загрузка модели: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = SentenceTransformerEmbeddings(model)
    
    logger.info(f"💾 Загрузка БД из {db_path}")
    vectorstore = FAISS.load_local(str(db_path), embeddings, allow_dangerous_deserialization=True)
    
    return vectorstore


def format_result(result: Document, rank: int) -> str:
    """Форматирует результат"""
    metadata = result.metadata
    doc = metadata.get('document', 'Unknown')
    article = metadata.get('article', '')
    level = metadata.get('level', 'N/A')
    
    return f"""
    {rank}. 📄 {doc}
       📜 {article}
       📊 Level: {level}
       📖 {result.page_content[:150]}...
    """


def test_relevance(vectorstore):
    """Тестирует релевантность"""
    
    test_queries = [
        ("Что такое многоквартирный дом?", "ЖК РФ Статья 15"),
        ("Какие коммунальные услуги существуют?", "ЖК РФ Статья 154"),
        ("Правила снятия показаний счетчиков", "Правила 354"),
        ("Кто платит за общедомовые нужды?", "ЖК РФ Статья 154"),
        ("Как проводится общее собрание собственников?", "ЖК РФ Статья 44-48"),
        ("Что такое капитальный ремонт?", "ЖК РФ Статья..."),
        ("Права и обязанности собственника помещения", "ЖК РФ Статья..."),
        ("Как рассчитывается плата за отопление?", "Правила 354"),
        ("Что входит в содержание общего имущества?", "Правила 491"),
        ("Как изменить размер платы за коммунальные услуги?", "Правила 354"),
        ("Что делать если нет горячей воды?", "Правила 354"),
        ("Кто управляет многоквартирным домом?", "ЖК РФ Статья 161"),
        ("Порядок начисления пени за просрочку платежа", "ГК РФ Статья 330"),
        ("Как оспорить начисления по коммунальным услугам?", "Правила 354"),
        ("Что такое лицевой счет?", "Правила 354"),
    ]
    
    results_summary = []
    
    for i, (query, expected_doc) in enumerate(test_queries, 1):
        logger.info("\n" + "=" * 100)
        logger.info(f"ТЕСТ #{i}: {query}")
        logger.info(f"Ожидается: {expected_doc}")
        logger.info("=" * 100)
        
        results = vectorstore.similarity_search(query, k=3)
        
        for j, result in enumerate(results, 1):
            logger.info(format_result(result, j))
        
        top_doc = results[0].metadata.get('document', '')
        top_article = results[0].metadata.get('article', '')
        
        relevance = "✅ РЕЛЕВАНТНО" if expected_doc.split()[0] in top_doc else "⚠️ ПРОВЕРИТЬ"
        
        logger.info(f"\n{relevance}")
        logger.info("-" * 100)
        
        results_summary.append({
            'query': query,
            'expected': expected_doc,
            'actual': f"{top_doc} {top_article}",
            'relevance': relevance
        })
    
    return results_summary


def main():
    logger.info("=" * 100)
    logger.info("ДЕТАЛЬНОЕ ТЕСТИРОВАНИЕ РЕЛЕВАНТНОСТИ")
    logger.info("=" * 100)
    
    vectorstore = load_vector_db()
    if not vectorstore:
        return
    
    results_summary = test_relevance(vectorstore)
    
    report_path = Path(__file__).parent / "reports" / "relevance_test_detailed.json"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, ensure_ascii=False, indent=2)
    
    # Статистика
    relevant = sum(1 for r in results_summary if "✅" in r['relevance'])
    total = len(results_summary)
    
    logger.info("\n" + "=" * 100)
    logger.info("СТАТИСТИКА")
    logger.info("=" * 100)
    logger.info(f"Всего тестов: {total}")
    logger.info(f"Релевантно: {relevant}")
    logger.info(f"Точность: {relevant/total*100:.1f}%")
    logger.info(f"\n✅ Отчет: {report_path}")
    logger.info("=" * 100)


if __name__ == '__main__':
    main()
