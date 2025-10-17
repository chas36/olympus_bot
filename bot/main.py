import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from loguru import logger

from database.database import init_db, close_db
from bot.handlers import registration, olympiad, screenshots, admin
from bot.handlers import admin_extended, admin_olympiads
from bot.middlewares import LoggingMiddleware, ThrottlingMiddleware
from tasks.reminders import setup_reminder_scheduler
from utils.scheduler import send_pending_olympiad_notifications

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


async def olympiad_notification_scheduler(bot: Bot):
    """Планировщик для отложенных уведомлений об олимпиадах"""
    logger.info("⏰ Запуск планировщика уведомлений об олимпиадах...")

    while True:
        try:
            await send_pending_olympiad_notifications(bot)
        except Exception as e:
            logger.error(f"❌ Ошибка в планировщике уведомлений: {e}")

        # Проверяем каждую минуту
        await asyncio.sleep(60)


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
    dp.include_router(admin.router)  # Админ роутер первым для приоритета
    dp.include_router(admin_extended.router)  # Расширенные админ функции
    dp.include_router(admin_olympiads.router)  # Управление олимпиадами и экспорт
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
    
    # Запускаем бота и планировщик уведомлений параллельно
    logger.info("🚀 Бот запущен и готов к работе!")

    try:
        await asyncio.gather(
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
            olympiad_notification_scheduler(bot)
        )
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
