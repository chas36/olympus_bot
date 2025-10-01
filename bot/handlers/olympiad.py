from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.database import AsyncSessionLocal
from database import crud
from bot.keyboards import get_grade_selection_keyboard

router = Router()


class OlympiadStates(StatesGroup):
    """Состояния для получения кода олимпиады"""
    selecting_grade = State()


@router.message(Command("get_code"))
async def cmd_get_code(message: Message, state: FSMContext):
    """Команда для получения кода олимпиады"""
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
        
        # Проверяем наличие активной сессии
        active_session = await crud.get_active_session(session)
        
        if not active_session:
            await message.answer(
                "❌ Сейчас нет активной олимпиады!\n\n"
                "Дождись, когда преподаватель загрузит задания."
            )
            return
        
        # Проверяем, не получал ли уже ученик код для этой сессии
        existing_request = await crud.get_code_request_for_student_in_session(
            session, student.id, active_session.id
        )
        
        if existing_request:
            screenshot_status = "✅ Прислан" if existing_request.screenshot_submitted else "❌ Не прислан"
            await message.answer(
                f"ℹ️ Ты уже получил код для олимпиады по предмету {active_session.subject}!\n\n"
                f"Класс: {existing_request.grade}\n"
                f"Код: `{existing_request.code}`\n"
                f"Скриншот: {screenshot_status}\n\n"
                f"⚠️ Не забудь прислать скриншот завершенной работы!",
                parse_mode="Markdown"
            )
            return
        
        # Сохраняем ID сессии в состоянии
        await state.update_data(session_id=active_session.id)
        
        # Проверяем доступность кодов 9 класса
        available_grade9 = await crud.count_available_grade9_codes(session, active_session.id)
        
        await message.answer(
            f"📚 {active_session.subject}\n\n"
            f"Выбери класс, который будешь писать:",
            reply_markup=get_grade_selection_keyboard(available_grade9 > 0)
        )
        
        await state.set_state(OlympiadStates.selecting_grade)


@router.callback_query(OlympiadStates.selecting_grade, F.data.in_(["grade_8", "grade_9"]))
async def process_grade_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора класса"""
    telegram_id = str(callback.from_user.id)
    selected_grade = 8 if callback.data == "grade_8" else 9
    
    async with AsyncSessionLocal() as session:
        # Получаем студента
        student = await crud.get_student_by_telegram_id(session, telegram_id)
        
        # Получаем данные из состояния
        data = await state.get_data()
        session_id = data.get("session_id")
        
        # Получаем сессию
        olympiad_session = await crud.get_session_by_id(session, session_id)
        
        if not olympiad_session:
            await callback.answer("❌ Сессия не найдена!", show_alert=True)
            await state.clear()
            return
        
        # Получаем код в зависимости от выбранного класса
        if selected_grade == 8:
            # Получаем именной код 8 класса
            grade8_code = await crud.get_grade8_code_for_student(
                session, student.id, session_id
            )
            
            if not grade8_code:
                await callback.message.answer(
                    "❌ Для тебя не найден код 8 класса!\n\n"
                    "Обратись к преподавателю."
                )
                await callback.answer()
                await state.clear()
                return
            
            code = grade8_code.code
            
            # Помечаем код как выданный
            await crud.mark_grade8_code_issued(session, grade8_code.id)
            
        else:  # grade 9
            # Получаем свободный код 9 класса
            grade9_code = await crud.get_available_grade9_code(session, session_id)
            
            if not grade9_code:
                await callback.message.answer(
                    "❌ К сожалению, все коды для 9 класса уже заняты!\n\n"
                    "Ты можешь взять код для 8 класса."
                )
                await callback.answer()
                return
            
            code = grade9_code.code
            
            # Присваиваем код ученику
            await crud.assign_grade9_code(session, grade9_code.id, student.id)
        
        # Создаем запись о запросе кода
        code_request = await crud.create_code_request(
            session, student.id, session_id, selected_grade, code
        )
        
        await callback.message.answer(
            f"✅ Твой код для олимпиады по предмету {olympiad_session.subject}:\n\n"
            f"📋 Класс: {selected_grade}\n"
            f"🔑 Код: `{code}`\n\n"
            f"⚠️ ВАЖНО: После завершения работы обязательно пришли в бот "
            f"скриншот или фотографию последней страницы!\n\n"
            f"💡 Просто отправь фото в этот чат.",
            parse_mode="Markdown"
        )
        
        await callback.answer("✅ Код получен!")
        await state.clear()


@router.message(Command("my_status"))
async def cmd_my_status(message: Message):
    """Проверка статуса ученика"""
    telegram_id = str(message.from_user.id)
    
    async with AsyncSessionLocal() as session:
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
                f"👤 {student.full_name}\n"
                f"✅ Зарегистрирован\n\n"
                f"Сейчас нет активных олимпиад."
            )
            return
        
        # Получаем запрос для текущей сессии
        code_request = await crud.get_code_request_for_student_in_session(
            session, student.id, active_session.id
        )
        
        if not code_request:
            await message.answer(
                f"👤 {student.full_name}\n"
                f"✅ Зарегистрирован\n\n"
                f"📚 Текущая олимпиада: {active_session.subject}\n"
                f"❌ Код еще не получен\n\n"
                f"Используй /get_code для получения кода."
            )
        else:
            screenshot_status = "✅ Прислан" if code_request.screenshot_submitted else "❌ Не прислан"
            
            await message.answer(
                f"👤 {student.full_name}\n"
                f"✅ Зарегистрирован\n\n"
                f"📚 Олимпиада: {active_session.subject}\n"
                f"📋 Класс: {code_request.grade}\n"
                f"🔑 Код: `{code_request.code}`\n"
                f"📸 Скриншот: {screenshot_status}\n\n"
                f"{'⚠️ Не забудь прислать скриншот завершенной работы!' if not code_request.screenshot_submitted else ''}",
                parse_mode="Markdown"
            )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Справка по командам"""
    telegram_id = str(message.from_user.id)
    
    async with AsyncSessionLocal() as session:
        student = await crud.get_student_by_telegram_id(session, telegram_id)
        
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
