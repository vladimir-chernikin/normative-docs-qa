#!/usr/bin/env python3
"""
Скрипт запуска удаленного веб-сервера для frontend
Режим: удаленный доступ со всех IP адресов
Host: 0.0.0.0:8090 (доступен как sawa6195355.mooo.com:8090)
"""

import os
import sys
import http.server
import socketserver
import socket
import json
from pathlib import Path

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Кастомный обработчик с логированием запросов"""
    
    def log_message(self, format, *args):
        """Переопределяем логирование для более информативного вывода"""
        client_ip = self.client_address[0]
        print(f"📡 {client_ip} - {format % args}")

def get_local_ip():
    """Получить локальный IP адрес"""
    try:
        # Подключаемся к внешнему адресу чтобы узнать локальный IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "unknown"

def get_api_url(env="prod"):
    """Получить URL API на основе конфигурации и среды"""
    project_root = Path(__file__).parent.parent
    config_path = project_root / "frontend" / "config" / "frontend.config.js"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Извлекаем URL из JS файла с помощью простого парсинга
            import re
            match = re.search(r"backendUrl: '(http://[^']*)'", content)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"⚠️ Не удалось прочитать конфигурацию API URL: {e}")
    
    # Значения по умолчанию, если не удалось прочитать конфигурацию
    if env == "dev":
        return "http://localhost:8008"
    else:
        return "http://sawa6195355.mooo.com:8008"  # Для prod

def start_remote_server(env="prod"):
    """Запуск удаленного веб-сервера для frontend"""
    
    # Путь к frontend директории
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / "frontend"
    
    # Проверяем существование frontend директории
    if not frontend_dir.exists():
        print(f"❌ Ошибка: директория {frontend_dir} не найдена")
        return False
    
    # Переходим в frontend директорию
    os.chdir(frontend_dir)
    
    # Настройки сервера
    HOST = "0.0.0.0"  # Принимаем соединения со всех IP
    PORT = 8090
    local_ip = get_local_ip()
    api_url = get_api_url(env)
    
    print("🚀 Запуск удаленного веб-сервера...")
    print(f"📍 Режим: удаленный доступ")
    print(f"🔗 Локальный адрес: http://{local_ip}:{PORT}")
    print(f"🌍 Внешний адрес: http://sawa6195355.mooo.com:{PORT}")
    print(f"📁 Директория: {frontend_dir}")
    print(f"🎯 Целевой API: {api_url}")
    print("=" * 50)
    
    try:
        # Создаем веб-сервер с кастомным обработчиком
        with socketserver.TCPServer((HOST, PORT), CustomHTTPRequestHandler) as httpd:
            print(f"✅ Сервер запущен и принимает соединения")
            print(f"🔍 Слушаю на {HOST}:{PORT}")
            print(f"🌐 Доступен по адресам:")
            print(f"   • http://127.0.0.1:{PORT} (локально)")
            print(f"   • http://{local_ip}:{PORT} (локальная сеть)")
            print(f"   • http://sawa6195355.mooo.com:{PORT} (интернет)")
            print("⏹️  Для остановки нажмите Ctrl+C")
            print("-" * 50)
            print("📊 Журнал запросов:")
            
            # Запускаем сервер
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен пользователем")
        return True
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Ошибка: порт {PORT} уже занят")
            print(f"💡 Попробуйте завершить процесс: lsof -ti:{PORT} | xargs kill -9")
        else:
            print(f"❌ Ошибка запуска сервера: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False



def main(env="prod"):
    """Главная функция"""
    print("=" * 60)
    print("🌍 УДАЛЕННЫЙ ЗАПУСК FRONTEND СЕРВЕРА")
    print("=" * 60)
    
    # Информация о системе
    print(f"🐍 Python: {sys.version}")
    print(f"💻 OS: {os.name}")
    print(f"📂 Рабочая директория: {os.getcwd()}")
    print(f"🌐 Локальный IP: {get_local_ip()}")
    print("-" * 60)
    
    # Запускаем сервер
    success = start_remote_server(env)
    
    if success:
        print("\n✅ Сервер успешно завершен")
    else:
        print("\n❌ Сервер завершен с ошибкой")
        sys.exit(1)

if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "prod"
    main(env) 