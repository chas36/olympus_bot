"""
Расширенные хэндлеры для администраторов - управление через бот
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.database import AsyncSessionLocal
from database import crud
from bot.keyboards import (
    get_students_management_menu, get_classes_management_menu,
    get_olympiads_management_menu, get_export_menu, get_admin_main_menu,
    get_back_button, get_confirm_keyboard, get_class_selection_keyboard,
    get_olympiad_selection_keyboard
)
from utils.admin_logger import AdminActionLogger
from utils.admin_notifications import notify_system_event
from utils.excel_export import ExcelExporter
import os
from loguru import logger

router = Router()

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    waiting_for_student_id = State()
    waiting_for_class_number = State()
    waiting_for_olympiad_id = State()


# ==================== МЕНЮ УПРАВЛЕНИЯ ====================

@router.callback_query(F.data == "admin_students_menu")
async def show_students_menu(callback: CallbackQuery):
    """Показать меню управления учениками"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "👥 <b>Управление учениками</b>\n\n"
        "Выберите действие:",
        reply_markup=get_students_management_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_classes_menu")
async def show_classes_menu(callback: CallbackQuery):
    """Показать меню управления классами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "🎓 <b>Управление классами</b>\n\n"
        "Выберите действие:",
        reply_markup=get_classes_management_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_olympiads_menu")
async def show_olympiads_menu(callback: CallbackQuery):
    """Показать меню управления олимпиадами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "🏆 <b>Управление олимпиадами</b>\n\n"
        "Выберите действие:",
        reply_markup=get_olympiads_management_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_export_menu")
