#!/usr/bin/env python3
"""Генерирует конфигурационный файл для фронтенда."""
import json
import sys
from pathlib import Path
import socket

project_root = Path(__file__).parent.parent

def is_local_machine():
    """Проверяет, запущен ли скрипт на локальной машине разработчика."""
    hostname = socket.gethostname()
    return "sawa6195355" in hostname or hostname == "sawaTitan18"

def generate_frontend_config(mode: str, env: str = "prod"):
    """Геренрирует frontend.config.js на основе главного config.json."""
    config_path = project_root / "config" / "config.json"
    frontend_config_path = project_root / "frontend" / "config" / "frontend.config.js"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Ошибка чтения config.json: {e}", file=sys.stderr)
        sys.exit(1)

    # Определяем хост в зависимости от среды выполнения
    if env == "dev" and is_local_machine():
        host = "localhost"  # Для локальной разработки на машине разработчика используем localhost
    else:
        # Для prod или для dev на удаленном сервере используем хост из конфигурации
        if mode == 'gpu':
            server_config = config.get('gpu_server')
            if not server_config:
                print("❌ Секция 'gpu_server' не найдена в config.json", file=sys.stderr)
                sys.exit(1)
        elif mode == 'cpu':
            server_config = config.get('cpu_server')
            if not server_config:
                print("❌ Секция 'cpu_server' не найдена в config.json", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"❌ Неверный режим '{mode}'. Используйте 'gpu' или 'cpu'.", file=sys.stderr)
            sys.exit(1)
        
        host = server_config.get('host')
    
    # Определяем порт из конфигурации
    if mode == 'gpu':
        port = config.get('gpu_server', {}).get('port', 8008)
    else:
        port = config.get('cpu_server', {}).get('port', 8008)

    backend_url = f"http://{host}:{port}"

    print(f"🔧 Конфигурирую фронтенд для режима '{mode}' в среде '{env}' с URL: {backend_url}")

    js_content = f"""// ⚠️ THIS FILE IS AUTO-GENERATED. DO NOT EDIT MANUALLY.
const config = {{
    backendUrl: '{backend_url}'
}};
"""

    try:
        frontend_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(frontend_config_path, 'w', encoding='utf-8') as f:
            f.write(js_content)
        print(f"✅ Конфигурация успешно записана в {frontend_config_path}")
    except IOError as e:
        print(f"❌ Ошибка записи в {frontend_config_path}: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Генерируем файл с конфигурацией баз данных
    generate_database_config(config)

def generate_database_config(config):
    """Генерирует файл database_config.js с названиями баз данных из config.json."""
    database_config_path = project_root / "frontend" / "config" / "database_config.js"
    
    # Получаем данные о базах данных из конфигурации
    databases = config.get('databases', {})
    
    # Если секция databases отсутствует, используем значения по умолчанию
    if not databases:
        databases = {
            "current": {
                "name": "Текущая база",
                "description": "База данных с нормативными документами"
            },
            "new": {
                "name": "Новая база",
                "description": "Новая база данных для тестирования"
            }
        }
    
    # Формируем содержимое JavaScript файла
    js_content = """// Конфигурация баз данных
// Этот файл автоматически генерируется скриптом configure_frontend.py

const databaseConfig = {
"""
    
    # Добавляем данные о каждой базе данных
    for db_key, db_info in databases.items():
        js_content += f"""    {db_key}: {{
        name: "{db_info.get('name', 'База данных')}",
        description: "{db_info.get('description', 'Описание отсутствует')}"
    }},
"""
    
    # Закрываем объект
    js_content = js_content.rstrip(",\n") + "\n};"
    
    try:
        database_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(database_config_path, 'w', encoding='utf-8') as f:
            f.write(js_content)
        print(f"✅ Конфигурация баз данных успешно записана в {database_config_path}")
    except IOError as e:
        print(f"❌ Ошибка записи в {database_config_path}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        env = sys.argv[2] if len(sys.argv) > 2 else "prod"
        generate_frontend_config(mode, env)
    else:
        print("Usage: python configure_frontend.py <gpu|cpu> [prod|dev]", file=sys.stderr)
        sys.exit(1)