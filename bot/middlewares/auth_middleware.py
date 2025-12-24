# bot/middlewares/auth_middleware.py
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from aiogram.fsm.context import FSMContext

from domain.services.session_manager import session_manager


class AuthMiddleware(BaseMiddleware):
    """Middleware для проверки авторизации"""

    def __init__(self):
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        if not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id

        # 1. Пропускаем команду /start
        if isinstance(event, Message) and event.text:
            command = event.text.strip().lower()
            if command == '/start' or command.startswith('/start '):
                return await handler(event, data)

        # 2. Пропускаем команду /help
        if isinstance(event, Message) and event.text:
            command = event.text.strip().lower()
            if command == '/help' or command.startswith('/help '):
                return await handler(event, data)

        # 3. Пропускаем публичные callback'ы для начала авторизации
        if isinstance(event, CallbackQuery):
            public_callbacks = ['auth_start', 'auth_cancel', 'help', 'main_menu']
            if event.data in public_callbacks:
                return await handler(event, data)

        # 4. Пропускаем сообщения, которые находятся в процессе FSM-авторизации
        if isinstance(event, Message):
            # Получаем состояние FSM из data
            state: FSMContext = data.get('state')
            if state:
                # Получаем текущее состояние
                current_state = await state.get_state()
                # Если пользователь находится в процессе авторизации - пропускаем
                if current_state and 'AuthStates' in str(current_state):
                    return await handler(event, data)

        if not session_manager.is_authorized(user_id):
            if isinstance(event, Message):
                await event.answer("🔒 Требуется авторизация. Используйте /start")
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "🔒 Доступ ограничен. Используйте /start для авторизации.",
                    show_alert=True
                )
            return

        return await handler(event, data)