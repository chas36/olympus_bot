"""
Хэндлеры управления олимпиадами и экспорта данных
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from database.database import get_async_session
from database import crud
from bot.keyboards import (
    get_olympiads_management_menu, get_export_menu,
    get_admin_main_menu, get_olympiad_selection_keyboard, get_confirm_keyboard
)
from utils.admin_logger import AdminActionLogger
from utils.admin_notifications import notify_system_event
from utils.excel_export import ExcelExporter
import os
import csv
import io
from loguru import logger

router = Router()

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ==================== ОЛИМПИАДЫ ====================

@router.callback_query(F.data == "admin_olympiads_list")
async def show_olympiads_list(callback: CallbackQuery):
    """Показать список олимпиад"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with get_async_session() as session:
        sessions = await crud.get_all_sessions(session)

        if not sessions:
            await callback.message.edit_text(
                "📝 В базе данных нет олимпиад",
                reply_markup=get_olympiads_management_menu()
            )
            return

        text = "🏆 <b>Список олимпиад:</b>\n\n"

        for s in sessions[:15]:
            status = "🟢 Активна" if s.is_active else "⚪ Неактивна"
            text += f"<b>ID {s.id}:</b> {s.subject} ({status})\n"
            text += f"   Дата: {s.date.strftime('%d.%m.%Y')}\n"
            text += f"   Класс: {s.class_number or 'Разные'}\n\n"

        if len(sessions) > 15:
            text += f"... и еще {len(sessions) - 15} олимпиад"

    await callback.message.edit_text(
        text,
        reply_markup=get_olympiads_management_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_olympiads_activate")
async def activate_olympiad_selection(callback: CallbackQuery):
    """Выбор олимпиады для активации"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with get_async_session() as session:
        sessions = await crud.get_all_sessions(session)

        if not sessions:
            await callback.message.edit_text(
                "📝 В базе данных нет олимпиад",
                reply_markup=get_olympiads_management_menu()
            )
            return

        olympiads_data = [
            {"id": s.id, "subject": s.subject, "is_active": s.is_active}
            for s in sessions
        ]

    await callback.message.edit_text(
        "✅ <b>Активация олимпиады</b>\n\n"
        "Выберите олимпиаду для активации:",
        reply_markup=get_olympiad_selection_keyboard(olympiads_data, "activate"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("olympiad_activate_"))
async def execute_activate_olympiad(callback: CallbackQuery):
    """Выполнить активацию олимпиады"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    olympiad_id = int(callback.data.split("_")[2])

    async with get_async_session() as session:
        olympiad = await crud.activate_session(session, olympiad_id)

        if not olympiad:
            await callback.answer("Олимпиада не найдена", show_alert=True)
            return

    AdminActionLogger.log_olympiad_action(
        callback.from_user.id,
        callback.from_user.full_name,
        "activate_olympiad",
        olympiad_id,
        olympiad.subject
    )

    await callback.message.edit_text(
        f"✅ <b>Олимпиада активирована!</b>\n\n"
        f"Предмет: {olympiad.subject}\n"
        f"Дата: {olympiad.date.strftime('%d.%m.%Y')}",
        reply_markup=get_olympiads_management_menu(),
        parse_mode="HTML"
    )

    # Уведомляем других админов
    await notify_system_event(
        callback.bot,
        f"Администратор {callback.from_user.full_name} активировал олимпиаду: {olympiad.subject}"
    )


@router.callback_query(F.data == "admin_olympiads_deactivate")
async def deactivate_all_olympiads(callback: CallbackQuery):
    """Деактивировать все олимпиады"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with get_async_session() as session:
        await crud.deactivate_all_sessions(session)

    AdminActionLogger.log_action(
        callback.from_user.id,
        callback.from_user.full_name,
        "deactivate_all_olympiads"
    )

    await callback.message.edit_text(
        "✅ <b>Все олимпиады деактивированы</b>",
        reply_markup=get_olympiads_management_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_olympiads_delete")
async def delete_olympiad_selection(callback: CallbackQuery):
    """Выбор олимпиады для удаления"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with get_async_session() as session:
        sessions = await crud.get_all_sessions(session)

        if not sessions:
            await callback.message.edit_text(
                "📝 В базе данных нет олимпиад",
                reply_markup=get_olympiads_management_menu()
            )
            return

        olympiads_data = [
            {"id": s.id, "subject": s.subject, "is_active": s.is_active}
            for s in sessions
        ]

    await callback.message.edit_text(
        "🗑 <b>Удаление олимпиады</b>\n\n"
        "Выберите олимпиаду для удаления:",
        reply_markup=get_olympiad_selection_keyboard(olympiads_data, "delete"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("olympiad_delete_"))
async def confirm_delete_olympiad(callback: CallbackQuery):
    """Подтверждение удаления олимпиады"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    olympiad_id = int(callback.data.split("_")[2])

    async with get_async_session() as session:
        olympiad = await crud.get_session_by_id(session, olympiad_id)

        if not olympiad:
            await callback.answer("Олимпиада не найдена", show_alert=True)
            return

    await callback.message.edit_text(
        f"⚠️ <b>Подтверждение удаления</b>\n\n"
        f"Предмет: {olympiad.subject}\n"
        f"Дата: {olympiad.date.strftime('%d.%m.%Y')}\n"
        f"Класс: {olympiad.class_number or 'Разные'}\n\n"
        f"Вместе с олимпиадой будут удалены все связанные коды!\n"
        f"Подтвердите действие:",
        reply_markup=get_confirm_keyboard(f"delete_olympiad_{olympiad_id}"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("confirm_delete_olympiad_"))
async def execute_delete_olympiad(callback: CallbackQuery):
    """Выполнить удаление олимпиады"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    olympiad_id = int(callback.data.split("_")[3])

    async with get_async_session() as session:
        olympiad = await crud.get_session_by_id(session, olympiad_id)

        if not olympiad:
            await callback.answer("Олимпиада не найдена", show_alert=True)
            return

        subject = olympiad.subject
        await crud.delete_session_by_id(session, olympiad_id)

    AdminActionLogger.log_olympiad_action(
        callback.from_user.id,
        callback.from_user.full_name,
        "delete_olympiad",
        olympiad_id,
        subject
    )

    await callback.message.edit_text(
        f"✅ <b>Олимпиада удалена</b>\n\n"
        f"Предмет: {subject}",
        reply_markup=get_olympiads_management_menu(),
        parse_mode="HTML"
    )

    # Уведомляем других админов
    await notify_system_event(
        callback.bot,
        f"Администратор {callback.from_user.full_name} удалил олимпиаду: {subject}"
    )


@router.callback_query(F.data == "admin_olympiads_stats")
async def show_olympiad_stats_selection(callback: CallbackQuery):
    """Выбор олимпиады для статистики"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    async with get_async_session() as session:
        sessions = await crud.get_all_sessions(session)

        if not sessions:
            await callback.message.edit_text(
                "📝 В базе данных нет олимпиад",
                reply_markup=get_olympiads_management_menu()
            )
            return

        olympiads_data = [
            {"id": s.id, "subject": s.subject, "is_active": s.is_active}
            for s in sessions
        ]

    await callback.message.edit_text(
        "📊 <b>Статистика по олимпиаде</b>\n\n"
        "Выберите олимпиаду:",
        reply_markup=get_olympiad_selection_keyboard(olympiads_data, "stats"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("olympiad_stats_"))
async def show_olympiad_stats(callback: CallbackQuery):
    """Показать статистику по олимпиаде"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    olympiad_id = int(callback.data.split("_")[2])

    async with get_async_session() as session:
        from sqlalchemy import select, func
        from database.models import Grade8Code, Grade9Code, CodeRequest

        olympiad = await crud.get_session_by_id(session, olympiad_id)

        if not olympiad:
            await callback.answer("Олимпиада не найдена", show_alert=True)
            return

        # Статистика по кодам 8 класса
        grade8_total = await session.execute(
            select(func.count(Grade8Code.id)).where(Grade8Code.session_id == olympiad_id)
        )
        grade8_issued = await session.execute(
            select(func.count(Grade8Code.id)).where(
                Grade8Code.session_id == olympiad_id,
                Grade8Code.is_issued == True
            )
        )

        # Статистика по кодам 9 класса
        grade9_total = await session.execute(
            select(func.count(Grade9Code.id)).where(Grade9Code.session_id == olympiad_id)
        )
        grade9_used = await session.execute(
            select(func.count(Grade9Code.id)).where(
                Grade9Code.session_id == olympiad_id,
                Grade9Code.is_used == True
            )
        )

        # Статистика по запросам
        requests_total = await session.execute(
            select(func.count(CodeRequest.id)).where(CodeRequest.session_id == olympiad_id)
        )
        screenshots = await session.execute(
            select(func.count(CodeRequest.id)).where(
                CodeRequest.session_id == olympiad_id,
                CodeRequest.screenshot_submitted == True
            )
        )

        g8_total = grade8_total.scalar()
        g8_issued = grade8_issued.scalar()
        g9_total = grade9_total.scalar()
        g9_used = grade9_used.scalar()
        req_total = requests_total.scalar()
        scr_count = screenshots.scalar()

    text = (
        f"📊 <b>Статистика: {olympiad.subject}</b>\n\n"
        f"📅 Дата: {olympiad.date.strftime('%d.%m.%Y')}\n"
        f"🎓 Класс: {olympiad.class_number or 'Разные'}\n"
        f"⭐ Статус: {'🟢 Активна' if olympiad.is_active else '⚪ Неактивна'}\n\n"
        f"<b>Коды 8 класса:</b>\n"
        f"  Всего: {g8_total}\n"
        f"  Выдано: {g8_issued}\n\n"
        f"<b>Коды 9+ классов:</b>\n"
        f"  Всего: {g9_total}\n"
        f"  Использовано: {g9_used}\n"
        f"  Осталось: {g9_total - g9_used}\n\n"
        f"<b>Запросы кодов:</b> {req_total}\n"
        f"<b>Скриншоты:</b> {scr_count}\n"
    )

    if req_total > 0:
        percentage = int((scr_count / req_total) * 100)
        text += f"<b>Процент сдачи:</b> {percentage}%"

    await callback.message.edit_text(
        text,
        reply_markup=get_olympiads_management_menu(),
        parse_mode="HTML"
    )


# ==================== ЭКСПОРТ ====================

@router.callback_query(F.data == "admin_export_students_csv")
async def export_students_csv(callback: CallbackQuery):
    """Экспорт учеников в CSV"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    await callback.answer("Генерирую CSV файл...", show_alert=False)

    async with get_async_session() as session:
        students = await crud.get_all_students(session)

        # Создаем CSV в памяти
        output = io.StringIO()
        writer = csv.writer(output)

        # Заголовки
        writer.writerow([
            "ID", "ФИО", "Класс", "Параллель", "Код регистрации",
            "Зарегистрирован", "Telegram ID", "Дата создания"
        ])

        # Данные
        for s in students:
            writer.writerow([
                s.id,
                s.full_name,
                s.class_number or "",
                s.parallel or "",
                s.registration_code,
                "Да" if s.is_registered else "Нет",
                s.telegram_id or "-",
                s.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])

        output.seek(0)
        csv_bytes = output.getvalue().encode('utf-8-sig')  # BOM для Excel

    # Отправляем файл
    file = BufferedInputFile(csv_bytes, filename="students.csv")
    await callback.message.answer_document(file, caption=f"📄 Список учеников ({len(students)} чел.)")

    AdminActionLogger.log_export(
        callback.from_user.id,
        callback.from_user.full_name,
        "students_csv",
        len(students)
    )


@router.callback_query(F.data == "admin_export_students_excel")
async def export_students_excel(callback: CallbackQuery):
    """Экспорт учеников в Excel"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    await callback.answer("Генерирую Excel файл...", show_alert=False)

    try:
        async with get_async_session() as session:
            students = await crud.get_all_students(session)

            students_data = [
                {
                    "id": s.id,
                    "full_name": s.full_name,
                    "class_number": s.class_number,
                    "parallel": s.parallel,
                    "registration_code": s.registration_code,
                    "is_registered": s.is_registered,
                    "telegram_id": s.telegram_id,
                    "created_at": s.created_at.isoformat(),
                    "registered_at": s.registered_at.isoformat() if s.registered_at else None
                }
                for s in students
            ]

        # Генерируем Excel
        excel_file = ExcelExporter.export_students(students_data)

        # Отправляем файл
        file = BufferedInputFile(excel_file.read(), filename="students.xlsx")
        await callback.message.answer_document(file, caption=f"📊 Список учеников ({len(students)} чел.)")

        AdminActionLogger.log_export(
            callback.from_user.id,
            callback.from_user.full_name,
            "students_excel",
            len(students)
        )

    except ImportError:
        await callback.answer(
            "❌ Модуль openpyxl не установлен. Используйте CSV экспорт.",
            show_alert=True
        )


@router.callback_query(F.data == "admin_export_olympiads_csv")
async def export_olympiads_csv(callback: CallbackQuery):
    """Экспорт олимпиад в CSV"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    await callback.answer("Генерирую CSV файл...", show_alert=False)

    async with get_async_session() as session:
        sessions = await crud.get_all_sessions(session)

        # Создаем CSV
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["ID", "Предмет", "Класс", "Дата", "Этап", "Активна", "Файл"])

        for s in sessions:
            writer.writerow([
                s.id,
                s.subject,
                s.class_number or "Разные",
                s.date.strftime("%d.%m.%Y"),
                s.stage or "-",
                "Да" if s.is_active else "Нет",
                s.uploaded_file_name or "-"
            ])

        output.seek(0)
        csv_bytes = output.getvalue().encode('utf-8-sig')

    file = BufferedInputFile(csv_bytes, filename="olympiads.csv")
    await callback.message.answer_document(file, caption=f"📄 Список олимпиад ({len(sessions)} шт.)")

    AdminActionLogger.log_export(
        callback.from_user.id,
        callback.from_user.full_name,
        "olympiads_csv",
        len(sessions)
    )


@router.callback_query(F.data == "admin_export_stats_excel")
async def export_stats_excel(callback: CallbackQuery):
    """Экспорт статистики в Excel"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    await callback.answer("Генерирую Excel файл...", show_alert=False)

    try:
        async with get_async_session() as session:
            all_students = await crud.get_all_students(session)
            registered = [s for s in all_students if s.is_registered]
            all_sessions = await crud.get_all_sessions(session)
            classes = await crud.get_all_classes(session)

            # Собираем статистику по классам
            classes_stats = []
            for class_num in classes:
                class_students = await crud.get_students_by_class(session, class_num)
                class_registered = sum(1 for s in class_students if s.is_registered)
                classes_stats.append({
                    "class_number": class_num,
                    "total": len(class_students),
                    "registered": class_registered
                })

            stats = {
                "general": {
                    "Всего учеников": len(all_students),
                    "Зарегистрировано": len(registered),
                    "Не зарегистрировано": len(all_students) - len(registered),
                    "Всего олимпиад": len(all_sessions),
                    "Активных олимпиад": sum(1 for s in all_sessions if s.is_active)
                },
                "classes": classes_stats
            }

        excel_file = ExcelExporter.export_statistics(stats)

        file = BufferedInputFile(excel_file.read(), filename="statistics.xlsx")
        await callback.message.answer_document(file, caption="📊 Статистика системы")

        AdminActionLogger.log_export(
            callback.from_user.id,
            callback.from_user.full_name,
            "statistics_excel"
        )

    except ImportError:
        await callback.answer(
            "❌ Модуль openpyxl не установлен.",
            show_alert=True
        )


# ==================== УВЕДОМЛЕНИЯ ====================

@router.callback_query(F.data == "admin_notifications")
async def show_notifications_settings(callback: CallbackQuery):
    """Показать настройки уведомлений"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    text = (
        "🔔 <b>Уведомления</b>\n\n"
        "Система автоматически отправляет уведомления при:\n"
        "• Регистрации новых учеников\n"
        "• Запросе кодов\n"
        "• Загрузке скриншотов\n"
        "• Загрузке новых олимпиад\n"
        "• Критических системных событиях\n\n"
        "Все уведомления отправляются администраторам\n"
        "из списка ADMIN_IDS в .env файле."
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_admin_main_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_help")
async def show_admin_help(callback: CallbackQuery):
    """Показать справку"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    text = (
        "📚 <b>Справка по админ-панели</b>\n\n"
        "<b>Управление через бот:</b>\n"
        "• Все основные операции доступны через кнопки\n"
        "• Действия логируются и отслеживаются\n"
        "• Критичные операции требуют подтверждения\n\n"
        "<b>API доступ:</b>\n"
        "• Полная документация: /docs\n"
        "• Все операции доступны через REST API\n\n"
        "<b>Экспорт данных:</b>\n"
        "• CSV - универсальный формат\n"
        "• Excel - с форматированием и стилями\n\n"
        "<b>Дополнительная документация:</b>\n"
        "• docs/ADMIN_PANEL.md\n"
        "• README.md"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_admin_main_menu(),
        parse_mode="HTML"
    )
