#!/bin/bash
# Скрипт установки Nginx для QA System (вариант с портом 8080)
# БЕЗ отдельного поддомена и SSL

echo "=============================================="
echo "Установка Nginx для QA System (порт 8080)"
echo "=============================================="

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "Пожалуйста, запустите скрипт с sudo:"
    echo "sudo ./install_nginx_port.sh"
    exit 1
fi

# 1. Установка конфигурации Nginx
echo ""
echo "1. Установка конфигурации Nginx..."
cp /tmp/qa-system-frontend-port.conf /etc/nginx/sites-available/qa-system-frontend
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

# 4. Проверка что frontend работает
echo ""
echo "4. Проверка что frontend сервер работает..."
if ! lsof -i :8080 > /dev/null 2>&1; then
    echo "⚠️  ВНИМАНИЕ: Frontend сервер не запущен на порту 8080!"
    echo "Запустите его:"
    echo "  cd /home/olga/normativ_docs/Волков"
    echo "  python3 run_frontend_server.py"
    echo ""
    echo "Или используйте systemd сервис (если установлен):"
    echo "  sudo systemctl start qa-system-frontend"
fi

echo ""
echo "=============================================="
echo "Установка завершена!"
echo "=============================================="
echo ""
echo "QA System Frontend доступен по адресам:"
echo "  http://komunal-dom.ru:8080"
echo "  http://www.komunal-dom.ru:8080"
echo "  http://155.212.217.73:8080"
echo ""
echo "Преимущества Nginx:"
echo "  ✓ Gzip сжатие (в 3-5 раз меньше трафик)"
echo "  ✓ Кеширование статики в браузере"
echo "  ✓ Быстрая отдача файлов"
echo "  ✓ Защита от медленных клиентов"
echo ""
echo "Проверить статус Nginx:"
echo "  sudo systemctl status nginx"
echo ""
echo "Просмотр логов:"
echo "  tail -f /var/log/nginx/qa-frontend-access.log"
echo "  tail -f /var/log/nginx/qa-frontend-error.log"
echo ""
echo "Тестировать скорость:"
echo "  curl -I http://komunal-dom.ru:8080"
echo "=============================================="
