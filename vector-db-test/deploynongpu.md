/home/userui/Markin/pdf conversion/clean_texts
Какие принципы лежат в основе гражданского законодательства Российской Федерации?
    1. Почему начисляют плату за коммунальные услуги, если в квартире никто не живёт? 
    2. Почему я должен платить за лифт если я им не пользуюсь? 
    3. Что входит в обязаности управляющей компании?


sudo systemctl restart xray
sudo systemctl status xray

#!/bin/bash
# setup_env.sh - Скрипт для создания окружения stzh311

# Создать окружение conda с Python 3.11
conda create -n stzh311_new python=3.11 -y

# Активировать окружение
conda activate stzh311_new

# Установить PyTorch с поддержкой CUDA
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121

# Установить основные библиотеки
pip install numpy==1.24.3
pip install scikit-learn==1.3.2
pip install faiss-gpu==1.11.0
pip install transformers==4.53.2 huggingface-hub==0.34.1 tokenizers==0.21.2
pip install sentence-transformers==5.0.0
pip install fastapi==0.104.1 uvicorn==0.24.0 pydantic==2.4.2
pip install langsmith==0.0.92
pip install langchain==0.0.325
# pip install langchain==0.0.325 langchain-core==0.1.53 langchain-community==0.0.38 langchain-text-splitters==0.0.1
pip install python-dotenv==1.0.0 psutil==5.9.6 tiktoken==0.5.1 tqdm==4.67.1 python-multipart==0.0.6
pip install openai==1.98.0
pip install mistralai==0.4.2
pip install google-generativeai==0.8.5
pip install google-cloud-aiplatform==1.106.0

pip install langchain-community==0.0.38
pip install langchain-text-splitters==0.0.1



# Инструкция по развертыванию системы векторного поиска на машине без GPU
(base) userdisk@mos99ws995u:~/Загрузки$ sudo sshfs -o allow_other,IdentityFile=~/.ssh/id_rsa sawa@sawa6195355.mooo.com:/home/sawa /mnt/sawa6195355
The authenticity of host 'sawa6195355.mooo.com (188.255.55.146)' can't be established.
ED25519 key fingerprint is SHA256:V4D7gA8svAVbjUgCZXdRKA+rXS5M1nmmpKu//YyFuY0.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
sawa@sawa6195355.mooo.com's password: 

chromium-browser --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile

ПРАВИЛЬНЫЕ КОМАНДЫ ОСТАНОВКИ СЕРВЕРОВ
Для API сервера на порту 8008:
Для веб сервера на порту 8090:
lsof -ti:8008 | xargs kill -9 2>/dev/null || true
lsof -ti:8090 | xargs kill -9 2>/dev/null || true
## Обзор задачи
source /home/userui/stzh311cpu/bin/activate
ssh userui@85.198.80.170


папка проекта:
vector-db-test
conda create --name stzh_cpu python=3.11
python3.11 -m venv ~/stzh311cpu
cd Volkov/vector-db-test

pip install -r backend/requirements_gpu.txt (для GPU)
pip install -r backend/requirements_cpu.txt (для CPU)

export GOOGLE_APPLICATION_CREDENTIALS="august-bond-467911-t8-43c2bfbc4bc4.json"
nohup python run_backend_cpu.py > backend.log 2>&1 &
nohup python run_frontend.py --mode cpu > frontend.log 2>&1 &

**Для GPU:**
cd vector-db-test
conda activate stzh311
python run_backend_gpu.py

cd vector-db-test
conda activate stzh311
python run_frontend.py --mode gpu


**Для CPU:**
cd Volkov/vector-db-test
cd vector-db-test
conda activate stzh311cpu
python run_backend_cpu.py --env dev
 
cd vector-db-test
conda activate stzh311cpu
python run_frontend.py --mode cpu --env dev

http://85.198.80.170:8090

   * Для локальной разработки:
       * python run_backend_gpu.py (или _cpu)
       * python run_frontend.py --mode local



Терминал 1: Запуск Бэкенда
Терминал 2: Запуск Фронтенда



conda activate stzh311
cd /home/sawa/GitHub/stazh_aspect/vector-db-test/
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8008


conda activate stzh311
cd /home/sawa/GitHub/stazh_aspect/vector-db-test/frontend
python -m http.server 8090 --bind 0.0.0.0



cd vector-db-test
conda activate stzh311
python scripts/vectorize_documents.py


cd vector-db-test
conda activate stzh311
python scripts/vectorize_frida.py




Развертывание готовой системы векторного поиска с titan18ubuntu (GPU-машина) на aspektubuntu (CPU-машина) для тестирования запросов по готовым векторным базам.

**Источник:** titan18ubuntu (машина с GPU RTX 4090, где проводилась векторизация)  
**Цель:** aspektubuntu (userui@85.198.80.170, машина без GPU для тестирования поиска)

## ⚠️ ВАЖНЫЕ ИСПРАВЛЕНИЯ

**Найдены и исправлены следующие проблемы конфигурации:**
1. ✅ **Порт 8000 → 8008** в `backend/main.py` 
2. ✅ **Старый GPU-сервер** `sawa6195355.mooo.com` заменен на локальный `127.0.0.1`
3. ✅ **Автоопределение хоста** во Frontend отключено
4. ✅ **Централизованная конфигурация** добавлена в `config/config.json`

