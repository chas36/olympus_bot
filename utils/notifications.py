"""
Утилиты для отправки уведомлений администратору
"""

from aiogram import Bot
import os
import logging
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")


async def notify_admin_new_session(bot: Bot, subject: str, grade8_count: int, grade9_count: int):
    """
    Уведомление о создании новой сессии олимпиады
    """
    if not ADMIN_TELEGRAM_ID:
        return
    
    message = (
        f"📚 <b>Новая олимпиада загружена</b>\n\n"
        f"Предмет: {subject}\n"
        f"Кодов 8 класса: {grade8_count}\n"
        f"Кодов 9 класса: {grade9_count}\n\n"
        f"Олимпиада активирована и доступна ученикам."
    )
    
    try:
        await bot.send_message(ADMIN_TELEGRAM_ID, message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления администратору: {e}")


async def notify_admin_code_requested(bot: Bot, student_name: str, grade: int, subject: str):
    """
    Уведомление о запросе кода учеником
    """
    if not ADMIN_TELEGRAM_ID:
        return
    
    message = (
        f"🔑 <b>Код запрошен</b>\n\n"
        f"Ученик: {student_name}\n"
        f"Класс: {grade}\n"
        f"Предмет: {subject}"
    )
    
    try:
        await bot.send_message(ADMIN_TELEGRAM_ID, message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")


async def notify_admin_screenshot_received(bot: Bot, student_name: str, subject: str):
    """
    Уведомление о получении скриншота
    """
    if not ADMIN_TELEGRAM_ID:
        return
    
    message = (
        f"✅ <b>Скриншот получен</b>\n\n"
        f"Ученик: {student_name}\n"
        f"Предмет: {subject}"
    )
    
    try:
        await bot.send_message(ADMIN_TELEGRAM_ID, message, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка отправки уведомления: {e}")


async def notify_admin_daily_summary(
    bot: Bot,
    subject: str,
    total_students: int,
    requested_code: int,
    submitted_screenshots: int,
    missing_screenshots: int
):
    """
    Ежедневная сводка для администратора
    """
    if not ADMIN_TELEGRAM_ID:
        return
    
    percentage = (submitted_screenshots / requested_code * 100) if requested_code > 0 else 0
    
    message = (
        f"📊 <b>Ежедневная сводка</b>\n\n"
        f"Предмет: {subject}\n\n"
        f"👥 Всего учеников: {total_students}\n"
        f"🔑 Запросили код: {requested_code}\n"
        f"✅ Прислали скриншот: {submitted_screenshots}\n"
        f"❌ Не прислали: {missing_screenshots}\n"
        f"📈 Процент выполнения: {percentage:.1f}%\n\n"
    )
    
    if missing_screenshots > 0:
        message += f"⚠️ <b>{missing_screenshots} учеников</b> еще не прислали скриншот!"
    else:
        message += "🎉 Все ученики прислали скриншоты!"
    
    try:
        await bot.send_message(ADMIN_TELEGRAM_ID, message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка отправки сводки: {e}")


async def notify_admin_missing_screenshots(bot: Bot, students: List[Dict]):
    """
    Уведомление о учениках без скриншотов
    """
    if not ADMIN_TELEGRAM_ID or not students:
        return
    
    message = f"⚠️ <b>Ученики без скриншотов ({len(students)}):</b>\n\n"
    
    for student in students[:10]:  # Максимум 10 в одном сообщении
        message += f"• {student['full_name']} (класс {student['grade']})\n"
    
    if len(students) > 10:
        message += f"\n... и еще {len(students) - 10}"
    
    try:
        await bot.send_message(ADMIN_TELEGRAM_ID, message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка отправки списка: {e}")


async def notify_admin_student_registered(bot: Bot, student_name: str):
    """
    Уведомление о регистрации нового ученика
    """
    if not ADMIN_TELEGRAM_ID:
        return
    
    message = (
        f"👤 <b>Новая регистрация</b>\n\n"
        f"Ученик: {student_name}\n"
        f"Теперь может получать коды олимпиад."
    )
    
    try:
        await bot.send_message(ADMIN_TELEGRAM_ID, message, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка отправки уведомления: {e}")


async def notify_admin_error(bot: Bot, error_message: str, context: str = ""):
    """
    Уведомление об ошибке в системе
    """
    if not ADMIN_TELEGRAM_ID:
        return
    
    message = (
        f"❌ <b>Ошибка в системе</b>\n\n"
        f"{context}\n\n"
        f"<code>{error_message}</code>"
    )
    
    try:
        await bot.send_message(ADMIN_TELEGRAM_ID, message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления об ошибке: {e}")
