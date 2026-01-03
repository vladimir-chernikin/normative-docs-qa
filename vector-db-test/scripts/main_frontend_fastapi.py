#!/usr/bin/env python3
"""
Стабильный фронтенд-сервер на базе FastAPI + Uvicorn
Решает проблему зависания от ботов и некорректных запросов
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import socket

def get_local_ip():
    """Получить локальный IP адрес"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "unknown"

# Создаем экземпляр FastAPI
app = FastAPI(
    title="STAZH Aspect Frontend",
    description="Стабильный фронтенд-сервер на базе FastAPI",
    version="2.0.0"
)

# Определяем путь к директории frontend (на два уровня выше от текущего скрипта)
frontend_dir = Path(__file__).parent.parent / "frontend"

# Проверяем существование директории
if not frontend_dir.exists():
    raise RuntimeError(f"❌ Директория frontend не найдена: {frontend_dir}")

# "Монтируем" директорию frontend. Запросы к корневому URL ("/") 
# будут отдавать статические файлы из этой директории.
# Параметр html=True автоматически делает index.html страницей по умолчанию.
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")

print(f"✅ Frontend сервер сконфигурирован")
print(f"📁 Директория: {frontend_dir}")
print(f"🌐 Локальный IP: {get_local_ip()}")
