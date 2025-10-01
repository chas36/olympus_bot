"""
Главный файл для запуска всех компонентов Olympus Bot
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()


async def init_database():
    """Инициализация базы данных"""
    print("🔄 Инициализация базы данных...")
    from database.database import init_db
    await init_db()
    print("✅ База данных инициализирована")


async def run_migrations():
    """Запуск миграций Alembic"""
    print("🔄 Применение миграций...")
    import subprocess
    result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Миграции применены")
    else:
        print(f"❌ Ошибка миграций: {result.stderr}")


async def start_bot():
    """Запуск Telegram бота"""
    print("🤖 Запуск Telegram бота...")
    from bot.main import main
    await main()


async def start_api():
    """Запуск FastAPI сервера"""
    print("🌐 Запуск API сервера...")
    import uvicorn
    from api.main import app
    
    config = uvicorn.Config(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Главная функция"""
    print("=" * 50)
    print("🏆 Olympus Bot - Система управления олимпиадами")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("\nИспользование:")
        print("  python main.py init     - Инициализировать БД")
        print("  python main.py migrate  - Применить миграции")
        print("  python main.py bot      - Запустить бота")
        print("  python main.py api      - Запустить API")
        print("  python main.py all      - Запустить бота и API одновременно")
        return
    
    command = sys.argv[1].lower()
    
    if command == "init":
        await init_database()
    
    elif command == "migrate":
        await run_migrations()
    
    elif command == "bot":
        await init_database()
        await start_bot()
    
    elif command == "api":
        await init_database()
        await start_api()
    
    elif command == "all":
        await init_database()
        # Запускаем бота и API параллельно
        await asyncio.gather(
            start_bot(),
            start_api()
        )
    
    else:
        print(f"❌ Неизвестная команда: {command}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Остановка системы...")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