См. подробности в файле `CONFIGURATION_SUMMARY.md`

**Архитектура развертывания:**
- **Backend API:** запущен на aspektubuntu:8008 (внутренний доступ)
- **Frontend веб-сервер:** запущен на aspektubuntu:8090 (доступен из интернета)
- **Использование:** с любого компьютера открыть браузер → http://85.198.80.170:8090

**✅ Преимущества такого подхода:**
- **Простота использования:** один URL для доступа ко всей системе
- **Нет настроек на клиентских машинах:** только браузер
- **Централизованное управление:** все компоненты на одном сервере
- **Безопасность:** Backend API недоступен извне, только Frontend

---

## Шаг 1: Подготовка проекта на titan18ubuntu (источник)

### 1.1 Создание архива проекта

```bash
# На titan18ubuntu
cd /home/sawa/GitHub/stazh_aspect

# Создаем архив основного проекта (без .git и кэшей)
tar -czf vector-db-project.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.log' \
    --exclude='.pytest_cache' \
    --exclude='*.tmp' \
    vector-db-test/

# Проверяем размер архива
ls -lh vector-db-project.tar.gz
```

### 1.2 Создание архива локальных моделей

**Расположение локальных моделей на titan18ubuntu:**
```bash
# Основной кэш HuggingFace (все модели)
~/.cache/huggingface/hub/

# Конкретные модели проекта:
~/.cache/huggingface/hub/models--cointegrated--rubert-tiny2/
~/.cache/huggingface/hub/models--intfloat--multilingual-e5-small/
~/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/
~/.cache/huggingface/hub/models--sentence-transformers--LaBSE/
~/.cache/huggingface/hub/models--ai-forever--FRIDA/
```

```bash
# Создаем архив локальных моделей (только нужные для проекта)
cd ~/.cache/huggingface/hub

tar -czf ~/models-cache.tar.gz \
    models--cointegrated--rubert-tiny2 \
    models--intfloat--multilingual-e5-small \
    models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2 \
    models--sentence-transformers--LaBSE \
    models--ai-forever--FRIDA

# Проверяем размер архива моделей
ls -lh ~/models-cache.tar.gz
```

---

## Шаг 2: Копирование файлов на aspektubuntu

### 2.1 Копирование основного проекта

```bash
# С titan18ubuntu копируем проект на aspektubuntu
scp vector-db-project.tar.gz userui@85.198.80.170:~/
```

### 2.2 Копирование локальных моделей

```bash
# С titan18ubuntu копируем модели на aspektubuntu
scp ~/models-cache.tar.gz userui@85.198.80.170:~/
```

---

## Шаг 3: Настройка aspektubuntu (целевая машина)

### 3.1 Подключение к aspektubuntu

```bash
ssh userui@85.198.80.170
```

### 3.2 Подготовка системы

```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Python 3 и pip (если не установлены)
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Устанавливаем системные зависимости для научных библиотек
sudo apt install -y build-essential libopenblas-dev liblapack-dev gfortran

# Проверяем версию Python (должна быть >= 3.8)
python3 --version
```

### 3.3 Распаковка проекта

```bash
# Распаковываем основной проект
cd ~/
tar -xzf vector-db-project.tar.gz

# Переходим в директорию проекта
cd vector-db-test

# Создаем виртуальное окружение для изоляции зависимостей
python3 -m venv venv

# Активируем виртуальное окружение
source venv/bin/activate

# Обновляем pip в виртуальном окружении
pip install --upgrade pip
```

### 3.4 Установка зависимостей (CPU-версия)

```bash
# Активируем виртуальное окружение (если не активно)
source venv/bin/activate

# Устанавливаем CPU-версию PyTorch (легче и быстрее на CPU)
pip install torch==2.1.0+cpu torchvision==0.16.0+cpu -f https://download.pytorch.org/whl/torch_stable.html

# Устанавливаем основные зависимости проекта
cd backend
pip install -r requirements.txt

# Проверяем успешность установки ключевых библиотек
python3 -c "import torch; import faiss; import sentence_transformers; print('✅ Все основные библиотеки установлены')"
```

---

## Шаг 4: Настройка локальных моделей

### 4.1 Распаковка моделей в правильное место

```bash
# Создаем директорию кэша HuggingFace (если не существует)
mkdir -p ~/.cache/huggingface/hub

# Распаковываем модели в кэш
cd ~/.cache/huggingface/hub
tar -xzf ~/models-cache.tar.gz

# Проверяем, что модели распакованы корректно
ls -la | grep models--

# Ожидаемые директории:
# models--cointegrated--rubert-tiny2
# models--intfloat--multilingual-e5-small  
# models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2
# models--sentence-transformers--LaBSE
# models--ai-forever--FRIDA
```

### 4.2 Проверка доступности моделей

```bash
# Возвращаемся в проект
cd ~/vector-db-test

# Активируем виртуальное окружение
source venv/bin/activate

# Тестируем загрузку каждой модели
python3 -c "
from sentence_transformers import SentenceTransformer
print('Проверяем модели...')

models = [
    'cointegrated/rubert-tiny2',
    'intfloat/multilingual-e5-small', 
    'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
    'sentence-transformers/LaBSE'
]

for model_name in models:
    try:
        model = SentenceTransformer(model_name, device='cpu')
        print(f'✅ {model_name} - загружена успешно')
        del model
    except Exception as e:
        print(f'❌ {model_name} - ошибка: {e}')
"
```

