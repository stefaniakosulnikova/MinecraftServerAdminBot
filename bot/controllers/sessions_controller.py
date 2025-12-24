# bot/controllers/sessions_controller.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

router = Router()


@router.message(Command("sessions"))
async def cmd_sessions(message: Message):
    """Управление сессиями"""
    # Получаем session_manager из бота
    session_manager = getattr(message.bot, 'session_manager', None)

    if not session_manager:
        await message.answer("❌ Ошибка системы: менеджер сессий не доступен")
        return

    if not await session_manager.is_authorized(message.from_user.id):
        await message.answer("🔒 Сначала авторизуйтесь через /start")
        return

    session = await session_manager.get_session(message.from_user.id)
    server_info = await session_manager.get_server(message.from_user.id)

    if not session or not server_info:
        await message.answer("❌ Сессия не найдена")
        return

    remaining = await session_manager.get_remaining_time(message.from_user.id)
    expires_str = session["expires_at"].strftime("%d.%m.%Y %H:%M")

    text = (
        f"🔑 *Управление сессией*\n\n"
        f"👤 Пользователь: {message.from_user.first_name}\n"
        f"🌐 Сервер: `{server_info['host']}:{server_info['port']}`\n"
        f"⏰ Осталось времени: {remaining}\n"
        f"🔄 Действует до: {expires_str}\n\n"
        f"*Доступные команды:*\n"
        f"• /logout - выйти из системы\n"
        f"• /start - сменить сервер\n"
        f"• /help - справка по командам"
    )

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("logout"))
async def cmd_logout(message: Message):
    """Выход из системы"""
    session_manager = getattr(message.bot, 'session_manager', None)

    if not session_manager:
        await message.answer("❌ Ошибка системы")
        return

    if await session_manager.end_session(message.from_user.id):
        await message.answer(
            "✅ Вы успешно вышли из системы.\n"
            "Для доступа к функциям нужно авторизоваться заново через /start."
        )
    else:
        await message.answer("ℹ️ У вас нет активной сессии")


@router.callback_query(F.data == "session_info")
async def session_info_callback(callback: CallbackQuery):
    """Информация о сессии через callback"""
    await cmd_sessions(callback.message)
    await callback.answer()


@router.callback_query(F.data == "logout")
async def logout_callback(callback: CallbackQuery):
    """Выход через callback"""
    session_manager = getattr(callback.bot, 'session_manager', None)

    if not session_manager:
        await callback.answer("❌ Ошибка системы", show_alert=True)
        return

    if await session_manager.end_session(callback.from_user.id):
        await callback.message.edit_text(
            "✅ Вы успешно вышли из системы.\n"
            "Для доступа к функциям нужно авторизоваться заново."
        )
    else:
        await callback.answer("ℹ️ У вас нет активной сессии", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "extend_session")
async def extend_session_callback(callback: CallbackQuery):
    """Продление сессии"""
    await callback.answer("⏳ Функция продления сессии в разработке", show_alert=True)