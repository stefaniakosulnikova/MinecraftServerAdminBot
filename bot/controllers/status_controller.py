from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.keyboards.status_menu import get_status_keyboard

router = Router()


@router.callback_query(F.data == "status")
async def status_callback(callback: CallbackQuery):
    status_text = (
        "📊 *Статус сервера*\n\n"
        "🟢 Сервер: Online\n"
        "👥 Игроки: 0/20\n"
        "⚡ TPS: 20.0\n"
        "💾 Память: 0.5/2.0 GB\n"
        "⏰ Аптайм: 0ч 5м\n\n"
        "_Функционал в разработке_"
    )

    await callback.message.edit_text(
        status_text,
        parse_mode="Markdown",
        reply_markup=get_status_keyboard()
    )
    await callback.answer()