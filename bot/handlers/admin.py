"""
Хэндлеры для администраторов бота
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import AsyncSessionLocal
from database import crud
from bot.keyboards import get_admin_main_menu
import os
from loguru import logger

router = Router()

# Список ID администраторов (можно вынести в .env)
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Открыть админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к админ-панели")
        return

    await message.answer(
        "👤 Панель администратора\n\n"
        "Выберите действие:",
        reply_markup=get_admin_main_menu()
    )


@router.callback_query(F.data == "admin_menu")
async def show_admin_menu(callback: CallbackQuery):
    """Показать главное меню администратора"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа к админ-панели", show_alert=True)
        return

    await callback.message.edit_text(
        "👤 Панель администратора\n\n"
        "Выберите действие:",
        reply_markup=get_admin_main_menu()
    )


@router.callback_query(F.data == "admin_stats")
async def show_statistics(callback: CallbackQuery):
    """Показать статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        # Получаем статистику одним запросом вместо загрузки всех студентов
        student_stats = await crud.get_students_count_stats(session)
        all_sessions = await crud.get_all_sessions(session)
        active_session = await crud.get_active_session(session)

        stats_text = (
            "📊 Статистика системы\n\n"
            f"👥 Всего учеников: {student_stats['total']}\n"
            f"✅ Зарегистрированных: {student_stats['registered']}\n"
            f"❌ Не зарегистрированных: {student_stats['unregistered']}\n\n"
            f"🏆 Всего олимпиад: {len(all_sessions)}\n"
            f"🟢 Активных олимпиад: {1 if active_session else 0}\n"
        )

        if active_session:
            stats_text += f"\n📚 Активная олимпиада: {active_session.subject}"

    await callback.message.edit_text(
        stats_text,
        reply_markup=get_admin_main_menu()
    )


@router.callback_query(F.data == "admin_students")
async def show_students(callback: CallbackQuery):
    """Показать список учеников"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        # Получаем статистику одним запросом вместо N+1
        stats = await crud.get_classes_statistics(session)

        if not stats:
            await callback.message.edit_text(
                "📝 В базе данных пока нет учеников",
                reply_markup=get_admin_main_menu()
            )
            return

        text = "👥 Список классов:\n\n"
        for class_num, data in stats.items():
            text += f"{class_num} класс: {data['total']} учеников ({data['registered']} зарег.)\n"

    await callback.message.edit_text(
        text + "\n💡 Используйте API для управления учениками",
        reply_markup=get_admin_main_menu()
    )


@router.callback_query(F.data == "admin_upload")
async def show_upload_info(callback: CallbackQuery):
    """Показать информацию о загрузке файлов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "📤 Загрузка файлов\n\n"
        "Используйте API эндпоинты для загрузки:\n"
        "- POST /api/upload/csv - загрузка CSV\n"
        "- POST /api/upload/excel - загрузка Excel\n\n"
        "💡 Для работы с API используйте документацию на /docs",
        reply_markup=get_admin_main_menu()
    )


@router.callback_query(F.data == "admin_generate_codes")
async def show_codes_info(callback: CallbackQuery):
    """Показать информацию о генерации кодов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "🔑 Генерация кодов\n\n"
        "Используйте API эндпоинт:\n"
        "POST /api/admin/generate-codes?count=N\n\n"
        "Где N - количество кодов (от 1 до 100)\n\n"
        "💡 Для работы с API используйте документацию на /docs",
        reply_markup=get_admin_main_menu()
    )


