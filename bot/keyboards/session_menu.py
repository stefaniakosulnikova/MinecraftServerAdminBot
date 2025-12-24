# bot/keyboards/session_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_session_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления сессией"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🔄 Продлить", callback_data="extend_session"),
        InlineKeyboardButton(text="🚪 Выйти", callback_data="logout"),
    )
    builder.row(
        InlineKeyboardButton(text="🌐 Сменить сервер", callback_data="auth_change_server"),
        InlineKeyboardButton(text="➕ Новый сервер", callback_data="auth_add_server"),
    )
    builder.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="main_menu"),
    )

    return builder.as_markup()


# Экспортируем функцию
__all__ = ['get_session_menu_keyboard']