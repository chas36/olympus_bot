#!/usr/bin/env python3
"""
Скрипт проверки готовности системы к запуску

Проверяет:
- Наличие и корректность .env файла
- Подключение к БД
- Доступность Telegram API
- Структуру директорий
- Зависимости Python

Использование:
    python scripts/system_check.py
"""

import os
import sys
from pathlib import Path
import asyncio

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

# Цвета для вывода
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Печатает заголовок"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_ok(text):
    """Печатает успех"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text):
    """Печатает ошибку"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text):
    """Печатает предупреждение"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


# Константы для проверки плейсхолдеров переменных окружения
PLACEHOLDER_PREFIXES = ['your_', 'STRONG_PASSWORD']

def check_env_file():
    """Проверка .env файла"""
    print_header("1. Проверка .env файла")
    
    if not os.path.exists('.env'):
        print_error("Файл .env не найден!")
        print("   Создайте его из .env.example: cp .env.example .env")
        return False
    
    print_ok("Файл .env найден")
    
    # Загружаем переменные
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'BOT_TOKEN',
        'DATABASE_URL',
        'DATABASE_URL_SYNC',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or any(value.startswith(prefix) for prefix in PLACEHOLDER_PREFIXES):
            missing_vars.append(var)
            print_error(f"  {var} не настроен или использует значение по умолчанию")
        else:
            print_ok(f"  {var} настроен")
    
    if missing_vars:
        print_error("Необходимо настроить переменные окружения!")
        return False
    
    return True


def check_directories():
    """Проверка необходимых директорий"""
    print_header("2. Проверка структуры директорий")
    
    required_dirs = [
        'bot',
        'api',
        'database',
        'parser',
        'tasks',
        'utils',
        'admin_panel',
        'uploads',
        'screenshots',
        'logs'
    ]
    
    all_exist = True
    for directory in required_dirs:
        if os.path.exists(directory):
            print_ok(f"  {directory}/")
        else:
            print_error(f"  {directory}/ не найдена")
            all_exist = False
            # Создаем директорию
            os.makedirs(directory, exist_ok=True)
            print_warning(f"    Создана директория {directory}/")
    
    return all_exist


def check_python_packages():
    """Проверка установленных пакетов"""
    print_header("3. Проверка Python пакетов")
    
    required_packages = {
        'aiogram': 'aiogram',
        'fastapi': 'fastapi',
        'sqlalchemy': 'sqlalchemy',
        'asyncpg': 'asyncpg',
        'psycopg2': 'psycopg2',
        'python-docx': 'docx',
        'apscheduler': 'apscheduler',
        'python-dotenv': 'dotenv',
        'uvicorn': 'uvicorn',
        'alembic': 'alembic',
    }
    
    missing_packages = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print_ok(f"  {package_name}")
        except ImportError:
            print_error(f"  {package_name} не установлен")
            missing_packages.append(package_name)
    
    if missing_packages:
        print_error("Установите зависимости: pip install -r requirements.txt")
        return False
    
    return True


async def check_database():
    """Проверка подключения к БД"""
    print_header("4. Проверка подключения к базе данных")
    
    try:
        from database.database import async_engine
        from sqlalchemy import text
        
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
        
        print_ok("Подключение к PostgreSQL установлено")
        
        # Проверяем наличие таблиц
        async with async_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            tables = [row[0] for row in result]
        
        if tables:
            print_ok(f"  Найдено таблиц: {len(tables)}")
            for table in tables:
                print(f"    - {table}")
        else:
            print_warning("  Таблицы не найдены")
            print("    Выполните: python main.py init")
        
        return True
        
    except Exception as e:
        print_error(f"Ошибка подключения к БД: {e}")
        print("   Убедитесь, что PostgreSQL запущен и DATABASE_URL настроен правильно")
        return False


async def check_telegram_bot():
    """Проверка Telegram бота"""
    print_header("5. Проверка Telegram бота")
    
    try:
        from aiogram import Bot
        from dotenv import load_dotenv
        
        load_dotenv()
        bot_token = os.getenv('BOT_TOKEN')
        
        if not bot_token or bot_token.startswith('your_'):
            print_error("BOT_TOKEN не настроен")
            return False
        
        bot = Bot(token=bot_token)
        
        # Проверяем токен
        me = await bot.get_me()
        print_ok(f"Бот найден: @{me.username}")
        print(f"   ID: {me.id}")
        print(f"   Имя: {me.first_name}")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        print_error(f"Ошибка проверки бота: {e}")
        print("   Проверьте правильность BOT_TOKEN")
        return False


def check_parser():
    """Проверка парсера"""
    print_header("6. Проверка парсера документов")
    
    try:
        from parser.docx_parser import parse_olympiad_file
        print_ok("Парсер импортирован успешно")
        
        # Проверяем наличие тестового файла
        test_file = "8Ð.docx"
        if os.path.exists(test_file):
            print_ok(f"  Тестовый файл найден: {test_file}")
            try:
                result = parse_olympiad_file(test_file)
                print_ok(f"  Парсинг успешен:")
                print(f"    - Предмет: {result['subject']}")
                print(f"    - Кодов 8 класса: {len(result['grade8_codes'])}")
                print(f"    - Кодов 9 класса: {len(result['grade9_codes'])}")
            except Exception as e:
                print_error(f"  Ошибка парсинга: {e}")
                return False
        else:
            print_warning(f"  Тестовый файл {test_file} не найден (необязательно)")
        
        return True
        
    except Exception as e:
        print_error(f"Ошибка проверки парсера: {e}")
        return False


async def main():
    """Главная функция"""
    print(f"\n{Colors.BOLD}🔍 Проверка системы Olympus Bot{Colors.END}")
    
    checks = [
        ("ENV файл", check_env_file()),
        ("Директории", check_directories()),
        ("Python пакеты", check_python_packages()),
        ("База данных", await check_database()),
        ("Telegram бот", await check_telegram_bot()),
        ("Парсер", check_parser()),
    ]
    
    print_header("📊 Результаты проверки")
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for name, result in checks:
        status = f"{Colors.GREEN}✅ OK{Colors.END}" if result else f"{Colors.RED}❌ FAILED{Colors.END}"
        print(f"  {name}: {status}")
    
    print(f"\n{Colors.BOLD}Пройдено: {passed}/{total}{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Система готова к запуску!{Colors.END}")
        print(f"\nДля запуска используйте:")
        print(f"  {Colors.BLUE}python main.py all{Colors.END}  (бот + API)")
        print(f"  {Colors.BLUE}docker-compose up -d{Colors.END}  (через Docker)")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Система не готова к запуску{Colors.END}")
        print(f"\nИсправьте ошибки выше и запустите проверку снова")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
