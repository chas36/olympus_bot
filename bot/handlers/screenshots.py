from aiogram import Router, F, Bot
from aiogram.types import Message
from database.database import AsyncSessionLocal
from database import crud
import os
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

router = Router()

SCREENSHOTS_FOLDER = os.getenv("SCREENSHOTS_FOLDER", "screenshots")

# Создаем папку для скриншотов если её нет
os.makedirs(SCREENSHOTS_FOLDER, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """Очистка имени файла от недопустимых символов"""
    # Заменяем недопустимые символы на подчеркивание
    return re.sub(r'[<>:"/\\|?*]', '_', filename)


@router.message(F.photo)
async def handle_screenshot(message: Message, bot: Bot):
    """Обработка полученных фотографий (скриншотов)"""
    telegram_id = str(message.from_user.id)
    
    async with AsyncSessionLocal() as session:
        # Проверяем регистрацию
        student = await crud.get_student_by_telegram_id(session, telegram_id)
        
        if not student or not student.is_registered:
            await message.answer(
                "❌ Ты не зарегистрирован!\n\n"
                "Используй /start для регистрации."
            )
            return
        
        # Получаем активную сессию
        active_session = await crud.get_active_session(session)
        
        if not active_session:
            await message.answer(
                "❌ Сейчас нет активной олимпиады.\n\n"
                "Если ты хочешь отправить скриншот для прошлой олимпиады, "
                "обратись к преподавателю."
            )
            return
        
        # Проверяем, получал ли ученик код
        code_request = await crud.get_code_request_for_student_in_session(
            session, student.id, active_session.id
        )
        
        if not code_request:
            await message.answer(
                "❌ Ты еще не получал код для текущей олимпиады!\n\n"
                "Используй /get_code для получения кода."
            )
            return
        
        # Проверяем, не был ли уже прислан скриншот
        if code_request.screenshot_submitted:
            await message.answer(
                "ℹ️ Ты уже присылал скриншот для этой олимпиады.\n\n"
                "Если хочешь отправить новый, он перезапишет предыдущий."
            )
        
        # Скачиваем фото
        photo = message.photo[-1]  # Берем фото максимального размера

        # Генерируем структуру папок и имя файла
        # Формат: screenshots/предмет/класс_параллель/ФИО_дата_время.jpg
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Очищаем предмет от недопустимых символов
        subject_folder = sanitize_filename(active_session.subject)

        # Создаем папку для класса
        class_folder = f"{student.class_number}{student.parallel}" if student.parallel else str(student.class_number)

        # Очищаем ФИО от недопустимых символов
        student_name = sanitize_filename(student.full_name.replace(" ", "_"))

        # Создаем полную структуру папок
        full_folder = os.path.join(SCREENSHOTS_FOLDER, subject_folder, class_folder)
        os.makedirs(full_folder, exist_ok=True)

        # Формируем имя файла
        filename = f"{student_name}_{timestamp}.jpg"
        file_path = os.path.join(full_folder, filename)

        # Скачиваем файл
        await bot.download(photo, destination=file_path)

        # Обновляем запись в БД (сохраняем относительный путь от screenshots/)
        relative_path = os.path.join(subject_folder, class_folder, filename)
        await crud.mark_screenshot_submitted(session, code_request.id, relative_path)
        
        await message.answer(
            "✅ Скриншот получен и сохранен!\n\n"
            f"Спасибо за выполнение работы по предмету {active_session.subject}.\n\n"
            "Результаты будут объявлены после проверки."
        )


@router.message(F.document)
async def handle_document(message: Message):
    """Обработка документов (на случай если ученик отправит файл)"""
    await message.answer(
        "⚠️ Пожалуйста, отправь именно фото (не файлом).\n\n"
        "Просто выбери изображение из галереи или сделай фото камерой."
    )
