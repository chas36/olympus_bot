from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


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
        [InlineKeyboardButton(text="👥 Список учеников", callback_data="admin_students")],
        [InlineKeyboardButton(text="📤 Загрузить файл", callback_data="admin_upload")],
        [InlineKeyboardButton(text="🔑 Генерировать коды", callback_data="admin_generate_codes")],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