---

## Шаг 5: Конфигурация для CPU и удаленного доступа

### 5.1 Обновление Backend конфигурации

```bash
cd ~/vector-db-test

# Активируем виртуальное окружение
source venv/bin/activate
```

**Создаем файл `backend/config_cpu.py`:**

```python
# backend/config_cpu.py
"""
Конфигурация для CPU-машины без GPU
"""

import torch

# Принудительное использование CPU
DEVICE = "cpu"
torch.set_num_threads(4)  # Ограничиваем количество потоков для стабильности

# Настройки для удаленного доступа
BACKEND_HOST = "0.0.0.0"  # Принимаем подключения от любых IP
BACKEND_PORT = 8008

# Отключаем GPU мониторинг
GPU_MONITORING_ENABLED = False

# Батч-размер для CPU (меньше чем для GPU)
BATCH_SIZE = 16

# Таймаут для загрузки моделей (больше на CPU)
MODEL_LOAD_TIMEOUT = 300  # 5 минут

print(f"✅ Конфигурация CPU: устройство={DEVICE}, хост={BACKEND_HOST}:{BACKEND_PORT}")
```

### 5.2 Модификация run_server.py для CPU

Создаем `backend/run_server_cpu.py`:

```python
#!/usr/bin/env python3
"""
Скрипт запуска Backend API сервера для CPU-машины
"""

import os
import sys
import uvicorn
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Импортируем CPU конфигурацию
from backend.config_cpu import BACKEND_HOST, BACKEND_PORT, DEVICE

def main():
    print(f"🚀 Запуск Backend API для CPU-машины...")
    print(f"📍 Устройство: {DEVICE}")
    print(f"🌐 Хост: {BACKEND_HOST}:{BACKEND_PORT}")
    print(f"🔗 API будет доступен по адресу: http://85.198.80.170:{BACKEND_PORT}")
    
    # Устанавливаем переменные окружения для CPU
    os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Отключаем GPU
    os.environ["OMP_NUM_THREADS"] = "4"
    
    # Запускаем сервер
    uvicorn.run(
        "backend.main:app",
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        reload=False,  # Отключаем автоперезагрузку на продакшене
        workers=1,     # Один воркер для стабильности на CPU
        log_level="info"
    )

if __name__ == "__main__":
    main()
```

### 5.3 Создание скрипта быстрого запуска

Создаем `start_cpu_server.sh`:

```bash
#!/bin/bash
# Скрипт запуска системы на CPU-машине

echo "🔧 Подготовка к запуску системы векторного поиска на CPU..."

# Переходим в директорию проекта
cd ~/vector-db-test

# Активируем виртуальное окружение
source venv/bin/activate

# Проверяем доступность порта 8008
if lsof -ti:8008 > /dev/null 2>&1; then
    echo "⚠️  Порт 8008 занят. Останавливаем предыдущий процесс..."
    lsof -ti:8008 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Устанавливаем переменные окружения для CPU
export CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=4
export PYTHONPATH="${PWD}:$PYTHONPATH"

echo "🚀 Запуск Backend API сервера..."
echo "🌐 API будет доступен по адресу: http://85.198.80.170:8008"
echo "📊 Для проверки здоровья: http://85.198.80.170:8008/health"
echo "📚 Документация API: http://85.198.80.170:8008/docs"

# Запускаем сервер в фоновом режиме
nohup python3 backend/run_server_cpu.py > server.log 2>&1 &

# Сохраняем PID для последующей остановки
echo $! > server.pid

echo "✅ Сервер запущен в фоновом режиме (PID: $(cat server.pid))"
echo "📝 Логи сервера: ~/vector-db-test/server.log"
echo "🛑 Для остановки: ./stop_server.sh"

# Ждем несколько секунд и проверяем статус
sleep 5
if kill -0 $(cat server.pid) 2>/dev/null; then
    echo "✅ Сервер работает стабильно"
    
    # Пытаемся сделать тестовый запрос
    echo "🧪 Выполняем тестовый запрос..."
    curl -s http://localhost:8008/health && echo "" || echo "⚠️  Сервер еще не готов к приему запросов"
else
    echo "❌ Ошибка запуска сервера. Проверьте логи: tail server.log"
fi
```

Создаем `stop_server.sh`:

```bash
#!/bin/bash
# Скрипт остановки сервера

echo "🛑 Остановка Backend API сервера..."

cd ~/vector-db-test

if [ -f server.pid ]; then
    PID=$(cat server.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Сервер остановлен (PID: $PID)"
    else
        echo "⚠️  Процесс с PID $PID уже не существует"
    fi
    rm server.pid
else
    echo "⚠️  Файл server.pid не найден, ищем процесс по порту..."
    lsof -ti:8008 | xargs kill -9 2>/dev/null || true
fi

echo "🔍 Проверяем статус порта 8008..."
if lsof -ti:8008 > /dev/null 2>&1; then
    echo "⚠️  Порт 8008 все еще занят"
else
    echo "✅ Порт 8008 свободен"
fi
```

---

## Шаг 6: Настройка сетевого доступа

### 6.1 Настройка firewall (если включен)

