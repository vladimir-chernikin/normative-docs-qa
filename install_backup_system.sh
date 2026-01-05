#!/bin/bash
# Скрипт установки системы резервного копирования

echo "Установка системы резервного копирования QA System..."

# Копируем systemd юниты
echo "1. Копирование systemd юнитов для бекапа..."
sudo cp /tmp/qa-system-backup.service /etc/systemd/system/
sudo cp /tmp/qa-system-backup.timer /etc/systemd/system/

# Перезагружаем systemd
echo "2. Перезагрузка systemd..."
sudo systemctl daemon-reload

# Включаем таймер
echo "3. Включение автоматического бекапа (каждый день в 3:00)..."
sudo systemctl enable qa-system-backup.timer

# Запускаем таймер
echo "4. Запуск таймера..."
sudo systemctl start qa-system-backup.timer

# Ручной запуск первого бекапа
echo "5. Запуск первого резервного копирования..."
/home/olga/normativ_docs/Волков/backup_vector_db.sh

echo ""
echo "Установка системы бекапа завершена!"
echo ""
echo "Проверка статуса таймера:"
sudo systemctl status qa-system-backup.timer
echo ""
echo "Следующий бекап:"
sudo systemctl list-timers qa-system-backup.timer
echo ""
echo "Логи бекапа:"
echo "  tail -f /var/log/qa-system/backup.log"
echo ""
echo "Для ручного запуска бекапа:"
echo "  /home/olga/normativ_docs/Волков/backup_vector_db.sh"
