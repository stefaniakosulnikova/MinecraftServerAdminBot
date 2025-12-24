from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.keyboards.monitoring_menu import get_monitoring_keyboard

router = Router()


@router.message(Command("monitor"))
async def cmd_monitor(message: Message):
    """Мониторинг сервера"""
    # Получаем session_manager из бота
    session_manager = getattr(message.bot, 'session_manager', None)

    if not session_manager:
        await message.answer("❌ Ошибка системы: менеджер сессий не доступен")
        return

    if not await session_manager.is_authorized(message.from_user.id):
        await message.answer("🔒 Сначала авторизуйтесь через /start")
        return

    # Заглушка - здесь будет реальный мониторинг
    text = (
        "📊 *Мониторинг сервера*\n\n"
        "🟢 Статус: Online\n"
        "👥 Игроки: 5/20\n"
        "⚡ TPS: 19.8\n"
        "💾 Память: 1.2/4.0 GB\n"
        "⏰ Аптайм: 12ч 34м\n"
        "🌡️ CPU: 45%\n\n"
        "_Данные обновляются каждые 5 минут_"
    )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_monitoring_keyboard()
    )


@router.callback_query(F.data == "monitoring")
async def monitoring_callback(callback: CallbackQuery):
    """Колбэк для мониторинга"""
    await cmd_monitor(callback.message)
    await callback.answer()


@router.callback_query(F.data == "refresh_monitor")
async def refresh_monitor_callback(callback: CallbackQuery):
    """Обновление данных мониторинга"""
    await cmd_monitor(callback.message)
    await callback.answer("🔄 Данные обновлены")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Статистика сервера"""
    session_manager = getattr(message.bot, 'session_manager', None)

    if not session_manager:
        await message.answer("❌ Ошибка системы: менеджер сессий не доступен")
        return

    if not await session_manager.is_authorized(message.from_user.id):
        await message.answer("🔒 Сначала авторизуйтесь через /start")
        return

    text = (
        "📈 *Статистика сервера*\n\n"
        "• Запусков сегодня: 1\n"
        "• Всего игроков: 42\n"
        "• Средний онлайн: 8\n"
        "• Максимальный онлайн: 18\n"
        "• Ошибок за сутки: 2\n\n"
        "_Статистика собирается с момента запуска бота_"
    )

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("players"))
async def cmd_players(message: Message):
    """Информация об игроках"""
    session_manager = getattr(message.bot, 'session_manager', None)

    if not session_manager:
        await message.answer("❌ Ошибка системы: менеджер сессий не доступен")
        return

    if not await session_manager.is_authorized(message.from_user.id):
        await message.answer("🔒 Сначала авторизуйтесь через /start")
        return

    text = (
        "👥 *Игроки онлайн*\n\n"
        "1. Player1 (2ч 15м)\n"
        "2. Player2 (1ч 30м)\n"
        "3. Player3 (45м)\n"
        "4. Player4 (20м)\n"
        "5. Player5 (5м)\n\n"
        "Всего: 5/20 игроков"
    )

    await message.answer(text, parse_mode="Markdown")