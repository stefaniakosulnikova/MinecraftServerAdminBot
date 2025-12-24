# bot/controllers/commands_controller.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from domain.services.command_validator import CommandValidator
from domain.services.session_manager import session_manager
from infrastructure.adapters.rcon_client import RconClientAdapter
from infrastructure.adapters.crypto import CryptoService
from bot.keyboards.commands_menu import get_commands_keyboard, get_confirmation_keyboard

router = Router()
command_validator = CommandValidator()
crypto = CryptoService()


@router.message(Command("commands"))
async def cmd_commands(message: Message):
    """Меню быстрых команд"""
    if not session_manager.is_authorized(message.from_user.id):
        await message.answer("🔒 Сначала авторизуйтесь через /start")
        return

    text = (
        "⚡ *Быстрые команды*\n\n"
        "Выберите команду из меню или введите свою:\n"
        "• /list - список игроков\n"
        "• /save - сохранить мир\n"
        "• /stop - остановить сервер\n"
        "• /say <текст> - сообщение от сервера"
    )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_commands_keyboard()
    )


@router.message(Command("list"))
async def cmd_list(message: Message):
    """Команда list - список игроков"""
    if not session_manager.is_authorized(message.from_user.id):
        await message.answer("🔒 Сначала авторизуйтесь через /start")
        return

    server = session_manager.get_server(message.from_user.id)
    if not server:
        await message.answer("❌ Сервер не найден")
        return

    try:
        # Дешифруем пароль
        password = crypto.decrypt(server.encrypted_password)

        # Выполняем команду
        rcon_client = RconClientAdapter(server.host, server.port, password)
        result = await rcon_client.execute_command("list")

        await message.answer(f"👥 *Список игроков:*\n```\n{result}\n```", parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("save"))
async def cmd_save(message: Message):
    """Команда save-all - сохранить мир"""
    await execute_simple_command(message, "save-all", "💾 Мир сохранен")


@router.message(Command("stop"))
async def cmd_stop(message: Message, state: FSMContext):
    """Команда stop - остановить сервер (требует подтверждения)"""
    if not session_manager.is_authorized(message.from_user.id):
        await message.answer("🔒 Сначала авторизуйтесь через /start")
        return

    await message.answer(
        "⚠️ *ВНИМАНИЕ!*\n\n"
        "Вы собираетесь остановить сервер.\n"
        "Это действие может привести к потере данных.\n\n"
        "Подтвердите остановку:",
        parse_mode="Markdown",
        reply_markup=get_confirmation_keyboard()
    )

    # Сохраняем состояние для подтверждения
    await state.set_state("confirm_stop")


@router.callback_query(F.data == "confirm_stop")
async def confirm_stop(callback: CallbackQuery, state: FSMContext):
    """Подтверждение остановки сервера"""
    await execute_simple_command(callback.message, "stop", "🛑 Сервер остановлен")
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_stop")
async def cancel_stop(callback: CallbackQuery, state: FSMContext):
    """Отмена остановки сервера"""
    await callback.message.edit_text("❌ Остановка сервера отменена")
    await state.clear()
    await callback.answer()


async def execute_simple_command(message: Message, command: str, success_message: str):
    """Выполнение простой команды"""
    if not session_manager.is_authorized(message.from_user.id):
        await message.answer("🔒 Сначала авторизуйтесь через /start")
        return

    server = session_manager.get_server(message.from_user.id)
    if not server:
        await message.answer("❌ Сервер не найден")
        return

    try:
        # Дешифруем пароль
        password = crypto.decrypt(server.encrypted_password)

        # Выполняем команду
        rcon_client = RconClientAdapter(server.host, server.port, password)
        result = await rcon_client.execute_command(command)

        await message.answer(f"✅ {success_message}\n```\n{result}\n```", parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.callback_query(F.data.startswith("cmd_"))
async def quick_command(callback: CallbackQuery):
    """Обработка быстрых команд из меню"""
    command_map = {
        "cmd_list": "list",
        "cmd_save": "save-all",
        "cmd_time": "time set day",
        "cmd_weather": "weather clear",
        "cmd_players": "list"
    }

    cmd_key = callback.data
    if cmd_key in command_map:
        # Создаем фейковое сообщение для выполнения команды
        message = callback.message
        message.text = f"/{command_map[cmd_key]}"
        message.from_user = callback.from_user

        if cmd_key == "cmd_list":
            await cmd_list(message)
        elif cmd_key == "cmd_save":
            await cmd_save(message)

    await callback.answer()