async def show_export_menu(callback: CallbackQuery):
    """Показать меню экспорта"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "📥 <b>Экспорт данных</b>\n\n"
        "Выберите формат экспорта:",
        reply_markup=get_export_menu(),
        parse_mode="HTML"
    )


# ==================== УЧЕНИКИ ====================

@router.callback_query(F.data == "admin_students_list")
async def show_all_students(callback: CallbackQuery):
    """Показать всех учеников"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        students = await crud.get_all_students(session)

        if not students:
            await callback.message.edit_text(
                "📝 В базе данных нет учеников",
                reply_markup=get_students_management_menu()
            )
            return

        # Показываем первые 20
        text = f"👥 <b>Всего учеников: {len(students)}</b>\n\n"

        for student in students[:20]:
            status = "✅" if student.is_registered else "❌"
            class_info = f"{student.class_number}{student.parallel or ''}" if student.class_number else "Не указан"
            text += f"{status} <b>{student.full_name}</b> ({class_info} кл.)\n"
            text += f"   ID: {student.id} | Код: {student.registration_code}\n\n"

        if len(students) > 20:
            text += f"\n... и еще {len(students) - 20} учеников"

    AdminActionLogger.log_action(
        callback.from_user.id,
        callback.from_user.full_name,
        "view_students_list",
        {"total": len(students)}
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_students_management_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_students_registered")
async def show_registered_students(callback: CallbackQuery):
    """Показать зарегистрированных учеников"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        # Получаем только зарегистрированных студентов напрямую из БД
        students = await crud.get_registered_students(session)

        if not students:
            await callback.message.edit_text(
                "📝 Нет зарегистрированных учеников",
                reply_markup=get_students_management_menu()
            )
            return

        text = f"✅ <b>Зарегистрированных: {len(students)}</b>\n\n"

        for student in students[:20]:
            class_info = f"{student.class_number}{student.parallel or ''}" if student.class_number else "Не указан"
            text += f"<b>{student.full_name}</b> ({class_info} кл.)\n"
            text += f"   TG ID: {student.telegram_id}\n\n"

        if len(students) > 20:
            text += f"\n... и еще {len(students) - 20} учеников"

    await callback.message.edit_text(
        text,
        reply_markup=get_students_management_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_students_unregistered")
async def show_unregistered_students(callback: CallbackQuery):
    """Показать незарегистрированных учеников"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        # Получаем только незарегистрированных студентов напрямую из БД
        students = await crud.get_unregistered_students(session)

        if not students:
            await callback.message.edit_text(
                "📝 Все ученики зарегистрированы!",
                reply_markup=get_students_management_menu()
            )
            return

        text = f"❌ <b>Не зарегистрированных: {len(students)}</b>\n\n"

        for student in students[:20]:
            class_info = f"{student.class_number}{student.parallel or ''}" if student.class_number else "Не указан"
            text += f"<b>{student.full_name}</b> ({class_info} кл.)\n"
            text += f"   Код: <code>{student.registration_code}</code>\n\n"

        if len(students) > 20:
            text += f"\n... и еще {len(students) - 20} учеников"

    await callback.message.edit_text(
        text,
        reply_markup=get_students_management_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_students_search")
async def search_student_prompt(callback: CallbackQuery, state: FSMContext):
    """Запрос ID ученика для поиска"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "🔍 <b>Поиск ученика</b>\n\n"
        "Введите ID ученика или его ФИО:",
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )

    await state.set_state(AdminStates.waiting_for_student_id)


@router.callback_query(F.data == "admin_students_delete")
async def delete_student_prompt(callback: CallbackQuery, state: FSMContext):
    """Запрос ID ученика для удаления"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "🗑 <b>Удаление ученика</b>\n\n"
        "Введите ID ученика для удаления:\n"
        "(Узнать ID можно в списке учеников)",
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )

    await state.set_state(AdminStates.waiting_for_student_id)


@router.callback_query(F.data == "admin_students_clear_all")
async def confirm_clear_all_students(callback: CallbackQuery):
    """Подтверждение очистки всех учеников"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        # Подсчитываем студентов без их загрузки
        count = await crud.count_all_students(session)

    await callback.message.edit_text(
        f"⚠️ <b>ВНИМАНИЕ!</b>\n\n"
        f"Вы собираетесь удалить ВСЕХ учеников ({count} чел.)\n"
        f"Это действие НЕОБРАТИМО!\n\n"
        f"Подтвердите действие:",
        reply_markup=get_confirm_keyboard("clear_all_students"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "confirm_clear_all_students")
async def execute_clear_all_students(callback: CallbackQuery):
    """Выполнить очистку всех учеников"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        count = await crud.clear_all_students(session)

    AdminActionLogger.log_action(
        callback.from_user.id,
        callback.from_user.full_name,
        "clear_all_students",
        {"deleted_count": count}
    )

    await callback.message.edit_text(
        f"✅ <b>Готово!</b>\n\n"
        f"Удалено учеников: {count}",
        reply_markup=get_admin_main_menu(),
        parse_mode="HTML"
    )

    # Уведомляем других админов
    from aiogram import Bot
    bot = callback.bot
    await notify_system_event(
        bot,
        f"Администратор {callback.from_user.full_name} удалил всех учеников ({count} чел.)"
    )


# ==================== КЛАССЫ ====================

@router.callback_query(F.data == "admin_classes_list")
async def show_classes_list(callback: CallbackQuery):
    """Показать список классов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        # Получаем статистику одним запросом вместо N+1
        stats = await crud.get_classes_statistics(session)

        if not stats:
            await callback.message.edit_text(
                "📝 В базе данных нет классов",
                reply_markup=get_classes_management_menu()
            )
            return

        text = "🎓 <b>Список классов:</b>\n\n"

        for class_num, data in stats.items():
            text += f"<b>{class_num} класс:</b> {data['total']} уч. ({data['registered']} зарег.)\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_classes_management_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_classes_students")
async def show_class_students_selection(callback: CallbackQuery):
    """Выбор класса для просмотра учеников"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        classes = await crud.get_all_classes(session)

        if not classes:
            await callback.message.edit_text(
                "📝 В базе данных нет классов",
                reply_markup=get_classes_management_menu()
            )
            return

    await callback.message.edit_text(
        "👥 <b>Ученики по классам</b>\n\n"
        "Выберите класс:",
        reply_markup=get_class_selection_keyboard(classes),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("select_class_"))
async def show_class_students(callback: CallbackQuery):
    """Показать учеников выбранного класса"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    class_number = int(callback.data.split("_")[2])

    async with AsyncSessionLocal() as session:
        students = await crud.get_students_by_class(session, class_number)

        if not students:
            await callback.answer(f"В {class_number} классе нет учеников", show_alert=True)
            return

        text = f"👥 <b>{class_number} класс ({len(students)} уч.)</b>\n\n"

        # Показываем первые 30 учеников
        for student in students[:30]:
            status = "✅" if student.is_registered else "❌"
            text += f"{status} <b>{student.full_name}</b>\n"

            if student.is_registered:
                text += f"   TG ID: {student.telegram_id}\n"
            else:
                text += f"   Код: <code>{student.registration_code}</code>\n"

            text += "\n"

        if len(students) > 30:
            text += f"\n... и еще {len(students) - 30} учеников"

    await callback.message.edit_text(
        text,
        reply_markup=get_classes_management_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_classes_delete")
async def delete_class_selection(callback: CallbackQuery):
    """Выбор класса для удаления"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        classes = await crud.get_all_classes(session)

        if not classes:
            await callback.message.edit_text(
                "📝 В базе данных нет классов",
                reply_markup=get_classes_management_menu()
            )
            return

    await callback.message.edit_text(
        "🗑 <b>Удаление класса</b>\n\n"
        "Выберите класс для удаления:",
        reply_markup=get_class_selection_keyboard(classes),
        parse_mode="HTML"
    )


# Продолжение в следующем файле из-за ограничения размера...