```bash
# Проверяем статус firewall
sudo ufw status

# Если активен, открываем порт 8090 для Frontend (внешний доступ)
sudo ufw allow 8090/tcp

# Порт 8008 для Backend оставляем только для локального доступа (не открываем)
# sudo ufw allow 8008/tcp  # НЕ НУЖНО - Backend только для внутреннего использования

sudo ufw reload

# Проверяем, что правило добавлено
sudo ufw status numbered
```

### 6.2 Проверка сетевой доступности

```bash
# Проверяем Backend API (внутренний доступ)
sudo netstat -tlnp | grep :8008

# Проверяем Frontend веб-сервер (внешний доступ)
sudo netstat -tlnp | grep :8090

# Или альтернативные команды
sudo ss -tlnp | grep :8008
sudo ss -tlnp | grep :8090
```

---

## Шаг 7: Запуск и тестирование

### 7.1 Запуск Backend API

```bash
cd ~/vector-db-test

# Делаем скрипты исполняемыми
chmod +x start_cpu_server.sh stop_server.sh

# Запускаем сервер
./start_cpu_server.sh
```

### 7.2 Проверка конфигурации

```bash
# Проверка централизованной конфигурации
cd ~/vector-db-test
python3 config/config_loader.py

# Ожидаемый вывод:
# ============================================================
# 🚀 Vector DB Test System
# 📍 Режим: cpu_server
# 🏠 Платформа: aspektubuntu
# 🌐 Внешний IP: 85.198.80.170
# ------------------------------------------------------------
# 🔧 Backend: http://127.0.0.1:8008
# 🎨 Frontend: http://85.198.80.170:8090
# 💾 Устройство: cpu
# 🤖 Моделей: 4
# ============================================================
```

### 7.3 Проверка работоспособности API

```bash
# Локальная проверка статуса
curl http://localhost:8008/health

# Проверка списка доступных моделей
curl http://localhost:8008/models

# Тестовый поиск
curl -X POST http://localhost:8008/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "нормативы потребления коммунальных услуг",
    "model_name": "rubert-tiny2",
    "top_k": 3
  }'
```

### 7.4 Запуск Frontend веб-сервера

```bash
cd ~/vector-db-test

# Активируем виртуальное окружение
source venv/bin/activate

# Создаем скрипт запуска Frontend
cat > start_frontend_server.sh << 'EOF'
#!/bin/bash
# Скрипт запуска Frontend веб-сервера

echo "🌐 Запуск Frontend веб-сервера..."

cd ~/vector-db-test

# Проверяем доступность порта 8090
if lsof -ti:8090 > /dev/null 2>&1; then
    echo "⚠️  Порт 8090 занят. Останавливаем предыдущий процесс..."
    lsof -ti:8090 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

echo "🚀 Запуск Frontend сервера..."
echo "🌐 Веб-интерфейс будет доступен по адресу: http://85.198.80.170:8090"
echo "💻 Откройте браузер и перейдите по этому адресу с любого компьютера"

# Запускаем веб-сервер в фоновом режиме
cd frontend
nohup python3 -m http.server 8090 --bind 0.0.0.0 > ../frontend.log 2>&1 &

# Сохраняем PID для последующей остановки  
echo $! > ../frontend.pid

echo "✅ Frontend сервер запущен в фоновом режиме (PID: $(cat ../frontend.pid))"
echo "📝 Логи Frontend: ~/vector-db-test/frontend.log"
echo "🛑 Для остановки: ./stop_frontend.sh"

# Ждем несколько секунд и проверяем статус
sleep 3
if kill -0 $(cat ../frontend.pid) 2>/dev/null; then
    echo "✅ Frontend сервер работает стабильно"
    echo "🧪 Проверьте доступность: http://85.198.80.170:8090"
else
    echo "❌ Ошибка запуска Frontend сервера. Проверьте логи: tail frontend.log"
fi
EOF

# Создаем скрипт остановки Frontend
cat > stop_frontend.sh << 'EOF'
#!/bin/bash
# Скрипт остановки Frontend сервера

echo "🛑 Остановка Frontend веб-сервера..."

cd ~/vector-db-test

if [ -f frontend.pid ]; then
    PID=$(cat frontend.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Frontend сервер остановлен (PID: $PID)"
    else
        echo "⚠️  Процесс с PID $PID уже не существует"
    fi
    rm frontend.pid
else
    echo "⚠️  Файл frontend.pid не найден, ищем процесс по порту..."
    lsof -ti:8090 | xargs kill -9 2>/dev/null || true
fi

echo "🔍 Проверяем статус порта 8090..."
if lsof -ti:8090 > /dev/null 2>&1; then
    echo "⚠️  Порт 8090 все еще занят"
else
    echo "✅ Порт 8090 свободен"
fi
EOF

# Делаем скрипты исполняемыми
chmod +x start_frontend_server.sh stop_frontend.sh

# Запускаем Frontend сервер
./start_frontend_server.sh
```

---

## Шаг 8: Обновление конфигурации Frontend

### 8.1 Настройка Frontend для локального подключения к Backend

