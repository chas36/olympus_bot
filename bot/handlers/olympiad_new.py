from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.database import AsyncSessionLocal
from sqlalchemy import select, and_
from datetime import datetime

from database.models import (
    Student, OlympiadSession, OlympiadCode, CodeRequest, DistributionMode
)
from utils.code_distribution import CodeDistributor

router = Router()


class OlympiadStates(StatesGroup):
    """Состояния для получения кода олимпиады"""
    selecting_subject = State()  # Если несколько активных предметов


@router.message(Command("get_code"))
async def cmd_get_code(message: Message, state: FSMContext):
    """Команда для получения кода олимпиады"""
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
        
        # Проверяем наличие активных сессий
        result = await session.execute(
            select(OlympiadSession).where(OlympiadSession.is_active == True)
        )
        active_sessions = result.scalars().all()
        
        if not active_sessions:
            await message.answer(
                "❌ Сейчас нет активных олимпиад!\n\n"
                "Дождись, когда преподаватель загрузит задания."
            )
            return
        
        # Если несколько активных сессий, предлагаем выбрать
        if len(active_sessions) > 1:
            # TODO: Создать клавиатуру выбора предмета
            await message.answer(
                "📚 Доступные олимпиады:\n\n" +
                "\n".join([f"- {s.subject}" for s in active_sessions]) +
                "\n\nВыбери предмет:"
            )
            # Сохраняем сессии в состоянии
            await state.update_data(sessions=[s.id for s in active_sessions])
            await state.set_state(OlympiadStates.selecting_subject)
            return
        
        # Одна активная сессия
        olympiad = active_sessions[0]
        
        # Проверяем, не получал ли уже ученик код для этой сессии
        result = await session.execute(
            select(CodeRequest).where(
                and_(
                    CodeRequest.student_id == student.id,
                    CodeRequest.session_id == olympiad.id
                )
            )
        )
        existing_request = result.scalar_one_or_none()
        
        if existing_request:
            # Уже получал код
            code_result = await session.execute(
                select(OlympiadCode).where(OlympiadCode.id == existing_request.code_id)
            )
            code = code_result.scalar_one_or_none()
            
            screenshot_status = "✅ Прислан" if existing_request.screenshot_submitted else "❌ Не прислан"
            
            await message.answer(
                f"ℹ️ Ты уже получил код для олимпиады по предмету {olympiad.subject}!\n\n"
                f"Класс: {student.class_number}\n"
                f"Код: `{code.code if code else 'N/A'}`\n"
                f"Скриншот: {screenshot_status}\n\n"
                f"⚠️ Не забудь прислать скриншот завершенной работы!",
                parse_mode="Markdown"
            )
            return
        
        # Получаем код в зависимости от режима сессии
        if olympiad.distribution_mode == DistributionMode.PRE_DISTRIBUTED:
            # Код должен быть уже распределен
            result = await session.execute(
                select(OlympiadCode).where(
                    and_(
                        OlympiadCode.session_id == olympiad.id,
                        OlympiadCode.student_id == student.id,
                        OlympiadCode.class_number == student.class_number
                    )
                )
            )
            code = result.scalar_one_or_none()
            
            if not code:
                await message.answer(
                    "❌ Для тебя не найден код!\n\n"
                    "Обратись к преподавателю."
                )
                return
            
            # Помечаем код как выданный
            code.is_issued = True
            code.issued_at = datetime.utcnow()
            
        else:  # ON_DEMAND режим
            # Получаем код из пула
            code = await CodeDistributor.get_code_for_student_on_demand(
                session, student.id, olympiad.id
            )
            
            if not code:
                await message.answer(
                    "❌ К сожалению, все коды для твоего класса уже заняты!\n\n"
                    "Обратись к преподавателю."
                )
                return
            
            code.is_issued = True
            code.issued_at = datetime.utcnow()
        
        # Создаем запись о запросе кода
        code_request = CodeRequest(
            student_id=student.id,
            session_id=olympiad.id,
            code_id=code.id
        )
        session.add(code_request)
        
        await session.commit()
        
        # Отправляем код
        await message.answer(
            f"✅ Твой код для олимпиады по предмету {olympiad.subject}:\n\n"
            f"📋 Класс: {student.class_number}\n\n"
            f"⚠️ ВАЖНО: После завершения работы обязательно пришли в бот "
            f"скриншот или фотографию последней страницы!\n\n"
            f"💡 Просто отправь фото в этот чат."
        )
        
        # Второе сообщение - только код для удобного копирования
        await message.answer(
            f"🔑 <code>{code.code}</code>",
            parse_mode="HTML"
        )


@router.message(Command("my_status"))
async def cmd_my_status(message: Message):
    """Проверка статуса ученика"""
    telegram_id = str(message.from_user.id)
    
    async with AsyncSessionLocal() as session:
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
        
        # Получаем активную сессию
        result = await session.execute(
            select(OlympiadSession).where(OlympiadSession.is_active == True)
        )
        active_sessions = result.scalars().all()
        
        if not active_sessions:
            await message.answer(
                f"👤 {student.full_name}\n"
                f"📚 Класс: {student.class_number}\n"
                f"✅ Зарегистрирован\n\n"
                f"Сейчас нет активных олимпиад."
            )
            return
        
        # Проверяем статус для каждой активной сессии
        status_messages = [
            f"👤 {student.full_name}\n"
            f"📚 Класс: {student.class_number}\n"
            f"✅ Зарегистрирован\n"
        ]
        
        for olympiad in active_sessions:
            # Получаем запрос для этой сессии
            result = await session.execute(
                select(CodeRequest).where(
                    and_(
                        CodeRequest.student_id == student.id,
                        CodeRequest.session_id == olympiad.id
                    )
                )
            )
            code_request = result.scalar_one_or_none()
            
            if not code_request:
                status_messages.append(
                    f"\n📚 {olympiad.subject}:\n"
                    f"❌ Код еще не получен\n"
                    f"Используй /get_code"
                )
            else:
                # Получаем код
                result = await session.execute(
                    select(OlympiadCode).where(OlympiadCode.id == code_request.code_id)
                )
                code = result.scalar_one_or_none()
                
                screenshot_status = "✅ Прислан" if code_request.screenshot_submitted else "❌ Не прислан"
                
                status_messages.append(
                    f"\n📚 {olympiad.subject}:\n"
                    f"📸 Скриншот: {screenshot_status}\n"
                    f"🔑 Код: <code>{code.code if code else 'N/A'}</code>"
                )
                
                if not code_request.screenshot_submitted:
                    status_messages.append(
                        "⚠️ Не забудь прислать скриншот!"
                    )
        
        await message.answer(
            "\n".join(status_messages),
            parse_mode="HTML"
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Справка по командам"""
    telegram_id = str(message.from_user.id)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Student).where(Student.telegram_id == telegram_id)
        )
        student = result.scalar_one_or_none()
        
        if not student or not student.is_registered:
            await message.answer(
                "📖 Справка\n\n"
                "/start - Начать регистрацию\n"
                "/help - Показать эту справку"
            )
        else:
            await message.answer(
                "📖 Справка\n\n"
                "/get_code - Получить код для олимпиады\n"
                "/my_status - Проверить свой статус\n"
                "/help - Показать эту справку\n\n"
                "📸 Для отправки скриншота просто отправь фото в чат."
            )