"""
Модуль для отправки уведомлений администраторам
"""
from aiogram import Bot
from loguru import logger
import os


async def notify_admins(bot: Bot, message: str, parse_mode: str = "HTML"):
    """
    Отправляет уведомление всем администраторам

    Args:
        bot: Экземпляр бота
        message: Текст сообщения
        parse_mode: Режим парсинга (HTML или Markdown)
    """
    admin_ids = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

    if not admin_ids:
        logger.warning("No admin IDs configured for notifications")
        return

    for admin_id in admin_ids:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=message,
                parse_mode=parse_mode
            )
        except Exception as e:
            logger.error(f"Failed to send notification to admin {admin_id}: {e}")


async def notify_new_registration(bot: Bot, student_name: str, telegram_id: int):
    """Уведомление о новой регистрации ученика"""
    message = (
        "🆕 <b>Новая регистрация!</b>\n\n"
        f"Ученик: {student_name}\n"
        f"Telegram ID: {telegram_id}"
    )
    await notify_admins(bot, message)


async def notify_code_request(bot: Bot, student_name: str, grade: int, subject: str):
    """Уведомление о запросе кода"""
    message = (
        "🔑 <b>Запрос кода</b>\n\n"
        f"Ученик: {student_name}\n"
        f"Класс: {grade}\n"
        f"Предмет: {subject}"
    )
    await notify_admins(bot, message)


async def notify_screenshot_submitted(bot: Bot, student_name: str, subject: str):
    """Уведомление о загрузке скриншота"""
    message = (
        "📸 <b>Новый скриншот</b>\n\n"
        f"Ученик: {student_name}\n"
        f"Предмет: {subject}"
    )
    await notify_admins(bot, message)


async def notify_olympiad_uploaded(bot: Bot, subject: str, class_number: int, codes_count: int):
    """Уведомление о загрузке новой олимпиады"""
    message = (
        "📤 <b>Загружена новая олимпиада</b>\n\n"
        f"Предмет: {subject}\n"
        f"Класс: {class_number or 'Разные'}\n"
        f"Кодов загружено: {codes_count}"
    )
    await notify_admins(bot, message)


async def notify_low_codes(bot: Bot, subject: str, remaining_codes: int):
    """Уведомление о малом количестве кодов"""
    message = (
        "⚠️ <b>Мало кодов!</b>\n\n"
        f"Предмет: {subject}\n"
        f"Осталось кодов: {remaining_codes}\n\n"
        "Рекомендуется загрузить дополнительные коды."
    )
    await notify_admins(bot, message)


async def notify_system_event(bot: Bot, event: str, details: str = None):
    """Уведомление о системном событии"""
    message = f"ℹ️ <b>Системное событие</b>\n\n{event}"

    if details:
        message += f"\n\n{details}"

    await notify_admins(bot, message)
