#!/bin/bash
# Скрипт установки Nginx конфигурации для QA System с SSL

echo "=============================================="
echo "Установка Nginx для QA System Frontend"
echo "=============================================="

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "Пожалуйста, запустите скрипт с sudo:"
    echo "sudo ./install_nginx_ssl.sh"
    exit 1
fi

# 1. Установка конфигурации Nginx
echo ""
echo "1. Установка конфигурации Nginx..."
cp /tmp/qa-system-frontend.conf /etc/nginx/sites-available/qa-system-frontend
ln -sf /etc/nginx/sites-available/qa-system-frontend /etc/nginx/sites-enabled/qa-system-frontend

# 2. Проверка конфигурации Nginx
echo ""
echo "2. Проверка конфигурации Nginx..."
nginx -t
if [ $? -ne 0 ]; then
    echo "ОШИБКА: Конфигурация Nginx некорректна!"
    exit 1
fi

# 3. Перезагрузка Nginx
echo ""
echo "3. Перезагрузка Nginx..."
systemctl reload nginx

# 4. Проверка наличия certbot
echo ""
echo "4. Проверка наличия certbot..."
if ! command -v certbot &> /dev/null; then
    echo "Установка certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
fi

# 5. Получение SSL сертификата
echo ""
echo "5. Получение SSL сертификата для qa.komunal-dom.ru..."
echo "ВНИМАНИЕ: Для получения сертификата домен qa.komunal-dom.ru должен указывать на этот сервер!"
echo ""
read -p "Продолжить? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    certbot --nginx -d qa.komunal-dom.ru --non-interactive --agree-tos --email admin@komunal-dom.ru --redirect

    if [ $? -eq 0 ]; then
        echo "✅ SSL сертификат установлен успешно!"
    else
        echo "⚠️  Не удалось получить SSL сертификат автоматически"
        echo "Возможно домен qa.komunal-dom.ru еще не настроен или не указывает на этот сервер"
        echo ""
        echo "Варианты решения:"
        echo "1. Добавьте DNS запись A для qa.komunal-dom.ru -> 155.212.217.73"
        echo "2. Или временно отключите SSL в конфиге (закомментируйте редирект на HTTPS)"
    fi
else
    echo "Пропуск установки SSL сертификата"
    echo "Вам нужно будет установить SSL вручную позже:"
    echo "  sudo certbot --nginx -d qa.komunal-dom.ru"
fi

# 6. Финальная проверка
echo ""
echo "6. Финальная проверка конфигурации..."
nginx -t

echo ""
echo "=============================================="
echo "Установка завершена!"
echo "=============================================="
echo ""
echo "QA System Frontend доступен по адресам:"
echo "  HTTP:  http://qa.komunal-dom.ru"
echo "  HTTPS: https://qa.komunal-dom.ru"
echo ""
echo "Проверить статус Nginx:"
echo "  sudo systemctl status nginx"
echo ""
echo "Просмотр логов:"
echo "  tail -f /var/log/nginx/qa-frontend-access.log"
echo "  tail -f /var/log/nginx/qa-frontend-error.log"
echo ""
echo "=============================================="
