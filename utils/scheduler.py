"""
Планировщик задач для отложенных уведомлений
"""

import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
from database.database import SessionLocal
from database.models import OlympiadSession, MOSCOW_TZ, moscow_now
from utils.notifications import notify_students_olympiad_activated
import logging

logger = logging.getLogger(__name__)


async def send_pending_olympiad_notifications(bot: Bot):
    """
    Проверяет и отправляет отложенные уведомления об олимпиадах

    Вызывается планировщиком каждую минуту после 9:00
    """
    db = SessionLocal()
    try:
        current_time = moscow_now()

        # Находим сессии с запланированными уведомлениями
        sessions = db.query(OlympiadSession).filter(
            OlympiadSession.notification_sent == False,
            OlympiadSession.notification_scheduled_for.isnot(None),
            OlympiadSession.notification_scheduled_for <= current_time,
            OlympiadSession.is_active == True
        ).all()

        for session in sessions:
            try:
                logger.info(f"Отправка отложенного уведомления для олимпиады: {session.subject}")
                await notify_students_olympiad_activated(
                    bot=bot,
                    session_id=session.id,
                    subject=session.subject,
                    date=session.date.isoformat() if session.date else "",
                    db=db
                )
                logger.info(f"Отложенное уведомление отправлено для олимпиады: {session.subject}")
            except Exception as e:
                logger.error(f"Ошибка отправки отложенного уведомления для олимпиады {session.subject}: {e}")

    except Exception as e:
        logger.error(f"Ошибка в send_pending_olympiad_notifications: {e}")
    finally:
        db.close()


def should_delay_notification() -> tuple[bool, datetime]:
    """
    Проверяет, нужно ли отложить уведомление до 9:00

    Returns:
        (should_delay, scheduled_time):
            - should_delay: True если нужно отложить
            - scheduled_time: время когда нужно отправить (если отложено)
    """
    current_time = moscow_now()
    current_hour = current_time.hour

    # Если текущее время меньше 9:00, откладываем до 9:00 сегодня
    if current_hour < 9:
        scheduled_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
        return (True, scheduled_time)

    # Если уже 9:00 или позже, отправляем сразу
    return (False, current_time)