```bash
cd ~/vector-db-test

# Обновляем конфигурацию Frontend для подключения к локальному Backend
cat > config/frontend.config.js << 'EOF'
// config/frontend.config.js
const API_CONFIG = {
    // Конфигурация для aspektubuntu: Frontend и Backend на одном сервере
    LOCAL: {
        host: '127.0.0.1',  // Backend доступен локально
        port: 8008,
        protocol: 'http'
    }
};

// Всегда используем локальное подключение к Backend
const activeConfig = API_CONFIG.LOCAL;

// Формируем базовый URL для API  
const API_BASE_URL = `${activeConfig.protocol}://${activeConfig.host}:${activeConfig.port}`;

console.log('🔗 Frontend подключается к Backend API:', API_BASE_URL);

// Экспортируем для использования в script.js
window.API_BASE_URL = API_BASE_URL;
EOF

echo "✅ Конфигурация Frontend обновлена для локального подключения к Backend"
```

### 8.2 Полная проверка работы системы

**Шаг 1: Проверка на aspektubuntu (локально)**

```bash
cd ~/vector-db-test

# Проверяем статус Backend API
curl -s http://127.0.0.1:8008/health
curl -s http://127.0.0.1:8008/models | head -20

# Проверяем статус Frontend
curl -s http://127.0.0.1:8090 | head -10

# Проверяем процессы
ps aux | grep python3 | grep -E "(8008|8090)"
```

**Шаг 2: Проверка с внешнего компьютера**

```bash
# С любого компьютера в интернете:

# Проверяем доступность Frontend (должен работать)
curl -I http://85.198.80.170:8090

# Проверяем, что Backend недоступен извне (должен выдать ошибку)
curl -I http://85.198.80.170:8008  # Ожидаем: connection refused
```

**Шаг 3: Браузерная проверка**

```bash
# Откройте браузер и перейдите по адресу:
# http://85.198.80.170:8090

# Система должна:
# ✅ 1. Загрузить веб-интерфейс (Frontend)  
# ✅ 2. Подключиться к Backend API локально
# ✅ 3. Показать список доступных моделей (4 модели)
# ✅ 4. Позволить выполнять поиск по векторным базам
# ✅ 5. Отображать время выполнения запросов
# ✅ 6. Работать сравнение между моделями

# Тестовые запросы:
# - "нормативы потребления коммунальных услуг" 
# - "жилищное законодательство"
# - "коммунальные платежи"
```

---

## Шаг 9: Мониторинг и обслуживание

### 9.1 Проверка логов

```bash
# На aspektubuntu
cd ~/vector-db-test

# Просмотр логов сервера в реальном времени
tail -f server.log

# Просмотр последних ошибок
grep -i error server.log | tail -10

# Проверка использования ресурсов
htop  # Процессы и память
iostat -x 1  # Дисковая активность
```

### 9.2 Автоматический перезапуск (опционально)

Создаем systemd service для автоматического запуска:

```bash
# Создаем service файл
sudo nano /etc/systemd/system/vector-search-api.service
```

```ini
[Unit]
Description=Vector Search API Backend
After=network.target

[Service]
Type=simple
User=userui
WorkingDirectory=/home/userui/vector-db-test
Environment=PATH=/home/userui/vector-db-test/venv/bin
Environment=CUDA_VISIBLE_DEVICES=""
Environment=OMP_NUM_THREADS=4
ExecStart=/home/userui/vector-db-test/venv/bin/python backend/run_server_cpu.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Активируем и запускаем service
sudo systemctl daemon-reload
sudo systemctl enable vector-search-api
sudo systemctl start vector-search-api

# Проверяем статус
sudo systemctl status vector-search-api
```

---

## Шаг 10: Устранение неполадок

### 10.1 Распространенные проблемы

**Проблема: Модели не загружаются**
```bash
# Решение: проверяем кэш и права доступа
ls -la ~/.cache/huggingface/hub/
chmod -R 755 ~/.cache/huggingface/hub/
```

**Проблема: Frontend недоступен извне (порт 8090)**
```bash
# Решение: проверяем firewall и network binding
sudo ufw allow 8090
sudo netstat -tlnp | grep :8090
curl http://85.198.80.170:8090
```

**Проблема: Медленная работа на CPU**
```bash
# Решение: оптимизируем количество потоков
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
```

**Проблема: Нехватка оперативной памяти**
```bash
# Решение: мониторим память и перезапускаем при необходимости
free -h
./stop_full_system.sh && sleep 5 && ./start_full_system.sh
```

**Проблема: Backend API не подключается к Frontend**
```bash
# Решение: проверяем конфигурацию и перезапускаем Backend
cat config/frontend.config.js | grep -A5 "API_CONFIG"
curl http://127.0.0.1:8008/health
./stop_server.sh && sleep 3 && ./start_cpu_server.sh
```

**Проблема: "Connection refused" при доступе к Frontend извне**
```bash
# Решение: проверяем сетевые настройки
sudo ufw status | grep 8090
sudo netstat -tlnp | grep :8090
# Если процесс слушает только 127.0.0.1, перезапускаем Frontend
./stop_frontend.sh && ./start_frontend_server.sh
```

### 10.2 Команды диагностики

```bash
# Проверка состояния системы
./diagnostics.sh
```

Создаем `diagnostics.sh`:

```bash
#!/bin/bash
echo "🔍 Диагностика системы векторного поиска"
echo "=========================================="

echo "📊 Использование ресурсов:"
free -h
df -h /

echo -e "\n🌐 Сетевые подключения:"
sudo netstat -tlnp | grep :8008
sudo netstat -tlnp | grep :8090

