#!/usr/bin/env python3
"""
QuickConverterBot - Запуск бота
"""
import os
import sys
import asyncio
from pathlib import Path

def load_env_file():
    """Загружает переменные из .env файла"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ Файл .env не найден!")
        print("\nСоздай файл .env в корне проекта:")
        print("BOT_TOKEN=твой_токен_от_botfather")
        print("DATABASE_PATH=data/db.sqlite3")
        print("SCHEDULER_INTERVAL_SECONDS=60")
        return False
    
    try:
        # Загружаем .env файл
        from dotenv import load_dotenv
        load_dotenv()
        return True
    except ImportError:
        print("❌ Модуль python-dotenv не установлен!")
        print("Установи: pip install python-dotenv")
        return False
    except Exception as e:
        print(f"❌ Ошибка загрузки .env: {e}")
        return False

def validate_token():
    """Проверяет токен бота"""
    token = os.getenv("BOT_TOKEN")
    
    if not token:
        print("❌ BOT_TOKEN не найден в .env файле!")
        return False
    
    # Убираем лишние пробелы и переносы строк
    token = token.strip()
    
    if len(token) < 30:
        print("❌ BOT_TOKEN слишком короткий!")
        return False
    
    # Проверяем формат токена (должен содержать двоеточие)
    if ":" not in token:
        print("❌ BOT_TOKEN должен содержать двоеточие (:)")
        return False
    
    # Проверяем, что первая часть - это число
    try:
        bot_id = int(token.split(":")[0])
        if bot_id <= 0:
            print("❌ ID бота должен быть положительным числом")
            return False
    except ValueError:
        print("❌ ID бота должен быть числом")
        return False
    
    print(f"✅ Токен найден для бота ID: {bot_id}")
    return True

def check_dependencies():
    """Проверяет необходимые зависимости"""
    try:
        import aiogram
        import httpx
        import aiosqlite
        print("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("Установи: pip install -r requirements.txt")
        return False

def main():
    """Основная функция"""
    print("🚀 QuickConverterBot - Запуск...")
    print("=" * 50)
    
    # Шаг 1: Загружаем .env
    print("📋 Шаг 1: Загрузка конфигурации...")
    if not load_env_file():
        return 1
    
    # Шаг 2: Проверяем токен
    print("🔑 Шаг 2: Проверка токена...")
    if not validate_token():
        return 1
    
    # Шаг 3: Проверяем зависимости
    print("📦 Шаг 3: Проверка зависимостей...")
    if not check_dependencies():
        return 1
    
    # Шаг 4: Запускаем бота
    print("🤖 Шаг 4: Запуск бота...")
    print("💡 Для остановки нажми Ctrl+C")
    print("=" * 50)
    
    try:
        # Импортируем и запускаем бота
        from src.bot import run_bot
        asyncio.run(run_bot())
        
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
        return 0
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Проверь, что все файлы на месте")
        return 1
        
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        print("Проверь логи и попробуй снова")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
