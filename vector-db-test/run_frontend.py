#!/usr/bin/env python3
"""Точка входа для запуска Frontend сервера."""
import os
import sys
import argparse
import subprocess
from pathlib import Path
import importlib.util

# Добавляем корень проекта в sys.path для корректных импортов
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def import_module_from_file(module_name, file_path):
    """Импортирует модуль из файла по указанному пути."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Не удалось загрузить модуль из {file_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def main():
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="Запуск Frontend сервера")
    parser.add_argument("--mode", choices=["cpu", "gpu"], default="cpu",
                        help="Режим работы: cpu или gpu (по умолчанию: cpu)")
    parser.add_argument("--env", choices=["prod", "dev"], default="prod",
                        help="Среда выполнения: prod (рабочий сервер) или dev (машина разработки) (по умолчанию: prod)")
    parser.add_argument("--port", type=int, default=8090,
                        help="Порт для запуска сервера (по умолчанию: 8090)")
    parser.add_argument("--skip-check", action="store_true",
                        help="Пропустить проверку моделей")
    args = parser.parse_args()
    
    # Если не указан флаг пропуска проверки, проверяем наличие моделей
    if not args.skip_check:
        print("🔍 Проверка наличия моделей перед запуском фронтенда...")
        try:
            # Запускаем скрипт проверки моделей
            result = subprocess.run(
                [sys.executable, str(project_root / "check_models.py")],
                check=False,
                capture_output=True,
                text=True
            )
            
            # Выводим результат проверки
            print(result.stdout)
            
            # Если проверка не прошла, выводим предупреждение
            if result.returncode != 0:
                print("\n⚠️ ПРЕДУПРЕЖДЕНИЕ: Некоторые модели отсутствуют или повреждены.")
                print("⚠️ Фронтенд будет запущен, но некоторые функции могут не работать.")
                print("⚠️ Для загрузки моделей выполните: python download_models.py")
                print("\n⚠️ Нажмите Enter для продолжения или Ctrl+C для отмены...")
                input()  # Ждем подтверждения от пользователя
        except Exception as e:
            print(f"❌ Ошибка при проверке моделей: {e}")
            print("⚠️ Продолжаем запуск без проверки моделей.")
    
    # Конфигурируем фронтенд
    try:
        # Загружаем модуль configure_frontend из файла
        configure_frontend_path = project_root / "scripts" / "configure_frontend.py"
        configure_frontend = import_module_from_file("configure_frontend", configure_frontend_path)
        configure_frontend.generate_frontend_config(args.mode, args.env)
    except Exception as e:
        print(f"❌ Ошибка при конфигурации фронтенда: {e}")
        print("⚠️ Продолжаем запуск с настройками по умолчанию.")
    
    # Запускаем стабильный веб-сервер на базе FastAPI + Uvicorn
    try:
        import uvicorn
        print("🚀 Запуск стабильного Frontend сервера на базе FastAPI/Uvicorn...")
        print("🛡️ Защита от зависания при некорректных запросах ботов")
        print(f"🔗 Сервер будет доступен на порту {args.port}")
        print("=" * 60)
        
        uvicorn.run(
            "scripts.main_frontend_fastapi:app",  # Путь к новому файлу и переменной app
            host="0.0.0.0",
            port=args.port,  # Используем порт из аргументов (8090 по умолчанию)
            reload=False,    # Отключаем автоперезагрузку для продакшена
            log_level="info",
            access_log=True  # Включаем логирование доступа
        )
    except ImportError:
        print("❌ Ошибка: uvicorn не установлен")
        print("💡 Установите командой: pip install uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка при запуске фронтенд-сервера Uvicorn: {e}")
        print(f"Детали ошибки: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
