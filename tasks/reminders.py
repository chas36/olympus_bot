from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, time
import pytz
from database.database import AsyncSessionLocal
from database import crud
from aiogram import Bot
import os
from dotenv import load_dotenv

load_dotenv()

TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "Europe/Moscow"))
REMINDER_END_TIME = os.getenv("REMINDER_END_TIME", "21:30")
REMINDER_INTERVAL_MINUTES = int(os.getenv("REMINDER_INTERVAL_MINUTES", "30"))


async def send_screenshot_reminders(bot: Bot):
    """
    Отправляет напоминания ученикам, которые не прислали скриншоты
    """
    current_time = datetime.now(TIMEZONE)
    end_hour, end_minute = map(int, REMINDER_END_TIME.split(":"))
    end_time = time(end_hour, end_minute)
    
    # Проверяем, не позднее ли указанного времени
    if current_time.time() > end_time:
        print(f"⏰ Время {current_time.time()} позже {end_time}, напоминания не отправляются")
        return
    
    async with AsyncSessionLocal() as session:
        # Получаем активную сессию
        active_session = await crud.get_active_session(session)
        
        if not active_session:
            print("ℹ️ Нет активной сессии, напоминания не отправляются")
            return
        
        # Получаем запросы без скриншотов
        requests_without_screenshot = await crud.get_requests_without_screenshot(
            session, active_session.id
        )
        
        if not requests_without_screenshot:
            print("✅ Все ученики прислали скриншоты")
            return
        
        print(f"📤 Отправка напоминаний {len(requests_without_screenshot)} ученикам...")
        
        for request in requests_without_screenshot:
            student = request.student
            
            if not student.telegram_id:
                continue
            
            try:
                # Отправляем напоминание
                await bot.send_message(
                    chat_id=student.telegram_id,
                    text=(
                        f"⏰ Напоминание!\n\n"
                        f"Ты получил код для олимпиады по предмету {active_session.subject}, "
                        f"но еще не прислал скриншот завершенной работы.\n\n"
                        f"📸 Пожалуйста, отправь фото или скриншот последней страницы "
                        f"в этот чат до {REMINDER_END_TIME}.\n\n"
                        f"Это важно для подтверждения выполнения работы!"
                    )
                )
                
                # Записываем напоминание в БД
                await crud.create_reminder(session, request.id, "screenshot")
                
                print(f"✅ Напоминание отправлено: {student.full_name}")
                
            except Exception as e:
                print(f"❌ Ошибка отправки напоминания {student.full_name}: {e}")
        
        print(f"✅ Напоминания отправлены")


def setup_reminder_scheduler(bot: Bot) -> AsyncIOScheduler:
    """
    Настраивает планировщик напоминаний
    
    Args:
        bot: экземпляр бота
        
    Returns:
        Настроенный планировщик
    """
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    
    # Парсим время окончания напоминаний
    end_hour, end_minute = map(int, REMINDER_END_TIME.split(":"))
    
    # Добавляем задачу на отправку напоминаний каждые N минут
    # Напоминания работают с 9:00 до указанного времени (по умолчанию 21:30)
    scheduler.add_job(
        send_screenshot_reminders,
        'interval',
        minutes=REMINDER_INTERVAL_MINUTES,
        start_date=datetime.now(TIMEZONE).replace(hour=9, minute=0, second=0),
        end_date=datetime.now(TIMEZONE).replace(hour=end_hour, minute=end_minute, second=0),
        args=[bot],
        id='screenshot_reminders',
        replace_existing=True
    )
    
    print(f"⏰ Планировщик напоминаний настроен:")
    print(f"   - Интервал: каждые {REMINDER_INTERVAL_MINUTES} минут")
    print(f"   - Окончание: {REMINDER_END_TIME}")
    print(f"   - Часовой пояс: {TIMEZONE}")
    
    return scheduler


async def send_immediate_reminder_to_student(bot: Bot, telegram_id: str, subject: str):
    """
    Отправляет немедленное напоминание конкретному ученику
    
    Args:
        bot: экземпляр бота
        telegram_id: Telegram ID ученика
        subject: предмет олимпиады
    """
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=(
                f"⏰ Напоминание!\n\n"
                f"Не забудь прислать скриншот завершенной работы по предмету {subject}!\n\n"
                f"📸 Просто отправь фото в этот чат."
            )
        )
        print(f"✅ Немедленное напоминание отправлено: {telegram_id}")
    except Exception as e:
        print(f"❌ Ошибка отправки напоминания: {e}")
