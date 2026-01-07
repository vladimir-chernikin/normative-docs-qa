#!/usr/bin/env python3
"""
Загрузчик централизованной конфигурации для системы векторного поиска
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigLoader:
    """Загрузчик конфигурации из config.json"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Инициализация загрузчика конфигурации
        
        Args:
            config_file: Путь к файлу конфигурации (по умолчанию config/config.json)
        """
        if config_file is None:
            # Определяем корневую директорию проекта
            current_dir = Path(__file__).parent
            project_root = current_dir.parent
            config_file = project_root / "config" / "config.json"
        
        self.config_file = Path(config_file)
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Загружает конфигурацию из JSON файла"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Конфигурация загружена из {self.config_file}")
        except FileNotFoundError:
            raise FileNotFoundError(f"❌ Файл конфигурации не найден: {self.config_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"❌ Ошибка чтения JSON конфигурации: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Получить значение по пути ключей (например, 'backend.port')
        
        Args:
            key_path: Путь к ключу через точку (например, 'backend.port')
            default: Значение по умолчанию если ключ не найден
            
        Returns:
            Значение из конфигурации или default
        """
        if self._config is None:
            return default
        
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_backend_config(self) -> Dict[str, Any]:
        """Получить конфигурацию Backend сервера"""
        return self.get('backend', {})
    
    def get_frontend_config(self) -> Dict[str, Any]:
        """Получить конфигурацию Frontend сервера"""
        return self.get('frontend', {})
    
    def get_backend_url(self, internal: bool = True) -> str:
        """
        Получить URL Backend API
        
        Args:
            internal: True для внутреннего доступа, False для внешнего
            
        Returns:
            URL Backend API
        """
        if internal:
            return self.get('urls.backend_internal', 'http://127.0.0.1:8008')
        else:
            host = self.get('deployment.external_ip', '127.0.0.1')
            port = self.get('backend.port', 8008)
            return f"http://{host}:{port}"
    
    def get_frontend_url(self, external: bool = True) -> str:
        """
        Получить URL Frontend сервера
        
        Args:
            external: True для внешнего доступа, False для локального
            
        Returns:
            URL Frontend сервера
        """
        if external:
            return self.get('urls.frontend_external', 'http://85.198.80.170:8090')
        else:
            return self.get('urls.frontend_local', 'http://127.0.0.1:8090')
    
    def get_system_config(self) -> Dict[str, Any]:
        """Получить системную конфигурацию"""
        return self.get('system', {})
    
    def is_cpu_mode(self) -> bool:
        """Проверить, работает ли система в CPU режиме"""
        return self.get('models.device', 'cpu') == 'cpu'
    
    def get_models_list(self) -> list:
        """Получить список поддерживаемых моделей"""
        return self.get('models.embedding_models', [])
    
    def print_summary(self) -> None:
        """Вывести сводку конфигурации"""
        print("=" * 60)
        print(f"🚀 {self.get('project', 'Vector DB Test System')}")
        print(f"📍 Режим: {self.get('deployment.mode', 'unknown')}")
        print(f"🏠 Платформа: {self.get('deployment.platform', 'unknown')}")
        print(f"🌐 Внешний IP: {self.get('deployment.external_ip', 'unknown')}")
        print("-" * 60)
        print(f"🔧 Backend: {self.get_backend_url(internal=True)}")
        print(f"🎨 Frontend: {self.get_frontend_url(external=True)}")
        print(f"💾 Устройство: {self.get('models.device', 'unknown')}")
        print(f"🤖 Моделей: {len(self.get_models_list())}")
        print("=" * 60)

# Глобальный экземпляр загрузчика для импорта
config = ConfigLoader()

# Функции-хелперы для быстрого доступа
def get_backend_port() -> int:
    """Получить порт Backend сервера"""
    return config.get('backend.port', 8008)

def get_frontend_port() -> int:
    """Получить порт Frontend сервера"""
    return config.get('frontend.port', 8090)

def get_backend_host() -> str:
    """Получить хост Backend сервера"""
    return config.get('backend.host', '0.0.0.0')

def get_frontend_host() -> str:
    """Получить хост Frontend сервера"""
    return config.get('frontend.host', '0.0.0.0')

def get_api_url() -> str:
    """Получить URL для подключения к Backend API (внутренний)"""
    return config.get_backend_url(internal=True)

def get_web_url() -> str:
    """Получить URL веб-интерфейса (внешний)"""
    return config.get_frontend_url(external=True)

if __name__ == "__main__":
    # Тестирование загрузчика конфигурации
    print("🧪 Тестирование загрузчика конфигурации...")
    config.print_summary()
    
    print("\n📊 Тестовые значения:")
    print(f"Backend порт: {get_backend_port()}")
    print(f"Frontend порт: {get_frontend_port()}")
    print(f"API URL: {get_api_url()}")
    print(f"Web URL: {get_web_url()}")
    print(f"CPU режим: {config.is_cpu_mode()}")
    print(f"Модели: {config.get_models_list()}") 