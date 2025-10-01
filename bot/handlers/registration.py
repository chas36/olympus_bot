from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.database import AsyncSessionLocal
from database import crud
from utils.auth import validate_code_format

router = Router()


class RegistrationStates(StatesGroup):
    """Состояния процесса регистрации"""
    waiting_for_code = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    telegram_id = str(message.from_user.id)
    
    async with AsyncSessionLocal() as session:
        # Проверяем, зарегистрирован ли пользователь
        student = await crud.get_student_by_telegram_id(session, telegram_id)
        
        if student and student.is_registered:
            await message.answer(
                f"👋 Привет, {student.full_name}!\n\n"
                "Ты уже зарегистрирован в системе.\n\n"
                "Доступные команды:\n"
                "/get_code - Получить код для олимпиады\n"
                "/my_status - Проверить свой статус\n"
                "/help - Помощь"
            )
        else:
            await message.answer(
                "👋 Добро пожаловать в бот олимпиады!\n\n"
                "Для регистрации введи код, который ты получил от преподавателя.\n\n"
                "Формат кода: XXXX-XXXX-XXXX"
            )
            await state.set_state(RegistrationStates.waiting_for_code)


@router.message(RegistrationStates.waiting_for_code)
async def process_registration_code(message: Message, state: FSMContext):
    """Обработка регистрационного кода"""
    code = message.text.strip().upper()
    telegram_id = str(message.from_user.id)
    
    # Проверяем формат кода
    if not validate_code_format(code):
        await message.answer(
            "❌ Неверный формат кода!\n\n"
            "Код должен быть в формате: XXXX-XXXX-XXXX\n"
            "Попробуй еще раз."
        )
        return
    
    async with AsyncSessionLocal() as session:
        # Проверяем, существует ли ученик с таким кодом
        student = await crud.get_student_by_registration_code(session, code)
        
        if not student:
            await message.answer(
                "❌ Код не найден!\n\n"
                "Проверь правильность кода или обратись к преподавателю."
            )
            return
        
        # Проверяем, не зарегистрирован ли уже этот ученик
        if student.is_registered:
            await message.answer(
                "❌ Этот код уже был использован!\n\n"
                "Если это твой код, но ты потерял доступ к боту, "
                "обратись к преподавателю."
            )
            return
        
        # Проверяем, не зарегистрирован ли этот telegram_id под другим кодом
        existing_student = await crud.get_student_by_telegram_id(session, telegram_id)
        if existing_student:
            await message.answer(
                f"❌ Ты уже зарегистрирован как {existing_student.full_name}!\n\n"
                "Один Telegram аккаунт может использовать только один код."
            )
            return
        
        # Регистрируем ученика
        await crud.register_student(session, student.id, telegram_id)
        
        await message.answer(
            f"✅ Регистрация успешна!\n\n"
            f"Добро пожаловать, {student.full_name}!\n\n"
            f"Теперь ты можешь получать коды для олимпиад.\n\n"
            f"Доступные команды:\n"
            f"/get_code - Получить код для олимпиады\n"
            f"/my_status - Проверить свой статус\n"
            f"/help - Помощь"
        )
        
        # Очищаем состояние
        await state.clear()


@router.message(F.text == "/cancel")
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("Нечего отменять.")
        return
    
    await state.clear()
    await message.answer(
        "✅ Действие отменено.\n\n"
        "Напиши /start для начала."
    )