echo -e "\n📁 Векторные базы:"
ls -lh vectordb/

echo -e "\n🤖 Локальные модели:"
ls -la ~/.cache/huggingface/hub/ | grep models--

echo -e "\n📝 Последние ошибки в логах:"
if [ -f server.log ]; then
    tail -10 server.log | grep -i error || echo "Ошибок не найдено"
else
    echo "Лог-файл server.log не найден"
fi

echo -e "\n✅ Диагностика завершена"
```

---

## Резюме развертывания

**✅ Что будет развернуто на aspektubuntu:**

1. **Backend API** на порту 8008 (внутренний доступ, только localhost)
2. **Frontend веб-сервер** на порту 8090 (внешний доступ из интернета)
3. **4 готовые векторные базы FAISS** (1388 векторов каждая)
4. **4 локальные embedding модели** (rubert-tiny2, multilingual-e5-small, paraphrase-miniLM, labse)
5. **CPU-оптимизированная конфигурация** для стабильной работы

**🌐 Как использовать систему:**

1. **Backend API:** запускается на aspektubuntu (внутренний доступ на порту 8008)
2. **Frontend веб-сервер:** запускается на aspektubuntu (внешний доступ на порту 8090)
3. **Использование:** с любого компьютера открыть браузер → http://85.198.80.170:8090
4. **Векторный поиск:** выполняется по готовым базам без необходимости GPU

**📊 Ожидаемая производительность на CPU:**
- Время загрузки модели: 30-120 секунд
- Время поиска: 1-5 секунд на запрос 
- Потребление RAM: 2-6 GB в зависимости от модели
- Поддержка 5-20 одновременных запросов

**🔧 Управление системой:**
```bash
./start_cpu_server.sh        # Запуск Backend API
./start_frontend_server.sh   # Запуск Frontend веб-сервера
./stop_server.sh             # Остановка Backend
./stop_frontend.sh           # Остановка Frontend
./diagnostics.sh             # Диагностика системы
tail -f server.log           # Мониторинг Backend
tail -f frontend.log         # Мониторинг Frontend
```

**🌐 Быстрый запуск полной системы:**
```bash
cd ~/vector-db-test

# Создаем единый скрипт запуска
cat > start_full_system.sh << 'EOF'
#!/bin/bash
# Скрипт полного запуска системы векторного поиска

echo "🚀 Запуск полной системы векторного поиска на aspektubuntu..."

cd ~/vector-db-test

# Запускаем Backend API
echo "1️⃣ Запуск Backend API..."
./start_cpu_server.sh

# Ждем, чтобы Backend полностью загрузился
sleep 10

# Запускаем Frontend веб-сервер
echo "2️⃣ Запуск Frontend веб-сервера..."
./start_frontend_server.sh

echo ""
echo "✅ Полная система запущена!"
echo "🌐 Откройте браузер: http://85.198.80.170:8090"
echo "🔧 Для остановки всей системы: ./stop_full_system.sh"
EOF

# Создаем скрипт полной остановки
cat > stop_full_system.sh << 'EOF'
#!/bin/bash
# Скрипт полной остановки системы

echo "🛑 Остановка полной системы векторного поиска..."

cd ~/vector-db-test

echo "Останавливаем Frontend..."
./stop_frontend.sh

echo "Останавливаем Backend..."
./stop_server.sh

echo "✅ Вся система остановлена"
EOF

# Делаем скрипты исполняемыми
chmod +x start_full_system.sh stop_full_system.sh

# Быстрый запуск
./start_full_system.sh
```

---

## Приложение: Файлы для создания на aspektubuntu

### А.1 backend/config_cpu.py

```python
# backend/config_cpu.py
"""
Конфигурация для CPU-машины без GPU
"""

import torch

# Принудительное использование CPU
DEVICE = "cpu"
torch.set_num_threads(4)  # Ограничиваем количество потоков для стабильности

# Настройки для удаленного доступа
BACKEND_HOST = "0.0.0.0"  # Принимаем подключения от любых IP
BACKEND_PORT = 8008

# Отключаем GPU мониторинг
GPU_MONITORING_ENABLED = False

# Батч-размер для CPU (меньше чем для GPU)
BATCH_SIZE = 16

# Таймаут для загрузки моделей (больше на CPU)
MODEL_LOAD_TIMEOUT = 300  # 5 минут

print(f"✅ Конфигурация CPU: устройство={DEVICE}, хост={BACKEND_HOST}:{BACKEND_PORT}")
```

### А.2 backend/run_server_cpu.py

```python
#!/usr/bin/env python3
"""
Скрипт запуска Backend API сервера для CPU-машины
"""

import os
import sys
import uvicorn
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Импортируем CPU конфигурацию
from backend.config_cpu import BACKEND_HOST, BACKEND_PORT, DEVICE

def main():
    print(f"🚀 Запуск Backend API для CPU-машины...")
    print(f"📍 Устройство: {DEVICE}")
    print(f"🌐 Хост: {BACKEND_HOST}:{BACKEND_PORT}")
    print(f"🔗 API будет доступен по адресу: http://85.198.80.170:{BACKEND_PORT}")
    
    # Устанавливаем переменные окружения для CPU
    os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Отключаем GPU
    os.environ["OMP_NUM_THREADS"] = "4"
    
    # Запускаем сервер
    uvicorn.run(
        "backend.main:app",
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        reload=False,  # Отключаем автоперезагрузку на продакшене
        workers=1,     # Один воркер для стабильности на CPU
        log_level="info"
    )

