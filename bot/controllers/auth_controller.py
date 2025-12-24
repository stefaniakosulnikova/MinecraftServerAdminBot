from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import re

from bot.states.auth_states import AuthStates
from bot.keyboards.auth_menu import (
    get_auth_main_keyboard,
    get_auth_cancel_keyboard,
    get_auth_success_keyboard,
    get_session_manage_keyboard,
    get_password_toggle_keyboard
)
from domain.services.session_manager import session_manager

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Главный экран для неавторизованных пользователей"""
    if session_manager.is_authorized(message.from_user.id):
        from bot.keyboards.main_menu import get_main_menu_keyboard
        await message.answer(
            "🏠 Minecraft Server Admin Bot\n\n"
            "Вы уже авторизованы. Используйте меню ниже:",
            reply_markup=get_main_menu_keyboard()
        )
        return

    # Для неавторизованных
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


@router.callback_query(F.data == "auth_start")
async def start_auth(callback: CallbackQuery, state: FSMContext):
    """Начало процесса авторизации"""
    auth_text = (
        "🔐 *Подключение сервера (шаг 1/2)*\n\n"
        "Введи адрес сервера в формате:\n"
        "`host:port`\n\n"
        "👇 Введите адрес сервера:"
    )

    await callback.message.edit_text(
        auth_text,
        parse_mode="Markdown",
        reply_markup=get_auth_cancel_keyboard()
    )
    await state.set_state(AuthStates.waiting_for_host)
    await callback.answer()


@router.message(AuthStates.waiting_for_host)
async def process_host(message: Message, state: FSMContext):
    """Обработка ввода host:port"""
    user_input = message.text.strip()
    host_port_pattern = r'^([a-zA-Z0-9\.\-]+):(\d{1,5})$'
    match = re.match(host_port_pattern, user_input)

    if not match:
        error_text = (
            "❌ *Неверный формат!*\n\n"
            "Введите адрес в формате:\n"
            "`host:port`\n\n"
            "👇 Попробуйте снова:"
        )
        await message.answer(
            error_text,
            parse_mode="Markdown",
            reply_markup=get_auth_cancel_keyboard()
        )
        return

    host, port = match.groups()
    port = int(port)

    # Проверка порта
    if not (1 <= port <= 65535):
        await message.answer(
            "❌ Неверный порт!",
            reply_markup=get_auth_cancel_keyboard()
        )
        return

    await state.update_data(server_host=host, server_port=port)

    step2_text = (
        f"🔐 *Подключение сервера (шаг 2/2)*\n\n"
        f"Сервер: `{host}:{port}`\n\n"
        f"Теперь отправь RCON пароль для подключения.\n\n"
        f"👇 Введите пароль:"
    )

    await message.answer(
        step2_text,
        parse_mode="Markdown",
        reply_markup=get_password_toggle_keyboard()
    )
    await state.set_state(AuthStates.waiting_for_password)



@router.message(AuthStates.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    from infrastructure.adapters.rcon_client import RconClientAdapter
    from infrastructure.adapters.crypto import CryptoService

    password = message.text.strip()
    data = await state.get_data()
    server_host = data.get("server_host")
    server_port = data.get("server_port")

    try:
        from infrastructure.adapters.rcon_service import RconService

        rcon_client = RconService(server_host, server_port, password)

        is_connected = await rcon_client.test_connection()

        if not is_connected:
            error_text = (
                f"❌ *Не удалось подключиться!*\n\n"
                f"Проверьте:\n"
                f"1. Правильность адреса: `{server_host}:{server_port}`\n"
                f"2. Правильность пароля RCON\n"
                f"3. Запущен ли сервер\n"
                f"4. Открыт ли RCON порт\n\n"
                f"👇 Попробуйте снова:"
            )
            await message.answer(
                error_text,
                parse_mode="Markdown",
                reply_markup=get_auth_cancel_keyboard()
            )
            return

    except Exception as e:
        error_text = (
            f"❌ *Ошибка подключения!*\n\n"
            f"Ошибка: {str(e)}\n\n"
            f"👇 Попробуйте снова:"
        )
        await message.answer(
            error_text,
            parse_mode="Markdown",
            reply_markup=get_auth_cancel_keyboard()
        )
        return

    session = session_manager.create_session(
        user_id=message.from_user.id,
        server_host=server_host,
        server_port=server_port
    )

    expires_str = session["expires_at"].strftime("%d.%m.%Y %H:%M")

    success_text = (
        f"🎉 *Авторизация успешна!*\n\n"
        f"✅ *Подключено к серверу:*\n"
        f"   📍 `{server_host}:{server_port}`\n"
        f"   ⏰ *Сессия активна до:* {expires_str}\n"
        f"   👤 *Пользователь:* {message.from_user.first_name}\n\n"
        f"*Что дальше?*"
    )

    await message.answer(
        success_text,
        parse_mode="Markdown",
        reply_markup=get_auth_success_keyboard()
    )

    await state.clear()




@router.callback_query(F.data == "auth_manage_session")
async def manage_session(callback: CallbackQuery):
    """Управление сессией"""
    user_id = callback.from_user.id
    session = session_manager.get_session(user_id)

    if not session:
        await callback.answer("❌ У вас нет активной сессии", show_alert=True)
        return

    remaining = session_manager.get_remaining_time(user_id)
    expires_str = session["expires_at"].strftime("%d.%m.%Y %H:%M")

    session_text = (
        f"⚙️ *Управление сессией*\n\n"
        f"✅ *Авторизован для:*\n"
        f"   📍 `{session['server_host']}:{session['server_port']}`\n"
        f"   ⏰ *Осталось:* {remaining}\n"
        f"   *Действует до:* {expires_str}\n"
        f"   👤 *Пользователь:* {callback.from_user.first_name}\n\n"
        f"*Действия:*"
    )

    await callback.message.edit_text(
        session_text,
        parse_mode="Markdown",
        reply_markup=get_session_manage_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "auth_logout")
async def logout(callback: CallbackQuery):
    """Выход из системы"""
    user_id = callback.from_user.id

    if session_manager.end_session(user_id):
        logout_text = (
            "🚪 *Вы вышли из системы*\n\n"
            "Ваша сессия завершена. Для доступа к функциям управления "
            "сервером нужно авторизоваться заново."
        )

        await callback.message.edit_text(
            logout_text,
            parse_mode="Markdown",
            reply_markup=get_auth_main_keyboard()
        )
    else:
        await callback.answer("❌ У вас нет активной сессии", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "auth_cancel")
async def cancel_auth(callback: CallbackQuery, state: FSMContext):
    """Отмена процесса авторизации"""
    await state.clear()

    cancel_text = (
        "❌ *Авторизация отменена*\n\n"
        "Вы можете попробовать снова, когда будете готовы."
    )

    await callback.message.edit_text(
        cancel_text,
        parse_mode="Markdown",
        reply_markup=get_auth_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "auth_retry")
async def retry_auth(callback: CallbackQuery, state: FSMContext):
    """Повторная попытка авторизации"""
    await start_auth(callback, state)


@router.callback_query(F.data == "auth_toggle_password")
async def toggle_password(callback: CallbackQuery):
    """Переключение видимости пароля (заглушка)"""
    await callback.answer("👁️ Функция показа/скрытия пароля в разработке", show_alert=True)