from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from database.database import AsyncSessionLocal
from database import crud
from loguru import logger


class RegistrationCheckMiddleware(BaseMiddleware):
    """
    Middleware для проверки регистрации пользователя
    Пропускает только команды /start и /help для незарегистрированных
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Список команд, доступных без регистрации
        public_commands = ['/start', '/help', '/cancel']
        
        # Проверяем, является ли сообщение командой из публичного списка
        if event.text and any(event.text.startswith(cmd) for cmd in public_commands):
            return await handler(event, data)
        
        # Для всех остальных команд проверяем регистрацию
        telegram_id = str(event.from_user.id)
        
        async with AsyncSessionLocal() as session:
            student = await crud.get_student_by_telegram_id(session, telegram_id)
            
            if not student or not student.is_registered:
                await event.answer(
                    "❌ Ты не зарегистрирован!\n\n"
                    "Используй /start для регистрации."
                )
                return
            
            # Добавляем студента в данные для использования в хендлере
            data['student'] = student
        
        return await handler(event, data)


class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования всех сообщений"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        
        # Логируем входящее сообщение
        logger.info(
            f"Message from {user.id} (@{user.username}): "
            f"{event.text[:50] if event.text else '[photo/file]'}"
        )
        
        try:
            result = await handler(event, data)
            return result
        except Exception as e:
            logger.error(f"Error handling message from {user.id}: {e}")
            await event.answer(
                "❌ Произошла ошибка при обработке запроса.\n"
                "Попробуй еще раз или обратись к администратору."
            )
            raise


class ThrottlingMiddleware(BaseMiddleware):
    """
    Middleware для ограничения частоты запросов
    Защита от спама
    """
    
    def __init__(self, rate_limit: int = 2):
        """
        Args:
            rate_limit: минимальное время между сообщениями (секунды)
        """
        self.rate_limit = rate_limit
        self.user_timestamps: Dict[int, float] = {}
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        import time
        
        user_id = event.from_user.id
        current_time = time.time()
        
        # Проверяем последнее время обращения
        if user_id in self.user_timestamps:
            time_passed = current_time - self.user_timestamps[user_id]
            
            if time_passed < self.rate_limit:
                # Слишком быстро
                await event.answer(
                    "⏰ Пожалуйста, подожди немного перед следующим запросом."
                )
                return
        
        # Обновляем время последнего обращения
        self.user_timestamps[user_id] = current_time
        
        return await handler(event, data)