if __name__ == "__main__":
    main()
```

### А.3 start_cpu_server.sh

```bash
#!/bin/bash
# Скрипт запуска системы на CPU-машине

echo "🔧 Подготовка к запуску системы векторного поиска на CPU..."

# Переходим в директорию проекта
cd ~/vector-db-test

# Активируем виртуальное окружение
source venv/bin/activate

# Проверяем доступность порта 8008
if lsof -ti:8008 > /dev/null 2>&1; then
    echo "⚠️  Порт 8008 занят. Останавливаем предыдущий процесс..."
    lsof -ti:8008 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Устанавливаем переменные окружения для CPU
export CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=4
export PYTHONPATH="${PWD}:$PYTHONPATH"

echo "🚀 Запуск Backend API сервера..."
echo "🌐 API будет доступен по адресу: http://85.198.80.170:8008"
echo "📊 Для проверки здоровья: http://85.198.80.170:8008/health"
echo "📚 Документация API: http://85.198.80.170:8008/docs"

# Запускаем сервер в фоновом режиме
nohup python3 backend/run_server_cpu.py > server.log 2>&1 &

# Сохраняем PID для последующей остановки
echo $! > server.pid

echo "✅ Сервер запущен в фоновом режиме (PID: $(cat server.pid))"
echo "📝 Логи сервера: ~/vector-db-test/server.log"
echo "🛑 Для остановки: ./stop_server.sh"

# Ждем несколько секунд и проверяем статус
sleep 5
if kill -0 $(cat server.pid) 2>/dev/null; then
    echo "✅ Сервер работает стабильно"
    
    # Пытаемся сделать тестовый запрос
    echo "🧪 Выполняем тестовый запрос..."
    curl -s http://localhost:8008/health && echo "" || echo "⚠️  Сервер еще не готов к приему запросов"
else
    echo "❌ Ошибка запуска сервера. Проверьте логи: tail server.log"
fi
```

### А.4 stop_server.sh

```bash
#!/bin/bash
# Скрипт остановки сервера

echo "🛑 Остановка Backend API сервера..."

cd ~/vector-db-test

