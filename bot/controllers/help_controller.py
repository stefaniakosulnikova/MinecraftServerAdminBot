from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📖 *Справка по командам:*\n\n"
        "*/start* - Главное меню\n"
        "*/help* - Эта справка\n"
        "*/status* - Статус сервера\n\n"
        "*Быстрые команды:*\n"
        "• /list - Список игроков\n"
        "• /save - Сохранить мир\n"
        "• /stop - Остановить сервер\n\n"
        "Для навигации также используйте кнопки меню."
    )

    await message.answer(help_text, parse_mode="Markdown")


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    help_text = (
        "📖 *Справка:*\n\n"
        "Используйте кнопки меню для навигации:\n"
        "• 📊 Статус сервера - информация о сервере\n"
        "• ⚡ Быстрые команды - частые действия\n"
        "• 📈 Мониторинг - статистика\n"
        "• 🔔 Уведомления - настройка оповещений"
    )

    await callback.message.edit_text(
        help_text,
        parse_mode="Markdown"
    )
    await callback.answer()