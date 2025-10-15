"""
Утилиты для отправки уведомлений администратору
"""

from aiogram import Bot
import os
import logging
from dotenv import load_dotenv
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")


async def check_notifications_enabled(db: Session, student_id: Optional[int] = None) -> bool:
    """
    Проверка, включены ли уведомления глобально и для конкретного ученика

    Args:
        db: Сессия базы данных
        student_id: ID ученика (опционально)

    Returns:
        True если уведомления включены, False иначе
    """
    from database.models import NotificationSettings, Student

    # Проверяем глобальную настройку
    global_settings = db.query(NotificationSettings).first()
    if global_settings and not global_settings.notifications_enabled:
        return False

    # Если указан ученик, проверяем его настройки
    if student_id:
        student = db.query(Student).filter(Student.id == student_id).first()
        if student and not student.notifications_enabled:
            return False

    return True


async def notify_admin_new_session(bot: Bot, subject: str, grade8_count: int, grade9_count: int, db: Session = None):
    """
    Уведомление о создании новой сессии олимпиады
    """
    if not ADMIN_TELEGRAM_ID:
        return

    # Проверяем, включены ли уведомления
    if db and not await check_notifications_enabled(db):
        logger.info("Уведомления отключены глобально")
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


async def notify_admin_code_requested(bot: Bot, student_name: str, grade: int, subject: str, db: Session = None, student_id: int = None):
    """
    Уведомление о запросе кода учеником
    """
    if not ADMIN_TELEGRAM_ID:
        return

    # Проверяем, включены ли уведомления
    if db and not await check_notifications_enabled(db, student_id):
        logger.info(f"Уведомления отключены для ученика {student_id}")
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


async def notify_admin_screenshot_received(bot: Bot, student_name: str, subject: str, db: Session = None, student_id: int = None):
    """
    Уведомление о получении скриншота
    """
    if not ADMIN_TELEGRAM_ID:
        return

    # Проверяем, включены ли уведомления
    if db and not await check_notifications_enabled(db, student_id):
        logger.info(f"Уведомления отключены для ученика {student_id}")
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
    missing_screenshots: int,
    db: Session = None
):
    """
    Ежедневная сводка для администратора
    """
    if not ADMIN_TELEGRAM_ID:
        return

    # Проверяем, включены ли уведомления
    if db and not await check_notifications_enabled(db):
        logger.info("Уведомления отключены глобально")
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


async def notify_admin_missing_screenshots(bot: Bot, students: List[Dict], db: Session = None):
    """
    Уведомление о учениках без скриншотов
    """
    if not ADMIN_TELEGRAM_ID or not students:
        return

    # Проверяем, включены ли уведомления
    if db and not await check_notifications_enabled(db):
        logger.info("Уведомления отключены глобально")
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


async def notify_admin_student_registered(bot: Bot, student_name: str, db: Session = None, student_id: int = None):
    """
    Уведомление о регистрации нового ученика
    """
    if not ADMIN_TELEGRAM_ID:
        return

    # Проверяем, включены ли уведомления
    if db and not await check_notifications_enabled(db, student_id):
        logger.info(f"Уведомления отключены для ученика {student_id}")
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


async def notify_admin_error(bot: Bot, error_message: str, context: str = "", db: Session = None):
    """
    Уведомление об ошибке в системе
    """
    if not ADMIN_TELEGRAM_ID:
        return

    # Проверяем, включены ли уведомления
    if db and not await check_notifications_enabled(db):
        logger.info("Уведомления отключены глобально")
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
