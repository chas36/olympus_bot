from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_grade_selection_keyboard(grade9_available: bool = True) -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора класса
    
    Args:
        grade9_available: доступны ли коды для 9 класса
    """
    buttons = [
        [InlineKeyboardButton(text="8️⃣ 8 класс", callback_data="grade_8")]
    ]
    
    if grade9_available:
        buttons.append(
            [InlineKeyboardButton(text="9️⃣ 9 класс", callback_data="grade_9")]
        )
    else:
        buttons.append(
            [InlineKeyboardButton(text="9️⃣ 9 класс (недоступно)", callback_data="grade_9_unavailable")]
        )
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Главное меню администратора"""
    buttons = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [
            InlineKeyboardButton(text="👥 Ученики", callback_data="admin_students_menu"),
            InlineKeyboardButton(text="🏆 Олимпиады", callback_data="admin_olympiads_menu")
        ],
        [
            InlineKeyboardButton(text="🎓 Классы", callback_data="admin_classes_menu"),
            InlineKeyboardButton(text="📤 Загрузка", callback_data="admin_upload")
        ],
        [
            InlineKeyboardButton(text="📥 Экспорт", callback_data="admin_export_menu"),
            InlineKeyboardButton(text="🔔 Уведомления", callback_data="admin_notifications")
        ],
        [InlineKeyboardButton(text="📚 Справка", callback_data="admin_help")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_students_management_menu() -> InlineKeyboardMarkup:
    """Меню управления учениками"""
    buttons = [
        [InlineKeyboardButton(text="📋 Список всех", callback_data="admin_students_list")],
        [InlineKeyboardButton(text="✅ Зарегистрированные", callback_data="admin_students_registered")],
        [InlineKeyboardButton(text="❌ Не зарегистрированные", callback_data="admin_students_unregistered")],
        [InlineKeyboardButton(text="🔍 Поиск ученика", callback_data="admin_students_search")],
        [InlineKeyboardButton(text="🗑 Удалить ученика", callback_data="admin_students_delete")],
        [InlineKeyboardButton(text="⚠️ Очистить всех", callback_data="admin_students_clear_all")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_classes_management_menu() -> InlineKeyboardMarkup:
    """Меню управления классами"""
    buttons = [
        [InlineKeyboardButton(text="📋 Список классов", callback_data="admin_classes_list")],
        [InlineKeyboardButton(text="👥 Ученики по классам", callback_data="admin_classes_students")],
        [InlineKeyboardButton(text="🗑 Удалить класс", callback_data="admin_classes_delete")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_olympiads_management_menu() -> InlineKeyboardMarkup:
    """Меню управления олимпиадами"""
    buttons = [
        [InlineKeyboardButton(text="📋 Список олимпиад", callback_data="admin_olympiads_list")],
        [InlineKeyboardButton(text="✅ Активировать", callback_data="admin_olympiads_activate")],
        [InlineKeyboardButton(text="❌ Деактивировать все", callback_data="admin_olympiads_deactivate")],
        [InlineKeyboardButton(text="🗑 Удалить олимпиаду", callback_data="admin_olympiads_delete")],
        [InlineKeyboardButton(text="📊 Статистика по олимпиаде", callback_data="admin_olympiads_stats")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_export_menu() -> InlineKeyboardMarkup:
    """Меню экспорта данных"""
    buttons = [
        [InlineKeyboardButton(text="📄 Ученики (CSV)", callback_data="admin_export_students_csv")],
        [InlineKeyboardButton(text="📊 Ученики (Excel)", callback_data="admin_export_students_excel")],
        [InlineKeyboardButton(text="📄 Олимпиады (CSV)", callback_data="admin_export_olympiads_csv")],
        [InlineKeyboardButton(text="📊 Статистика (Excel)", callback_data="admin_export_stats_excel")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_button() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ В главное меню", callback_data="admin_menu")]
    ])


def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{action}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_class_selection_keyboard(classes: list) -> InlineKeyboardMarkup:
    """Клавиатура выбора класса"""
    buttons = []

    # Группируем по 3 кнопки в ряд
    row = []
    for class_num in classes:
        row.append(InlineKeyboardButton(
            text=f"{class_num} класс",
            callback_data=f"select_class_{class_num}"
        ))

        if len(row) == 3:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_classes_menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_olympiad_selection_keyboard(olympiads: list, action: str = "view") -> InlineKeyboardMarkup:
    """Клавиатура выбора олимпиады"""
    buttons = []

    for olympiad in olympiads[:10]:  # Показываем максимум 10
        status_emoji = "🟢" if olympiad.get("is_active") else "⚪"
        text = f"{status_emoji} {olympiad['subject']} (ID: {olympiad['id']})"
        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"olympiad_{action}_{olympiad['id']}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_olympiads_menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
