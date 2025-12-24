# bot/keyboards/commands_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_commands_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура быстрых команд"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="👥 Список игроков", callback_data="cmd_list"),
        InlineKeyboardButton(text="💾 Сохранить мир", callback_data="cmd_save"),
    )
    builder.row(
        InlineKeyboardButton(text="☀️ День", callback_data="cmd_time"),
        InlineKeyboardButton(text="🌤️ Ясно", callback_data="cmd_weather"),
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_commands"),
        InlineKeyboardButton(text="↩️ Назад", callback_data="main_menu"),
    )

    return builder.as_markup()


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения для опасных команд"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="✅ Да, остановить", callback_data="confirm_stop"),
        InlineKeyboardButton(text="❌ Нет, отменить", callback_data="cancel_stop"),
    )

    return builder.as_markup()


def get_admin_commands_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура команд для админов"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="⚡ Перезагрузка", callback_data="cmd_restart"),
        InlineKeyboardButton(text="🔧 Тех. работы", callback_data="cmd_maintenance"),
    )
    builder.row(
        InlineKeyboardButton(text="📋 Бэкап", callback_data="cmd_backup"),
        InlineKeyboardButton(text="📊 Логи", callback_data="cmd_logs"),
    )
    builder.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="commands"),
    )

    return builder.as_markup()