"""
Обработчики команд для авторизации через Telegram бота
"""

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import os
import requests

from database.database import SessionLocal
from database.models import User, AuthToken, moscow_now

logger = logging.getLogger(__name__)

router = Router()

ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")
API_URL = os.getenv("API_URL", "http://localhost:8001")


# FSM для добавления пользователя
class AddUserForm(StatesGroup):
    waiting_for_telegram_id = State()
    waiting_for_role = State()


def get_db():
    """Получение сессии БД"""
    return SessionLocal()


def is_admin(telegram_id: str) -> bool:
    """Проверка, является ли пользователь администратором"""
    return str(telegram_id) == str(ADMIN_TELEGRAM_ID)


@router.message(CommandStart(deep_link=True))
async def handle_auth_deeplink(message: Message):
    """
    Обработка deep link для авторизации: /start auth_<token>
    """
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return

    deep_link_arg = args[1]

    # Проверяем, является ли это токеном авторизации
    if not deep_link_arg.startswith("auth_"):
        return

    token = deep_link_arg[5:]  # Убираем префикс "auth_"

    db = get_db()
    try:
        # Находим токен в БД
        auth_token = db.query(AuthToken).filter(
            AuthToken.token == token,
            AuthToken.is_used == False,
            AuthToken.expires_at > moscow_now()
        ).first()

        if not auth_token:
            await message.answer(
                "❌ <b>Ошибка авторизации</b>\n\n"
                "Токен недействителен или истек. Попробуйте получить новую ссылку.",
                parse_mode="HTML"
            )
            return

        # Получаем пользователя
        user = db.query(User).filter(User.id == auth_token.user_id).first()

        if not user or not user.is_active:
            await message.answer(
                "❌ <b>Ошибка авторизации</b>\n\n"
                "Ваш аккаунт не активен. Обратитесь к администратору.",
                parse_mode="HTML"
            )
            return

        # Проверяем, что токен принадлежит этому пользователю
        if user.telegram_id != str(message.from_user.id):
            await message.answer(
                "❌ <b>Ошибка авторизации</b>\n\n"
                "Эта ссылка предназначена для другого пользователя.",
                parse_mode="HTML"
            )
            return

        # Помечаем токен как использованный и отправляем запрос в API
        try:
            response = requests.post(
                f"{API_URL}/api/auth/verify",
                json={"token": token},
                timeout=10
            )

            if response.status_code == 200:
                await message.answer(
                    "✅ <b>Авторизация успешна!</b>\n\n"
                    "Вы можете вернуться в браузер и продолжить работу с панелью управления.\n\n"
                    f"Ваша роль: <b>{user.role}</b>",
                    parse_mode="HTML"
                )
                logger.info(f"Пользователь {user.telegram_id} успешно авторизовался")
            else:
                await message.answer(
                    "❌ <b>Ошибка при создании сессии</b>\n\n"
                    "Попробуйте еще раз или обратитесь к администратору.",
                    parse_mode="HTML"
                )
                logger.error(f"Ошибка API при авторизации: {response.status_code} - {response.text}")

        except Exception as e:
            await message.answer(
                "❌ <b>Ошибка связи с сервером</b>\n\n"
                "Попробуйте еще раз позже.",
                parse_mode="HTML"
            )
            logger.error(f"Ошибка при вызове API авторизации: {e}")

    finally:
        db.close()


# ============================================
# Команды администратора для управления пользователями
# ============================================

