#!/bin/bash

# Остановка процессов на портах
echo "Останавливаем процессы на портах 8008 и 8090..."
lsof -ti:8008 | xargs kill -9 2>/dev/null || true
lsof -ti:8090 | xargs kill -9 2>/dev/null || true

# Установка переменной окружения для JSON-файла
export GOOGLE_APPLICATION_CREDENTIALS="/home/sawa/GitHub/stazh_aspect/vector-db-test/august-bond-467911-t8-43c2bfbc4bc4.json"
echo "Установлена переменная окружения GOOGLE_APPLICATION_CREDENTIALS: $GOOGLE_APPLICATION_CREDENTIALS"

# Запуск backend сервера
echo "Запускаем backend сервер..."
cd /home/sawa/GitHub/stazh_aspect/vector-db-test
source $(conda info --base)/etc/profile.d/conda.sh
conda activate stzh311cpu
python run_backend_cpu.py --env dev --skip-check &
BACKEND_PID=$!

# Ожидание запуска backend
echo "Ожидаем запуск backend сервера..."
sleep 5

# Запуск frontend сервера
echo "Запускаем frontend сервер..."
python run_frontend.py --mode cpu --env dev &
FRONTEND_PID=$!

echo "Серверы запущены. Backend PID: $BACKEND_PID, Frontend PID: $FRONTEND_PID"
echo "Для остановки серверов нажмите Ctrl+C"

# Ожидание завершения
wait $BACKEND_PID $FRONTEND_PID