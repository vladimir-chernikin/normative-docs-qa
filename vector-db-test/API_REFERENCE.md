# API Reference - Q&A Система по нормативным документам

## Базовый URL
```
http://localhost:8008
```

---

## 🔐 АВТОРИЗАЦИЯ

### Регистрация
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "first_name": "Иван",
  "last_name": "Иванов",
  "phone": "+79991234567"
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Регистрация успешна",
  "user_id": "uuid-user-id"
}
```

---

### Вход
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Авторизация успешна",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "uuid-user-id",
    "email": "user@example.com",
    "first_name": "Иван",
    "balance": 0.0
  }
}
```

**Использование токена:**
```
Authorization: Bearer <token>
```

---

### Выход
```http
POST /api/auth/logout
Authorization: Bearer <token>
```

---

## 💰 БАЛАНС И ПЛАТЕЖИ

### Получить баланс
```http
GET /api/user/balance
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "success": true,
  "message": "Баланс получен",
  "balance": 500.0,
  "formatted": "500.00 ₽"
}
```

---

### Пополнить баланс (ТЕСТОВЫЙ РЕЖИМ)
```http
POST /api/user/balance/add
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 500.0,
  "payment_method": "sbp_qr"
}
```

**Доступные методы оплаты:**
- `card_mir` - Банковская карта МИР
- `card_tinkoff` - Т-Банк
- `card_sber` - СберБанк
- `sbp_qr` - СБП по QR коду
- `sbp_phone` - СБП по номеру телефона
- `sber_pay` - SberPay
- `t_pay` - T-Pay
- `yoomoney` - ЮMoney
- `apple_pay` - Apple Pay
- `google_pay` - Google Pay
- `yandex_pay` - Yandex Pay

**Ответ:**
```json
{
  "success": true,
  "message": "Платеж создан (тестовый режим)",
  "payment_intent": {
    "id": "uuid-intent",
    "amount": 500.0,
    "payment_method": "sbp_qr",
    "status": "completed",
    "description": "Пополнение баланса на 500.00 ₽"
  },
  "new_balance": 500.0,
  "test_mode": true
}
```

---

### Методы оплаты
```http
GET /api/user/payment-methods
```

**Ответ:**
```json
{
  "success": true,
  "methods": [
    {
      "id": "sbp_qr",
      "name": "СБП по QR коду",
      "description": "Сканируйте QR код камерой телефона",
      "icon": "📱",
      "min_amount": 10.0,
      "max_amount": 100000.0,
      "commission": 0.0,
      "processing_time": "мгновенно",
      "is_test_mode": false
    },
    ...
  ],
  "test_mode": true,
  "test_message": "ТЕСТОВЫЙ РЕЖИМ: Реальные деньги не списываются"
}
```

---

### История транзакций
```http
GET /api/user/transactions?limit=50&offset=0
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "success": true,
  "transactions": [
    {
      "id": "uuid-trans",
      "user_id": "uuid-user",
      "amount": 500.0,
      "transaction_type": "deposit",
      "status": "completed",
      "payment_method": "sbp_qr",
      "description": "Пополнение баланса (СБП по QR коду)",
      "created_at": "2025-01-01T12:00:00",
      "completed_at": "2025-01-01T12:00:01"
    },
    {
      "id": "uuid-trans2",
      "user_id": "uuid-user",
      "amount": 10.50,
      "transaction_type": "payment",
      "status": "completed",
      "description": "Запрос: ПРОСТАЯ СПРАВКА (Какой срок давности...)",
      "created_at": "2025-01-01T12:05:00",
      "completed_at": "2025-01-01T12:05:02"
    }
  ],
  "total": 2
}
```

---

### Статистика пользователя
```http
GET /api/user/stats
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "success": true,
  "stats": {
    "balance": 489.50,
    "total_requests": 15,
    "free_requests": 12,
    "paid_requests": 3,
    "total_spent": 10.50,
    "total_deposits": 500.0,
    "daily_limits": {
      "simple_reference_used": 8,
      "term_explanation_used": 4
    }
  }
}
```

---

## 🤗 КЛАССИФИКАЦИЯ ВОПРОСОВ И СТОИМОСТЬ

### Справка по типам вопросов
```http
GET /api/llm/cost/guide
```

**Ответ:** (см. полный пример в PAYMENT_METHODS.md)

---

### Предпросмотр стоимости
```http
POST /api/llm/cost/preview
Content-Type: application/json

{
  "query": "Какой срок давности по коммунальным долгам?",
  "model": "yandexgpt"
}
```

**Ответ (БЕСПЛАТНЫЙ):**
```json
{
  "query": "Какой срок давности по коммунальным долгам?",
  "question_type": "simple_reference",
  "question_type_name": "ПРОСТАЯ СПРАВКА",
  "question_complexity": "low",
  "confidence": 0.7,
  "is_free": true,
  "free_daily_limit": 10,
  "free_daily_remaining": 8,
  "requires_payment": false,
  "estimated_tokens": {
    "input_tokens_avg": 750,
    "output_tokens_avg": 300,
    "total_tokens_avg": 1050
  },
  "cost_range": "0.00 ₽ (бесплатно)",
  "recommendations": [
    "🆓 БЕСПЛАТНО! Осталось 8 бесплатных запросов сегодня",
    "✅ Это простой вопрос - будет быстро"
  ]
}
```

**Ответ (ПЛАТНЫЙ):**
```json
{
  "query": "Проанализируй порядок оспаривания начислений",
  "question_type": "legal_analysis",
  "question_type_name": "СЛОЖНЫЙ ЮРИДИЧЕСКИЙ АНАЛИЗ",
  "question_complexity": "high",
  "confidence": 0.7,
  "is_free": false,
  "free_daily_limit": 0,
  "requires_payment": true,
  "estimated_tokens": {
    "input_tokens_avg": 6000,
    "output_tokens_avg": 2500,
    "total_tokens_avg": 8500
  },
  "cost_range": "7.56 - 12.42 ₽",
  "recommendations": [
    "💰 Этот тип запроса ПЛАТНЫЙ",
    "💡 Для получения бесплатных ответов задавайте более простые вопросы"
  ]
}
```

---

## 🔧 ЛОГИКА ПРОВЕРКИ ПЕРЕД ЗАПРОСОМ

### Шаг 1: Классификация вопроса
```python
# Определяем тип вопроса
type_id, type_info, confidence = classifier.classify(query)
```

### Шаг 2: Проверка бесплатности
```python
if is_free:
    # Проверяем лимит
    can_use, message, remaining = check_free_limit(user_id, type_id)
    if can_use:
        # БЕСПЛАТНЫЙ запрос
        use_free_request(user_id, type_id)
        execute_llm_request()
    else:
        # Лимит исчерпан
        return "Лимит бесплатных запросов исчерпан"
else:
    # Платный запрос
    cost = estimate_cost(type_id)
    
    # Проверяем баланс
    if user.balance >= cost:
        # Списываем
        charge(user_id, cost)
        execute_llm_request()
    else:
        # Недостаточно средств
        return f"Недостаточно средств. Баланс: {user.balance}₽, требуется: {cost}₽"
```

---

## 📞 ПОДДЕРЖКА

**Email:** support@normativ-docs.ru  
**Телефон:** 8-800-XXX-XX-XX  
**Документация:** [PAYMENT_METHODS.md](./PAYMENT_METHODS.md)
