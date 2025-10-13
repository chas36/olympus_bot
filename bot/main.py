import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from loguru import logger

from database.database import init_db, close_db
from bot.handlers import registration, olympiad, screenshots
from bot.middlewares import LoggingMiddleware, ThrottlingMiddleware
from tasks.reminders import setup_reminder_scheduler

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
os.makedirs("logs", exist_ok=True)
logger.add(
    "logs/bot.log",
    rotation="1 day",
    retention="1 month",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)


async def main():
    """Главная функция запуска бота"""
    
    # Получаем токен бота
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("❌ BOT_TOKEN не найден в .env файле!")
        return
    
    # Создаем бота и диспетчер
    bot = Bot(token=bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрируем middleware
    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(ThrottlingMiddleware(rate_limit=1))
    
    # Регистрируем роутеры
    dp.include_router(registration.router)
    dp.include_router(olympiad.router)
    dp.include_router(screenshots.router)
    
    # Инициализируем базу данных
    logger.info("🔄 Инициализация базы данных...")
    await init_db()
    
    # Настраиваем планировщик напоминаний
    logger.info("🔄 Настройка планировщика напоминаний...")
    scheduler = setup_reminder_scheduler(bot)
    scheduler.start()
    
    # Запускаем бота
    logger.info("🚀 Бот запущен и готов к работе!")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        # Закрытие соединений при остановке
        logger.info("🔄 Остановка бота...")
        scheduler.shutdown()
        await close_db()
        await bot.session.close()
        logger.info("✅ Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Бот остановлен пользователем")