@router.message(Command("clear_students"))
async def clear_students_command(message: Message):
    """Очистить базу данных учеников (с подтверждением)"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде")
        return

    await message.answer(
        "⚠️ ВНИМАНИЕ!\n\n"
        "Вы собираетесь удалить ВСЕХ учеников из базы данных.\n"
        "Это действие НЕОБРАТИМО!\n\n"
        "Для подтверждения используйте:\n"
        "DELETE /api/admin/students?confirm=DELETE_ALL\n\n"
        "Или используйте API для удаления отдельных учеников или классов."
    )


@router.message(Command("delete_olympiad"))
async def delete_olympiad_command(message: Message):
    """Удалить олимпиаду"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде")
        return

    async with AsyncSessionLocal() as session:
        sessions = await crud.get_all_sessions(session)

        if not sessions:
            await message.answer("📝 В базе данных нет олимпиад")
            return

        text = "🏆 Список олимпиад:\n\n"
        for s in sessions:
            status = "🟢 Активна" if s.is_active else "⚪ Неактивна"
            text += f"ID {s.id}: {s.subject} ({status})\n"
            text += f"  Дата: {s.date.strftime('%d.%m.%Y')}\n"
            text += f"  Класс: {s.class_number or 'Разные'}\n\n"

        text += "💡 Для удаления используйте:\n"
        text += "DELETE /api/admin/olympiads/{session_id}"

    await message.answer(text)


@router.message(Command("delete_class"))
async def delete_class_command(message: Message):
    """Удалить класс"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде")
        return

    async with AsyncSessionLocal() as session:
        # Получаем статистику одним запросом вместо N+1
        stats = await crud.get_classes_statistics(session)

        if not stats:
            await message.answer("📝 В базе данных нет классов")
            return

        text = "👥 Список классов:\n\n"
        for class_num, data in stats.items():
            text += f"{class_num} класс: {data['total']} учеников\n"

        text += "\n💡 Для удаления класса используйте:\n"
        text += "DELETE /api/admin/classes/{class_number}"

    await message.answer(text)


@router.callback_query(F.data == "admin_olympiads")
async def show_olympiads(callback: CallbackQuery):
    """Показать список олимпиад"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        sessions = await crud.get_all_sessions(session)

        if not sessions:
            await callback.message.edit_text(
                "📝 В базе данных нет олимпиад",
                reply_markup=get_admin_main_menu()
            )
            return

        text = "🏆 Список олимпиад:\n\n"
        for s in sessions:
            status = "🟢 Активна" if s.is_active else "⚪ Неактивна"
            text += f"ID {s.id}: {s.subject} ({status})\n"
            text += f"  Дата: {s.date.strftime('%d.%m.%Y')}\n"
            text += f"  Класс: {s.class_number or 'Разные'}\n\n"

        text += "💡 Для управления используйте API"

    await callback.message.edit_text(
        text,
        reply_markup=get_admin_main_menu()
    )


@router.callback_query(F.data == "admin_api_help")
async def show_api_help(callback: CallbackQuery):
    """Показать справку по API"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    help_text = """
📚 Справка по API администратора

🔹 Управление учениками:
• GET /api/admin/students
• DELETE /api/admin/students/{id}?force=true
• DELETE /api/admin/students?confirm=DELETE_ALL

🔹 Управление классами:
• GET /api/admin/classes
• GET /api/admin/classes/{class_number}/students
• DELETE /api/admin/classes/{class_number}

🔹 Управление олимпиадами:
• GET /api/admin/olympiads
• DELETE /api/admin/olympiads/{id}
• POST /api/admin/olympiads/{id}/activate

🔹 Другое:
• POST /api/admin/generate-codes?count=N
• GET /api/admin/export/students

💡 Полная документация: /docs
"""
    await callback.message.edit_text(
        help_text,
        reply_markup=get_admin_main_menu()
    )


@router.message(Command("api_help"))
async def api_help_command(message: Message):
    """Показать справку по API"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде")
        return

    help_text = """
📚 Справка по API администратора

🔹 Управление учениками:
• GET /api/admin/students - список всех учеников
• DELETE /api/admin/students/{id}?force=true - удалить ученика
• DELETE /api/admin/students?confirm=DELETE_ALL - удалить всех

🔹 Управление классами:
• GET /api/admin/classes - список классов
• GET /api/admin/classes/{class_number}/students - ученики класса
• DELETE /api/admin/classes/{class_number} - удалить класс

🔹 Управление олимпиадами:
• GET /api/admin/olympiads - список олимпиад
• DELETE /api/admin/olympiads/{id} - удалить олимпиаду
• POST /api/admin/olympiads/{id}/activate - активировать

🔹 Другое:
• POST /api/admin/generate-codes?count=N - генерация кодов
• GET /api/admin/export/students - экспорт в CSV

💡 Полная документация: /docs
"""
    await message.answer(help_text)