if [ -f server.pid ]; then
    PID=$(cat server.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Сервер остановлен (PID: $PID)"
    else
        echo "⚠️  Процесс с PID $PID уже не существует"
    fi
    rm server.pid
else
    echo "⚠️  Файл server.pid не найден, ищем процесс по порту..."
    lsof -ti:8008 | xargs kill -9 2>/dev/null || true
fi

echo "🔍 Проверяем статус порта 8008..."
if lsof -ti:8008 > /dev/null 2>&1; then
    echo "⚠️  Порт 8008 все еще занят"
else
    echo "✅ Порт 8008 свободен"
fi
```

### А.5 diagnostics.sh

```bash
#!/bin/bash
echo "🔍 Диагностика системы векторного поиска"
echo "=========================================="

echo "📊 Использование ресурсов:"
free -h
df -h /

echo -e "\n🌐 Сетевые подключения:"
sudo netstat -tlnp | grep :8008
sudo netstat -tlnp | grep :8090

echo -e "\n📁 Векторные базы:"
ls -lh vectordb/

echo -e "\n🤖 Локальные модели:"
ls -la ~/.cache/huggingface/hub/ | grep models--

echo -e "\n📝 Последние ошибки в логах:"
if [ -f server.log ]; then
    tail -10 server.log | grep -i error || echo "Ошибок не найдено"
else
    echo "Лог-файл server.log не найден"
fi

echo -e "\n✅ Диагностика завершена"
```

### А.6 start_frontend_server.sh

```bash
#!/bin/bash
# Скрипт запуска Frontend веб-сервера

echo "🌐 Запуск Frontend веб-сервера..."

cd ~/vector-db-test

# Проверяем доступность порта 8090
if lsof -ti:8090 > /dev/null 2>&1; then
    echo "⚠️  Порт 8090 занят. Останавливаем предыдущий процесс..."
    lsof -ti:8090 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

echo "🚀 Запуск Frontend сервера..."
echo "🌐 Веб-интерфейс будет доступен по адресу: http://85.198.80.170:8090"
echo "💻 Откройте браузер и перейдите по этому адресу с любого компьютера"

# Запускаем веб-сервер в фоновом режиме
cd frontend
nohup python3 -m http.server 8090 --bind 0.0.0.0 > ../frontend.log 2>&1 &

# Сохраняем PID для последующей остановки  
echo $! > ../frontend.pid

echo "✅ Frontend сервер запущен в фоновом режиме (PID: $(cat ../frontend.pid))"
echo "📝 Логи Frontend: ~/vector-db-test/frontend.log"
echo "🛑 Для остановки: ./stop_frontend.sh"

# Ждем несколько секунд и проверяем статус
sleep 3
if kill -0 $(cat ../frontend.pid) 2>/dev/null; then
    echo "✅ Frontend сервер работает стабильно"
    echo "🧪 Проверьте доступность: http://85.198.80.170:8090"
else
    echo "❌ Ошибка запуска Frontend сервера. Проверьте логи: tail frontend.log"
fi
```

### А.7 stop_frontend.sh

```bash
#!/bin/bash
# Скрипт остановки Frontend сервера

echo "🛑 Остановка Frontend веб-сервера..."

cd ~/vector-db-test

if [ -f frontend.pid ]; then
    PID=$(cat frontend.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Frontend сервер остановлен (PID: $PID)"
    else
        echo "⚠️  Процесс с PID $PID уже не существует"
    fi
    rm frontend.pid
else
    echo "⚠️  Файл frontend.pid не найден, ищем процесс по порту..."
    lsof -ti:8090 | xargs kill -9 2>/dev/null || true
fi

echo "🔍 Проверяем статус порта 8090..."
if lsof -ti:8090 > /dev/null 2>&1; then
    echo "⚠️  Порт 8090 все еще занят"
else
    echo "✅ Порт 8090 свободен"
fi
```

### А.8 config/frontend.config.js (обновленная конфигурация)

```javascript
// config/frontend.config.js
const API_CONFIG = {
    // Конфигурация для aspektubuntu: Frontend и Backend на одном сервере
    LOCAL: {
        host: '127.0.0.1',  // Backend доступен локально
        port: 8008,
        protocol: 'http'
    }
};

// Всегда используем локальное подключение к Backend
const activeConfig = API_CONFIG.LOCAL;

// Формируем базовый URL для API  
const API_BASE_URL = `${activeConfig.protocol}://${activeConfig.host}:${activeConfig.port}`;

console.log('🔗 Frontend подключается к Backend API:', API_BASE_URL);

// Экспортируем для использования в script.js
window.API_BASE_URL = API_BASE_URL;
```

### А.9 start_full_system.sh

```bash
#!/bin/bash
# Скрипт полного запуска системы векторного поиска

echo "🚀 Запуск полной системы векторного поиска на aspektubuntu..."

cd ~/vector-db-test

# Запускаем Backend API
echo "1️⃣ Запуск Backend API..."
./start_cpu_server.sh

# Ждем, чтобы Backend полностью загрузился
sleep 10

# Запускаем Frontend веб-сервер
echo "2️⃣ Запуск Frontend веб-сервера..."
./start_frontend_server.sh

echo ""
echo "✅ Полная система запущена!"
echo "🌐 Откройте браузер: http://85.198.80.170:8090"
echo "🔧 Для остановки всей системы: ./stop_full_system.sh"
```

### А.10 stop_full_system.sh

```bash
#!/bin/bash
# Скрипт полной остановки системы

echo "🛑 Остановка полной системы векторного поиска..."

cd ~/vector-db-test

echo "Останавливаем Frontend..."
./stop_frontend.sh

echo "Останавливаем Backend..."
./stop_server.sh

echo "✅ Вся система остановлена"
```

---

## Краткое руководство пользователя

### Для администратора aspektubuntu:

```bash
# Первоначальный запуск (после развертывания)
cd ~/vector-db-test
./start_full_system.sh

# Ежедневное управление
./stop_full_system.sh   # Остановка
./start_full_system.sh  # Запуск
./diagnostics.sh        # Проверка состояния

# Мониторинг
tail -f server.log      # Backend логи
tail -f frontend.log    # Frontend логи
htop                   # Использование ресурсов
```

### Для пользователей системы:

```
1. Откройте браузер
2. Перейдите по адресу: http://85.198.80.170:8090
3. Выберите модель для поиска
4. Введите поисковый запрос
5. Просматривайте результаты с метаданными
6. Сравнивайте разные модели
```

**🎯 Готовые тестовые запросы:**
- "нормативы потребления коммунальных услуг"
- "жилищное законодательство" 
- "коммунальные платежи"
- "права и обязанности собственников"
- "управляющие компании"

Система готова к развертыванию! 🚀 


@Примеры_вопросов_консультационного_харракткра.txt 
проанализируй существующий проект - функционал сравнение llm. есть задача - выполнить генерацию ответов на вопросы с использованием набора чанков, подготовленных разными моделями эмбедингов и использованием разных провайдеров и разных моделей ллм. список вопросов в файле примеры_вопросов_консультационного...

думаю, надо использовать существующие эндпоинты бэкенда, 

подготовь удобную структуру, где будут перечислены все 5 моделей  эмбедингов, далее надо опросить всех трех провайдеров и получить доступные модели и подготовить удобную структуру, где перечислены все эти модели. эта структура должна быть удобна для корректировки пользователей обычным текстовым редактором, например это может быть json.

далее надо с использованием существующих ендпоинтов или добавить новые необходимые ендпоинты, сгенерировать код, который будет брать очередной вопрос из файла, применять  последовательно из отредактированного пользователем json очередную модель эмбедингов, искать 5 чанков, подавать вопрос с чанками в очередную модель , получать ответ и сохранять в xls файл ответ модели, чанки с метаданными, входные токены, выходные токены, стоимость запроса - все это в разные колонки. .

по итогу эксперты по данным вопросам и ответам разных моделей будут оценивать, какие модели справились лучше с ответами и какие модели эмбедингов выдали наиболее подходящие чанки.

при необходимости тестового запуска кода разрешено проверять только на очень ограниченном наборе вопросов и моделей, допустим 3 вопроса и 3 разных модели ллм и 3 разных модели эмбедингов.
