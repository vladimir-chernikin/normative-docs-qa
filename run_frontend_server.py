#!/usr/bin/env python3
"""
Простой HTTP сервер для тестового фронтенда
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8080
FRONTEND_DIR = Path("/home/olga/normativ_docs/Волков/test_frontend")

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Добавляем CORS заголовки для возможности запросов к API
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

        # Добавляем правильную кодировку для HTML файлов
        if self.path.endswith('.html') or self.path == '/':
            self.send_header('Content-Type', 'text/html; charset=utf-8')

        super().end_headers()

    def do_GET(self):
        # Если запрос корня, отдаем index.html
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

def start_server():
    # Переключаемся в директорию с фронтендом
    os.chdir(FRONTEND_DIR)

    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print("\n" + "=" * 60)
        print("🚀 ЗАПУСК ТЕСТОВОГО ФРОНТЕНДА")
        print("=" * 60)
        print(f"📍 URL: http://localhost:{PORT}")
        print(f"📁 Директория: {FRONTEND_DIR}")
        print(f"🔗 API: http://localhost:8001")
        print("=" * 60)
        print("Нажмите Ctrl+C для остановки\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✅ Сервер остановлен")

if __name__ == "__main__":
    start_server()
