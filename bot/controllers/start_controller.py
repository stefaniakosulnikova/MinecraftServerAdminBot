# bot/controllers/start_controller.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from domain.services.session_manager import session_manager
from bot.keyboards.auth_menu import get_auth_main_keyboard
from bot.keyboards.main_menu import get_main_menu_keyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Главная команда /start"""
    user_id = message.from_user.id

    # 1. Если пользователь уже авторизован - показываем главное меню
    if session_manager.is_authorized(user_id):
        await message.answer(
            f"🏠 Добро пожаловать, {message.from_user.first_name}!\n\n"
            f"Вы уже авторизованы. Используйте меню ниже:",
            reply_markup=get_main_menu_keyboard()
        )
        return

    # 2. Если НЕ авторизован - показываем меню авторизации
    welcome_text = (
        "🤖 *Minecraft Server Admin Bot*\n\n"
        "🔒 *Доступ ограничен*\n\n"
        "Чтобы управлять сервером Minecraft, "
        "нужно авторизоваться с помощью RCON.\n\n"
        "📌 *Сессия действует 6 часов*\n\n"
        "👇 Выберите действие:"
    )

    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_auth_main_keyboard()
    )


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    """Колбэк для главного меню"""
    await callback.message.edit_text(
        "🏠 *Главное меню*\n\n"
        "👇 Выберите действие:",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()