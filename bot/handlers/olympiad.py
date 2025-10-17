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

        # Проверяем класс ученика
        if not student.class_number:
            await message.answer(
                "❌ Твой класс не указан в системе!\n\n"
                "Обратись к преподавателю."
            )
            return

        # Ищем ближайший доступный класс (каскадный поиск)
        # Начинаем с класса ученика и ищем вверх до 11 класса
        available_class = await crud.find_nearest_available_class(
            session, active_session.id, student.class_number
        )

        if not available_class:
            await message.answer(
                f"❌ Олимпиада по предмету {active_session.subject} недоступна.\n\n"
                f"Нет свободных кодов ни для одного класса."
            )
            return

        # Только для 8 класса показываем выбор между 8 и 9 классом (если оба доступны)
        if student.class_number == 8 and available_class == 8:
            # Сохраняем ID сессии в состоянии
            await state.update_data(session_id=active_session.id)

            # Проверяем доступность резервных кодов 9 класса для 8-классников
            class_parallel = f"8{student.parallel or ''}"
            available_reserve = await crud.count_available_reserve_codes_for_grade8(
                session, active_session.id, class_parallel
            )

            await message.answer(
                f"📚 {active_session.subject}\n\n"
                f"Выбери класс, который будешь писать:",
                reply_markup=get_grade_selection_keyboard(available_reserve > 0)
            )

            await state.set_state(OlympiadStates.selecting_grade)
        else:
            # Для остальных классов выдаем код доступного класса
            # available_class уже найден выше (может быть равен или старше класса ученика)

            # Сначала пробуем найти предварительно распределенный код (Вариант 1)
            olympiad_code = await crud.get_assigned_code_for_student(
                session, student.id, active_session.id, available_class
            )

            # Если нет распределенного - берем любой доступный (Вариант 2)
            if not olympiad_code:
                olympiad_code = await crud.get_available_code_for_class(
                    session, active_session.id, available_class
                )

            if not olympiad_code:
                await message.answer(
                    f"❌ Для тебя не найден код!\n\n"
                    f"Обратись к преподавателю."
                )
                return

            code = olympiad_code.code

            # Помечаем код как выданный
            await crud.mark_code_issued(session, olympiad_code.id, student.id)

            # Создаем запись о запросе кода
            await crud.create_code_request(
                session, student.id, active_session.id, available_class, code
            )

            # Формируем сообщение в зависимости от того, свой класс или старший
            if available_class == student.class_number:
                # Код для своего класса
                class_info = f"📋 Класс: {available_class}"
            else:
                # Код от старшего класса
                class_info = f"📋 Класс: {available_class} (для твоего класса кодов нет, выдан код старшего класса)"

            # Первое сообщение - информация
            await message.answer(
                f"✅ Твой код для олимпиады по предмету {active_session.subject}:\n\n"
                f"{class_info}\n\n"
                f"⚠️ ВАЖНО: После завершения работы обязательно пришли в бот "
                f"скриншот или фотографию последней страницы!\n\n"
                f"💡 Просто отправь фото в этот чат."
            )

            # Второе сообщение - только код для удобного копирования
            await message.answer(
                f"🔑 <code>{code}</code>",
                parse_mode="HTML"
            )


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
            # Получаем код для 8 класса
            # Сначала пробуем предварительно распределенный (Вариант 1)
            olympiad_code = await crud.get_assigned_code_for_student(
                session, student.id, session_id, 8
            )

            # Если нет - берем любой доступный (Вариант 2)
            if not olympiad_code:
                olympiad_code = await crud.get_available_code_for_class(
                    session, session_id, 8
                )

            if not olympiad_code:
                await callback.message.answer(
                    "❌ Для тебя не найден код 8 класса!\n\n"
                    "Обратись к преподавателю."
                )
                await callback.answer()
                await state.clear()
                return

            code = olympiad_code.code

            # Помечаем код как выданный
            await crud.mark_code_issued(session, olympiad_code.id, student.id)

        else:  # grade 9 - резервные коды из пула 9 класса
            # Получаем резервный код для параллели ученика
            class_parallel = f"8{student.parallel or ''}"
            reserve_code = await crud.get_available_reserve_code_for_grade8(
                session, session_id, class_parallel
            )

            if not reserve_code:
                await callback.message.answer(
                    "❌ К сожалению, все резервные коды для 9 класса уже заняты!\n\n"
                    "Ты можешь взять код для 8 класса."
                )
                await callback.answer()
                return

            code = reserve_code.code

            # Помечаем резервный код как использованный
            await crud.mark_reserve_code_used(session, reserve_code.id, student.id)
        
        # Создаем запись о запросе кода
        code_request = await crud.create_code_request(
            session, student.id, session_id, selected_grade, code
        )
        
        # Первое сообщение - информация
        await callback.message.answer(
            f"✅ Твой код для олимпиады по предмету {olympiad_session.subject}:\n\n"
            f"📋 Класс: {selected_grade}\n\n"
            f"⚠️ ВАЖНО: После завершения работы обязательно пришли в бот "
            f"скриншот или фотографию последней страницы!\n\n"
            f"💡 Просто отправь фото в этот чат."
        )
        
        # Второе сообщение - только код для удобного копирования
        await callback.message.answer(
            f"🔑 <code>{code}</code>",
            parse_mode="HTML"
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
                f"📸 Скриншот: {screenshot_status}\n\n"
                f"{'⚠️ Не забудь прислать скриншот завершенной работы!' if not code_request.screenshot_submitted else ''}\n"
                f"🔑 Твой код:\n\n"
            )
            
            # Отправляем код отдельным сообщением
            await message.answer(
                f"<code>{code_request.code}</code>",
                parse_mode="HTML"
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