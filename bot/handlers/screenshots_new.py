from aiogram import Router, F, Bot
from aiogram.types import Message
from database.database import AsyncSessionLocal
from sqlalchemy import select, and_
import os
from datetime import datetime
from dotenv import load_dotenv

from database.models import Student, OlympiadSession, CodeRequest

load_dotenv()

router = Router()

SCREENSHOTS_FOLDER = os.getenv("SCREENSHOTS_FOLDER", "screenshots")
os.makedirs(SCREENSHOTS_FOLDER, exist_ok=True)


@router.message(F.photo)
async def handle_screenshot(message: Message, bot: Bot):
    """Обработка полученных фотографий (скриншотов)"""
    telegram_id = str(message.from_user.id)
    
    async with AsyncSessionLocal() as session:
        # Проверяем регистрацию
        result = await session.execute(
            select(Student).where(Student.telegram_id == telegram_id)
        )
        student = result.scalar_one_or_none()
        
        if not student or not student.is_registered:
            await message.answer(
                "❌ Ты не зарегистрирован!\n\n"
                "Используй /start для регистрации."
            )
            return
        
        # Получаем активные сессии
        result = await session.execute(
            select(OlympiadSession).where(OlympiadSession.is_active == True)
        )
        active_sessions = result.scalars().all()
        
        if not active_sessions:
            await message.answer(
                "❌ Сейчас нет активной олимпиады.\n\n"
                "Если ты хочешь отправить скриншот для прошлой олимпиады, "
                "обратись к преподавателю."
            )
            return
        
        # Находим запросы кодов для активных сессий
        session_ids = [s.id for s in active_sessions]
        
        result = await session.execute(
            select(CodeRequest).where(
                and_(
                    CodeRequest.student_id == student.id,
                    CodeRequest.session_id.in_(session_ids)
                )
            )
        )
        code_requests = result.scalars().all()
        
        if not code_requests:
            await message.answer(
                "❌ Ты еще не получал коды для текущих олимпиад!\n\n"
                "Используй /get_code для получения кода."
            )
            return
        
        # Если несколько запросов, обрабатываем каждый
        photo = message.photo[-1]  # Берем фото максимального размера
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        saved_screenshots = []
        
        for code_request in code_requests:
            # Получаем информацию о сессии
            result = await session.execute(
                select(OlympiadSession).where(OlympiadSession.id == code_request.session_id)
            )
            olympiad = result.scalar_one_or_none()
            
            if code_request.screenshot_submitted:
                # Уже был скриншот, обновляем
                status = "обновлен"
            else:
                status = "получен"
            
            # Генерируем имя файла
            filename = f"{student.id}_{olympiad.id}_{timestamp}.jpg"
            file_path = os.path.join(SCREENSHOTS_FOLDER, filename)
            
            # Скачиваем файл
            await bot.download(photo, destination=file_path)
            
            # Обновляем запись в БД
            code_request.screenshot_submitted = True
            code_request.screenshot_path = file_path
            code_request.screenshot_submitted_at = datetime.utcnow()
            
            saved_screenshots.append({
                "subject": olympiad.subject,
                "status": status
            })
        
        await session.commit()
        
        # Формируем ответ
        if len(saved_screenshots) == 1:
            await message.answer(
                f"✅ Скриншот {saved_screenshots[0]['status']} и сохранен!\n\n"
                f"Спасибо за выполнение работы по предмету {saved_screenshots[0]['subject']}.\n\n"
                f"Результаты будут объявлены после проверки."
            )
        else:
            subjects = ", ".join([s["subject"] for s in saved_screenshots])
            await message.answer(
                f"✅ Скриншот сохранен для следующих предметов:\n"
                f"{subjects}\n\n"
                f"Результаты будут объявлены после проверки."
            )


@router.message(F.document)
async def handle_document(message: Message):
    """Обработка документов (на случай если ученик отправит файл)"""
    await message.answer(
        "⚠️ Пожалуйста, отправь именно фото (не файлом).\n\n"
        "Просто выбери изображение из галереи или сделай фото камерой."
    )