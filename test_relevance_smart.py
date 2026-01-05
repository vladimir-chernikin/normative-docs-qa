#!/usr/bin/env python3
"""
Умное тестирование релевантности с анализом соответствия
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


def check_relevance_smart(query, result, expected_keywords):
    """
    Умная проверка релевантности
    
    Returns:
        (is_relevant, confidence, reason)
    """
    metadata = result.metadata
    doc = metadata.get('document', '')
    article = metadata.get('article', '')
    content = result.page_content.lower()
    
    # Проверяем ключевые слова
    content_matches = 0
    for keyword in expected_keywords:
        if keyword.lower() in content or keyword.lower() in doc.lower() or keyword.lower() in article.lower():
            content_matches += 1
    
    # Проверяем документ
    doc_lower = doc.lower()
    
    # Определяем тип документа по запросу
    if any(kw in query.lower() for kw in ['жк', 'жилищный', 'многоквартирный']):
        expected_doc_type = 'жилищный кодекс'
    elif any(kw in query.lower() for kw in ['гк', 'гражданский', 'юридическое лицо']):
        expected_doc_type = 'гражданский кодекс'
    elif any(kw in query.lower() for kw in ['правила 354', 'коммунальные услуги', 'счетчик', 'горячая вода']):
        expected_doc_type = 'правил № 354'
    elif any(kw in query.lower() for kw in ['правила 491', 'содержание общего имущества']):
        expected_doc_type = 'правил № 491'
    else:
        expected_doc_type = None
    
    # Проверяем соответствие документа
    doc_match = False
    if expected_doc_type:
        doc_match = expected_doc_type in doc_lower
    
    # Вычисляем уверенность
    confidence = 0.0
    reasons = []
    
    if content_matches >= len(expected_keywords):
        confidence += 0.5
        reasons.append(f"Все ключевые слова найдены ({content_matches}/{len(expected_keywords)})")
    elif content_matches > 0:
        confidence += 0.3 * (content_matches / len(expected_keywords))
        reasons.append(f"Найдено {content_matches}/{len(expected_keywords)} ключевых слов")
    
    if doc_match:
        confidence += 0.5
        reasons.append(f"Документ соответствует: {expected_doc_type}")
    elif expected_doc_type and expected_doc_type not in doc_lower:
        # Проверяем по названию документа
        if 'жилищный' in query.lower() and 'жилищный' in doc_lower:
            confidence += 0.3
            reasons.append("Документ ЖК РФ (по названию)")
        elif 'гражданский' in query.lower() and 'гражданский' in doc_lower:
            confidence += 0.3
            reasons.append("Документ ГК РФ (по названию)")
        elif 'правил' in query.lower() and '№ 354' in query.lower() and '354' in doc:
            confidence += 0.5
            reasons.append("Документ Правила 354")
        elif 'правил' in query.lower() and '№ 491' in query.lower() and '491' in doc:
            confidence += 0.5
            reasons.append("Документ Правила 491")
    
    # Итоговая оценка
    is_relevant = confidence >= 0.6
    
    return is_relevant, confidence, reasons


def test_relevance_smart(vectorstore):
    """Умное тестирование релевантности"""
    
    test_cases = [
        {
            "query": "Что такое многоквартирный дом?",
            "keywords": ["многоквартирный дом", "здание", "квартир"],
            "expected_doc": "ЖК РФ"
        },
        {
            "query": "Какие коммунальные услуги существуют?",
            "keywords": ["коммунальные услуги", "вода", "газ", "электрическая", "отопление"],
            "expected_doc": "ЖК РФ"
        },
        {
            "query": "Правила снятия показаний счетчиков",
            "keywords": ["счетчик", "показани", "прибор учет"],
            "expected_doc": "Правила 354"
        },
        {
            "query": "Кто платит за общедомовые нужды?",
            "keywords": ["общедомовые нужды", "плата", "собственник"],
            "expected_doc": "Правила 354"
        },
        {
            "query": "Как проводится общее собрание собственников?",
            "keywords": ["общее собрание", "собственник", "голосование"],
            "expected_doc": "ЖК РФ"
        },
        {
            "query": "Что такое капитальный ремонт?",
            "keywords": ["капитальный ремонт", "общее имущество"],
            "expected_doc": "ЖК РФ"
        },
        {
            "query": "Права и обязанности собственника помещения",
            "keywords": ["собственник", "права", "обязанност", "помещение"],
            "expected_doc": "ЖК РФ или ГК РФ"
        },
        {
            "query": "Как рассчитывается плата за отопление?",
            "keywords": ["отопл", "расчет", "плата", "коммунальная услуга"],
            "expected_doc": "Правила 354"
        },
        {
            "query": "Что входит в содержание общего имущества?",
            "keywords": ["общее имущество", "содержание", "многоквартирный дом"],
            "expected_doc": "Правила 491"
        },
        {
            "query": "Как изменить размер платы за коммунальные услуги?",
            "keywords": ["размер платы", "коммунальные услуги", "изменен"],
            "expected_doc": "Правила 354 или ЖК РФ"
        },
        {
            "query": "Что делать если нет горячей воды?",
            "keywords": ["горячая вода", "коммунальная услуга", "не предоставлена"],
            "expected_doc": "Правила 354"
        },
        {
            "query": "Кто управляет многоквартирным домом?",
            "keywords": ["управлен", "многоквартирный дом", "управляющая организац"],
            "expected_doc": "ЖК РФ"
        },
        {
            "query": "Порядок начисления пени за просрочку платежа",
            "keywords": ["пен", "просрочк", "платеж", "неустойка"],
            "expected_doc": "ГК РФ или ЖК РФ"
        },
        {
            "query": "Как оспорить начисления по коммунальным услугам?",
            "keywords": ["оспорить", "начислен", "коммунальные услуги", "претенз"],
            "expected_doc": "Правила 354"
        },
        {
            "query": "Что такое лицевой счет?",
            "keywords": ["лицевой счет", "платеж", "счет"],
            "expected_doc": "Правила 354 или ЖК РФ"
        },
    ]
    
    results_summary = []
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        keywords = test_case["keywords"]
        expected_doc = test_case["expected_doc"]
        
        logger.info("\n" + "=" * 100)
        logger.info(f"ТЕСТ #{i}: {query}")
        logger.info(f"Ожидается: {expected_doc}")
        logger.info(f"Ключевые слова: {', '.join(keywords)}")
        logger.info("=" * 100)
        
        results = vectorstore.similarity_search(query, k=3)
        
        # Показываем все результаты
        for j, result in enumerate(results, 1):
            metadata = result.metadata
            doc = metadata.get('document', 'Unknown')
            article = metadata.get('article', '')
            logger.info(f"\n{j}. 📄 {doc}")
            logger.info(f"   📜 {article}")
            logger.info(f"   📖 {result.page_content[:120]}...")
        
        # Анализируем топ-1 результат
        top_result = results[0]
        is_relevant, confidence, reasons = check_relevance_smart(query, top_result, keywords)
        
        if is_relevant:
            relevance_mark = "✅ РЕЛЕВАНТНО"
        elif confidence >= 0.4:
            relevance_mark = "⚠️ ЧАСТИЧНО РЕЛЕВАНТНО"
        else:
            relevance_mark = "❌ НЕ РЕЛЕВАНТНО"
        
        logger.info(f"\n{relevance_mark} (уверенность: {confidence:.2f})")
        logger.info(f"Причины: {', '.join(reasons)}")
        logger.info("-" * 100)
        
        results_summary.append({
            'test_num': i,
            'query': query,
            'expected_doc': expected_doc,
            'actual_doc': f"{results[0].metadata.get('document', '')} {results[0].metadata.get('article', '')}",
            'is_relevant': is_relevant,
            'confidence': round(confidence, 2),
            'reasons': reasons,
            'relevance_mark': relevance_mark
        })
    
    return results_summary


def main():
    logger.info("=" * 100)
    logger.info("УМНОЕ ТЕСТИРОВАНИЕ РЕЛЕВАНТНОСТИ")
    logger.info("=" * 100)
    
    vectorstore = load_vector_db()
    if not vectorstore:
        return
    
    results_summary = test_relevance_smart(vectorstore)
    
    # Сохраняем отчет
    report_path = Path(__file__).parent / "reports" / "relevance_test_smart.json"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, ensure_ascii=False, indent=2)
    
    # Статистика
    total = len(results_summary)
    relevant = sum(1 for r in results_summary if r['is_relevant'])
    partial = sum(1 for r in results_summary if not r['is_relevant'] and r['confidence'] >= 0.4)
    not_relevant = total - relevant - partial
    
    avg_confidence = sum(r['confidence'] for r in results_summary) / total
    
    logger.info("\n" + "=" * 100)
    logger.info("СТАТИСТИКА")
    logger.info("=" * 100)
    logger.info(f"Всего тестов: {total}")
    logger.info(f"✅ Полностью релевантно: {relevant} ({relevant/total*100:.1f}%)")
    logger.info(f"⚠️ Частично релевантно: {partial} ({partial/total*100:.1f}%)")
    logger.info(f"❌ Не релевантно: {not_relevant} ({not_relevant/total*100:.1f}%)")
    logger.info(f"\n📊 Средняя уверенность: {avg_confidence:.2f}")
    logger.info(f"✅ Отчет сохранен: {report_path}")
    logger.info("=" * 100)


if __name__ == '__main__':
    main()
