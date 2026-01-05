# Установка Nginx для QA System - Пошаговая инструкция

## Что делаем:

Настраиваем Nginx для QA System на поддомене `qa.komunal-dom.ru` с SSL.
**ВАЖНО:** Основной проект komunal-dom.ru НЕ трогаем!

---

## ШАГ 1: Установка конфига Nginx (без пароля не получится)

Откройте терминал и выполните:

```bash
cd /home/olga/normativ_docs/Волков
sudo ./install_nginx_ssl.sh
```

Скрипт сделает:
1. Скопирует конфиг в `/etc/nginx/sites-available/qa-system-frontend`
2. Создаст символьную ссылку в `/etc/nginx/sites-enabled/`
3. Проверит конфиг: `nginx -t`
4. Перезагрузит Nginx

**Остановитесь на шаге с certbot** (получение SSL) - нам сначала нужна DNS запись!

---

## ШАГ 2: Добавить DNS запись

Вам нужно добавить **одну DNS запись** там где куплен домен `komunal-dom.ru`:

### Панель регистратора/хостера:

| Тип | Имя | Значение | TTL |
|-----|-----|----------|-----|
| A | qa | 155.212.217.73 | 3600 |

### Примеры в разных панелях:

**reg.ru / nic.ru:**
```
Тип: A
Поддомен: qa
IP адрес: 155.212.217.73
```

**cloudflare:**
```
Type: A
Name: qa
IPv4: 155.212.217.73
Proxy: off (DNS only)
```

**Yandex Cloud / Selectel:**
```
Тип записи: A
Имя: qa
Значение: 155.212.217.73
```

### Проверка DNS (через 5-15 минут после добавления):

```bash
# Проверить что DNS запись работает
ping qa.komunal-dom.ru
# Должен ответить 155.212.217.73

# Или через dig
dig qa.komunal-dom.ru
# Должен показать A 155.212.217.73
```

---

## ШАГ 3: Получить SSL сертификат

Когда DNS запись начнет работать, выполните:

```bash
sudo certbot --nginx -d qa.komunal-dom.ru
```

Certbot спросит:
1. Email для уведомлений (введите ваш email)
2. Согласие с условиями (наберите `A` или `Y`)
3. Редирект HTTP → HTTPS (выберите `2` - Redirect)

После успешной установки certbot покажет:
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/qa.komunal-dom.ru/fullchain.pem
```

---

## ШАГ 4: Проверка

```bash
# 1. Проверить что Nginx работает
sudo systemctl status nginx

# 2. Проверить конфиг
sudo nginx -t

# 3. Проверить логи
tail -f /var/log/nginx/qa-frontend-access.log

# 4. Тест в браузере
# https://qa.komunal-dom.ru
```

---

## Что делать если что-то пошло не так:

### Проблема: DNS запись не работает

**Проверьте:**
```bash
ping qa.komunal-dom.ru
# Если "unknown host" - DNS запись еще не применилась (подождите 5-15 мин)
# Если отвечает другой IP - проверьте DNS запись
```

### Проблема: Certbot не может получить сертификат

**Ошибка:** "Failed to connect to host"

**Решение:** DNS запись еще не работает или указывает на другой IP

### Проблема: 502 Bad Gateway

**Причина:** Frontend сервер не запущен на порту 8080

**Решение:**
```bash
cd /home/olga/normativ_docs/Волков
python3 run_frontend_server.py
```

---

## Готово! После установки:

QA System будет доступен по адресу:
- **HTTPS:** https://qa.komunal-dom.ru
- **HTTP:** http://qa.komunal-dom.ru (авторедирект на HTTPS)

Основной проект продолжит работать:
- **http://komunal-dom.ru** (без изменений)

---

## Следующие шаги:

После установки можно:
1. Настроить мониторинг Nginx
2. Добавить алерты при падении
3. Настроить logrotate для логов

Но это **опционально**. Сейчас система готова к production!
