# bot/keyboards/monitoring_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_monitoring_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура мониторинга"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_monitor"),
        InlineKeyboardButton(text="👥 Игроки", callback_data="show_players"),
    )
    builder.row(
        InlineKeyboardButton(text="📈 Графики", callback_data="show_graphs"),
        InlineKeyboardButton(text="⚠️ Оповещения", callback_data="notifications"),
    )
    builder.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="main_menu"),
    )

    return builder.as_markup()