@router.message(Command("adduser"))
async def cmd_adduser(message: Message, state: FSMContext):
    """
    Команда для добавления нового пользователя (только для администратора)
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен. Эта команда доступна только администратору.")
        return

    await message.answer(
        "👤 <b>Добавление нового пользователя</b>\n\n"
        "Отправьте Telegram ID пользователя (цифры):",
        parse_mode="HTML"
    )
    await state.set_state(AddUserForm.waiting_for_telegram_id)


@router.message(AddUserForm.waiting_for_telegram_id)
async def process_telegram_id(message: Message, state: FSMContext):
    """Обработка Telegram ID"""
    telegram_id = message.text.strip()

    if not telegram_id.isdigit():
        await message.answer("❌ Неверный формат. Telegram ID должен состоять только из цифр. Попробуйте еще раз:")
        return

    # Сохраняем telegram_id
    await state.update_data(telegram_id=telegram_id)

    await message.answer(
        "📋 <b>Выберите роль пользователя:</b>\n\n"
        "1. <code>admin</code> - полный доступ\n"
        "2. <code>teacher</code> - управление олимпиадами\n"
        "3. <code>viewer</code> - только просмотр\n\n"
        "Отправьте название роли:",
        parse_mode="HTML"
    )
    await state.set_state(AddUserForm.waiting_for_role)


@router.message(AddUserForm.waiting_for_role)
async def process_role(message: Message, state: FSMContext):
    """Обработка роли пользователя"""
    role = message.text.strip().lower()

    valid_roles = ["admin", "teacher", "viewer"]
    if role not in valid_roles:
        await message.answer(
            f"❌ Неверная роль. Допустимые роли: {', '.join(valid_roles)}\n\n"
            "Попробуйте еще раз:"
        )
        return

    # Получаем данные из state
    data = await state.get_data()
    telegram_id = data.get("telegram_id")

    db = get_db()
    try:
        # Проверяем, существует ли пользователь
        existing_user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if existing_user:
            await message.answer(
                f"❌ Пользователь с Telegram ID {telegram_id} уже существует.\n\n"
                f"Текущая роль: <b>{existing_user.role}</b>",
                parse_mode="HTML"
            )
            await state.clear()
            return

        # Создаем нового пользователя
        new_user = User(
            telegram_id=telegram_id,
            role=role,
            is_active=True
        )
        db.add(new_user)
        db.commit()

        await message.answer(
            "✅ <b>Пользователь успешно добавлен!</b>\n\n"
            f"Telegram ID: <code>{telegram_id}</code>\n"
            f"Роль: <b>{role}</b>\n\n"
            "Пользователь теперь может авторизоваться в панели управления.",
            parse_mode="HTML"
        )
        logger.info(f"Администратор добавил нового пользователя: {telegram_id} (роль: {role})")

    except Exception as e:
        await message.answer(
            f"❌ Ошибка при добавлении пользователя: {e}",
            parse_mode="HTML"
        )
        logger.error(f"Ошибка при добавлении пользователя: {e}")

    finally:
        db.close()
        await state.clear()


@router.message(Command("listusers"))
async def cmd_listusers(message: Message):
    """
    Команда для просмотра списка пользователей (только для администратора)
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен. Эта команда доступна только администратору.")
        return

    db = get_db()
    try:
        users = db.query(User).all()

        if not users:
            await message.answer("📋 Список пользователей пуст.")
            return

        response = "📋 <b>Список пользователей:</b>\n\n"

        for user in users:
            status = "✅" if user.is_active else "❌"
            response += (
                f"{status} <b>ID {user.id}</b>\n"
                f"   Telegram ID: <code>{user.telegram_id}</code>\n"
                f"   Роль: <b>{user.role}</b>\n"
            )

            if user.username:
                response += f"   Username: @{user.username}\n"
            if user.full_name:
                response += f"   Имя: {user.full_name}\n"
            if user.last_login:
                response += f"   Последний вход: {user.last_login.strftime('%d.%m.%Y %H:%M')}\n"

            response += "\n"

        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        logger.error(f"Ошибка при получении списка пользователей: {e}")

    finally:
        db.close()


@router.message(Command("deluser"))
async def cmd_deluser(message: Message):
    """
    Команда для удаления пользователя (только для администратора)
    Формат: /deluser <telegram_id>
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен. Эта команда доступна только администратору.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Неверный формат команды.\n\n"
            "Использование: /deluser <telegram_id>",
            parse_mode="HTML"
        )
        return

    telegram_id = args[1].strip()

    if not telegram_id.isdigit():
        await message.answer("❌ Telegram ID должен состоять только из цифр.")
        return

    db = get_db()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            await message.answer(f"❌ Пользователь с Telegram ID {telegram_id} не найден.")
            return

        # Удаляем пользователя
        db.delete(user)
        db.commit()

        await message.answer(
            f"✅ Пользователь удален.\n\n"
            f"Telegram ID: <code>{telegram_id}</code>\n"
            f"Роль: <b>{user.role}</b>",
            parse_mode="HTML"
        )
        logger.info(f"Администратор удалил пользователя: {telegram_id}")

    except Exception as e:
        await message.answer(f"❌ Ошибка при удалении пользователя: {e}")
        logger.error(f"Ошибка при удалении пользователя: {e}")

    finally:
        db.close()


@router.message(Command("setactive"))
async def cmd_setactive(message: Message):
    """
    Команда для активации/деактивации пользователя
    Формат: /setactive <telegram_id> <true/false>
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен. Эта команда доступна только администратору.")
        return

    args = message.text.split()
    if len(args) < 3:
        await message.answer(
            "❌ Неверный формат команды.\n\n"
            "Использование: /setactive <telegram_id> <true/false>",
            parse_mode="HTML"
        )
        return

    telegram_id = args[1].strip()
    is_active_str = args[2].strip().lower()

    if not telegram_id.isdigit():
        await message.answer("❌ Telegram ID должен состоять только из цифр.")
        return

    if is_active_str not in ["true", "false"]:
        await message.answer("❌ Параметр должен быть true или false.")
        return

    is_active = is_active_str == "true"

    db = get_db()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            await message.answer(f"❌ Пользователь с Telegram ID {telegram_id} не найден.")
            return

        user.is_active = is_active
        db.commit()

        status = "активирован" if is_active else "деактивирован"
        await message.answer(
            f"✅ Пользователь {status}.\n\n"
            f"Telegram ID: <code>{telegram_id}</code>\n"
            f"Роль: <b>{user.role}</b>",
            parse_mode="HTML"
        )
        logger.info(f"Администратор изменил статус пользователя {telegram_id} на {is_active}")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        logger.error(f"Ошибка при изменении статуса пользователя: {e}")

    finally:
        db.close()
