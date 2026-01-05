#!/bin/bash
# Скрипт установки systemd юнитов для QA System

echo "Установка systemd сервисов для QA System..."

# Создаем директорию для логов
echo "1. Создание директории для логов..."
sudo mkdir -p /var/log/qa-system
sudo chown olga:olga /var/log/qa-system

# Копируем systemd юниты
echo "2. Копирование systemd юнитов..."
sudo cp /tmp/qa-system-backend.service /etc/systemd/system/
sudo cp /tmp/qa-system-frontend.service /etc/systemd/system/

# Перезагружаем systemd
echo "3. Перезагрузка systemd..."
sudo systemctl daemon-reload

# Включаем автозапуск
echo "4. Включение автозапуска..."
sudo systemctl enable qa-system-backend.service
sudo systemctl enable qa-system-frontend.service

# Останавливаем старые процессы
echo "5. Остановка старых процессов..."
pkill -f test_backend_api.py || true
pkill -f run_frontend_server.py || true

# Запускаем новые сервисы
echo "6. Запуск новых сервисов..."
sudo systemctl start qa-system-backend.service
sudo systemctl start qa-system-frontend.service

# Проверяем статус
echo "7. Проверка статуса..."
echo ""
echo "=== Backend Service ==="
sudo systemctl status qa-system-backend.service --no-pager -l
echo ""
echo "=== Frontend Service ==="
sudo systemctl status qa-system-frontend.service --no-pager -l

echo ""
echo "Установка завершена!"
echo "Проверить логи:"
echo "  Backend: sudo journalctl -u qa-system-backend -f"
echo "  Frontend: sudo journalctl -u qa-system-frontend -f"
echo "  Или: tail -f /var/log/qa-system/backend.log"
