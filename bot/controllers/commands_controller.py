# bot/controllers/commands_controller.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from domain.services.command_validator import CommandValidator, CommandType
from infrastructure.adapters.rcon_client import RconClientAdapter
from infrastructure.adapters.crypto import CryptoService
from bot.keyboards.commands_menu import get_commands_keyboard, get_confirmation_keyboard

router = Router()
command_validator = CommandValidator()
crypto = CryptoService()


@router.message(Command("commands"))
async def cmd_commands(message: Message):
    """Меню быстрых команд"""
    # Получаем session_manager из бота
    session_manager = getattr(message.bot, 'session_manager', None)

    if not session_manager or not await session_manager.is_authorized(message.from_user.id):
        await message.answer("🔒 Сначала авторизуйтесь через /start")
        return

    text = (
        "⚡ *Быстрые команды*\n\n"
        "Выберите команду из меню или введите свою:\n"
        "• /list - список игроков\n"
        "• /save - сохранить мир\n"
        "• /stop - остановить сервер\n"
        "• /say <текст> - сообщение от сервера\n"
        "• /time set day - установить день\n"
        "• /weather clear - установить ясную погоду"
    )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_commands_keyboard()
    )


@router.message(Command("list"))
async def cmd_list(message: Message):
    """Команда list - список игроков"""
    # Получаем session_manager из бота
    session_manager = getattr(message.bot, 'session_manager', None)

    if not session_manager:
        await message.answer("❌ Ошибка системы: менеджер сессий не доступен")
        return

    # Проверяем авторизацию
    if not await session_manager.is_authorized(message.from_user.id):
        await message.answer("🔒 Сначала авторизуйтесь через /start")
        return

    # Получаем информацию о сервере
    server_info = await session_manager.get_server(message.from_user.id)
    if not server_info:
        await message.answer("❌ Сервер не найден. Пожалуйста, авторизуйтесь заново.")
        return

    try:
        # Дешифруем пароль
        password = crypto.decrypt(server_info["encrypted_password"])

        # Выполняем команду
        rcon_client = RconClientAdapter(
            server_info["host"],
            server_info["port"],
            password
        )

        await message.answer("⏳ Получаю список игроков...")
        result = await rcon_client.execute_command("list")

        if result and result.strip():
            response_text = f"👥 *Список игроков:*\n```\n{result}\n```"
        else:
            response_text = "👥 На сервере нет игроков"

        await message.answer(response_text, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"❌ Ошибка выполнения команды: {str(e)[:200]}")


@router.message(Command("save"))
async def cmd_save(message: Message):
    """Команда save-all - сохранить мир"""
    await execute_simple_command(message, "save-all", "💾 Мир сохранен")


@router.message(Command("stop"))
async def cmd_stop(message: Message, state: FSMContext):
    """Команда stop - остановить сервер (требует подтверждения)"""
    session_manager = getattr(message.bot, 'session_manager', None)

    if not session_manager or not await session_manager.is_authorized(message.from_user.id):
        await message.answer("🔒 Сначала авторизуйтесь через /start")
        return

    await message.answer(
        "⚠️ *ВНИМАНИЕ!*\n\n"
        "Вы собираетесь остановить сервер.\n"
        "Это действие может привести к потере данных, если игроки не сохранили игру.\n\n"
        "Рекомендуется сначала выполнить /save\n\n"
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
    await callback.answer("✅ Сервер остановлен")


@router.callback_query(F.data == "cancel_stop")
async def cancel_stop(callback: CallbackQuery, state: FSMContext):
    """Отмена остановки сервера"""
    await callback.message.edit_text("❌ Остановка сервера отменена")
    await state.clear()
    await callback.answer()


@router.message(Command("time"))
async def cmd_time(message: Message):
    """Установка времени"""
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    if not args:
        await message.answer("Использование: /time <значение>\nПример: /time set day")
        return

    command = f"time {' '.join(args)}"
    await execute_simple_command(message, command, f"⏰ Время установлено: {' '.join(args)}")


@router.message(Command("weather"))
async def cmd_weather(message: Message):
    """Установка погоды"""
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    if not args:
        await message.answer("Использование: /weather <тип>\nПример: /weather clear")
        return

    command = f"weather {' '.join(args)}"
    await execute_simple_command(message, command, f"🌤️ Погода установлена: {' '.join(args)}")


@router.message(Command("say"))
async def cmd_say(message: Message):
    """Сообщение от сервера"""
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    if not args:
        await message.answer("Использование: /say <сообщение>")
        return

    command = f"say {' '.join(args)}"
    await execute_simple_command(message, command, f"📢 Сообщение отправлено")


@router.message(Command("gamemode"))
async def cmd_gamemode(message: Message):
    """Смена режима игры"""
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    if len(args) < 2:
        await message.answer("Использование: /gamemode <режим> <игрок>\nПример: /gamemode creative Player1")
        return

    command = f"gamemode {' '.join(args)}"
    await execute_simple_command(message, command, f"🎮 Режим игры изменен")


async def execute_simple_command(message: Message, command: str, success_message: str):
    """Выполнение простой команды"""
    # Получаем session_manager из бота
    session_manager = getattr(message.bot, 'session_manager', None)

    if not session_manager:
        await message.answer("❌ Ошибка системы: менеджер сессий не доступен")
        return

    # Проверяем авторизацию
    if not await session_manager.is_authorized(message.from_user.id):
        await message.answer("🔒 Сначала авторизуйтесь через /start")
        return

    # Валидируем команду
    is_valid, validated_command, error = command_validator.validate_command(command)
    if not is_valid:
        await message.answer(f"❌ {error}")
        return

    # Проверяем опасные команды
    if command_validator.is_dangerous_command(command):
        await message.answer(f"⚠️ Команда '{command}' является опасной. Будьте осторожны!")

    # Получаем информацию о сервере
    server_info = await session_manager.get_server(message.from_user.id)
    if not server_info:
        await message.answer("❌ Сервер не найден. Пожалуйста, авторизуйтесь заново.")
        return

    try:
        # Дешифруем пароль
        password = crypto.decrypt(server_info["encrypted_password"])

        # Выполняем команду
        rcon_client = RconClientAdapter(
            server_info["host"],
            server_info["port"],
            password
        )

        await message.answer(f"⏳ Выполняю команду: `{command}`", parse_mode="Markdown")
        result = await rcon_client.execute_command(command)

        if result and result.strip():
            response = f"✅ {success_message}\n```\n{result}\n```"
        else:
            response = f"✅ {success_message}"

        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"❌ Ошибка выполнения команды: {str(e)[:200]}")


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
        elif cmd_key == "cmd_time":
            await cmd_time(message)
        elif cmd_key == "cmd_weather":
            await cmd_weather(message)

    await callback.answer()


@router.callback_query(F.data == "refresh_commands")
async def refresh_commands(callback: CallbackQuery):
    """Обновление меню команд"""
    await cmd_commands(callback.message)
    await callback.answer("🔄 Меню обновлено")