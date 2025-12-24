# bot/controllers/auth_controller.py
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

router = Router()


@router.message(Command("auth"))
async def cmd_auth(message: Message):
    """Команда для начала авторизации"""
    await start_auth_internal(message)


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


async def start_auth_internal(message: Message):
    """Внутренняя функция для начала авторизации"""
    auth_text = (
        "🔐 *Подключение сервера (шаг 1/2)*\n\n"
        "Введи адрес сервера в формате:\n"
        "`host:port`\n\n"
        "👇 Введите адрес сервера:"
    )

    await message.answer(
        auth_text,
        parse_mode="Markdown",
        reply_markup=get_auth_cancel_keyboard()
    )


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
            "❌ Неверный порт! Должен быть от 1 до 65535",
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
    """Обработка пароля"""
    password = message.text.strip()
    data = await state.get_data()
    server_host = data.get("server_host")
    server_port = data.get("server_port")

    # Получаем session_manager из бота
    session_manager = getattr(message.bot, 'session_manager', None)

    if not session_manager:
        await message.answer("❌ Ошибка системы: менеджер сессий не доступен")
        return

    try:
        # Создаем сессию через менеджер
        success = await session_manager.create_session(
            user_id=message.from_user.id,
            host=server_host,
            port=server_port,
            password=password
        )

        if not success:
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

        # Успешная авторизация
        session = await session_manager.get_session(message.from_user.id)
        if session:
            expires_str = session["expires_at"].strftime("%d.%m.%Y %H:%M")
        else:
            expires_str = "6 часов"

        success_text = (
            f"🎉 *Авторизация успешна!*\n\n"
            f"✅ *Подключено к серверу:*\n"
            f"   📍 `{server_host}:{server_port}`\n"
            f"   ⏰ *Сессия активна:* {expires_str}\n"
            f"   👤 *Пользователь:* {message.from_user.first_name}\n\n"
            f"*Что дальше?*"
        )

        await message.answer(
            success_text,
            parse_mode="Markdown",
            reply_markup=get_auth_success_keyboard()
        )

        await state.clear()

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


@router.callback_query(F.data == "auth_manage_session")
async def manage_session(callback: CallbackQuery):
    """Управление сессией"""
    session_manager = getattr(callback.bot, 'session_manager', None)

    if not session_manager:
        await callback.answer("❌ Ошибка системы", show_alert=True)
        return

    session = await session_manager.get_session(callback.from_user.id)

    if not session:
        await callback.answer("❌ У вас нет активной сессии", show_alert=True)
        return

    remaining = await session_manager.get_remaining_time(callback.from_user.id)
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
    session_manager = getattr(callback.bot, 'session_manager', None)

    if not session_manager:
        await callback.answer("❌ Ошибка системы", show_alert=True)
        return

    user_id = callback.from_user.id

    if await session_manager.end_session(user_id):
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
    """Переключение видимости пароля"""
    await callback.answer("👁️ Функция показа/скрытия пароля в разработке", show_alert=True)# bot/controllers/auth_controller.py
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

router = Router()


@router.message(Command("auth"))
async def cmd_auth(message: Message):
    """Команда для начала авторизации"""
    await start_auth_internal(message)


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


async def start_auth_internal(message: Message):
    """Внутренняя функция для начала авторизации"""
    auth_text = (
        "🔐 *Подключение сервера (шаг 1/2)*\n\n"
        "Введи адрес сервера в формате:\n"
        "`host:port`\n\n"
        "👇 Введите адрес сервера:"
    )

    await message.answer(
        auth_text,
        parse_mode="Markdown",
        reply_markup=get_auth_cancel_keyboard()
    )


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
            "❌ Неверный порт! Должен быть от 1 до 65535",
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
    """Обработка пароля"""
    password = message.text.strip()
    data = await state.get_data()
    server_host = data.get("server_host")
    server_port = data.get("server_port")

    # Получаем session_manager из бота
    session_manager = getattr(message.bot, 'session_manager', None)

    if not session_manager:
        await message.answer("❌ Ошибка системы: менеджер сессий не доступен")
        return

    try:
        # Создаем сессию через менеджер
        success = await session_manager.create_session(
            user_id=message.from_user.id,
            host=server_host,
            port=server_port,
            password=password
        )

        if not success:
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

        # Успешная авторизация
        session = await session_manager.get_session(message.from_user.id)
        if session:
            expires_str = session["expires_at"].strftime("%d.%m.%Y %H:%M")
        else:
            expires_str = "6 часов"

        success_text = (
            f"🎉 *Авторизация успешна!*\n\n"
            f"✅ *Подключено к серверу:*\n"
            f"   📍 `{server_host}:{server_port}`\n"
            f"   ⏰ *Сессия активна:* {expires_str}\n"
            f"   👤 *Пользователь:* {message.from_user.first_name}\n\n"
            f"*Что дальше?*"
        )

        await message.answer(
            success_text,
            parse_mode="Markdown",
            reply_markup=get_auth_success_keyboard()
        )

        await state.clear()

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


@router.callback_query(F.data == "auth_manage_session")
async def manage_session(callback: CallbackQuery):
    """Управление сессией"""
    session_manager = getattr(callback.bot, 'session_manager', None)

    if not session_manager:
        await callback.answer("❌ Ошибка системы", show_alert=True)
        return

    session = await session_manager.get_session(callback.from_user.id)

    if not session:
        await callback.answer("❌ У вас нет активной сессии", show_alert=True)
        return

    remaining = await session_manager.get_remaining_time(callback.from_user.id)
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
    session_manager = getattr(callback.bot, 'session_manager', None)

    if not session_manager:
        await callback.answer("❌ Ошибка системы", show_alert=True)
        return

    user_id = callback.from_user.id

    if await session_manager.end_session(user_id):
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
    """Переключение видимости пароля"""
    await callback.answer("👁️ Функция показа/скрытия пароля в разработке", show_alert=True)