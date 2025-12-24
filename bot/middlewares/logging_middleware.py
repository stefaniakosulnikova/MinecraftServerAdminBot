# bot/middlewares/logging_middleware.py
from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from loggers.app_logger import logger
from config.settings import settings


class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования входящих событий"""

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any]
    ) -> Any:

        # Определяем тип события
        if isinstance(event.event, Message):
            event_type = "message"
            user_id = event.event.from_user.id
            content = event.event.text or "[без текста]"
        elif isinstance(event.event, CallbackQuery):
            event_type = "callback"
            user_id = event.event.from_user.id
            content = event.event.data
        else:
            event_type = type(event.event).__name__.lower()
            user_id = getattr(event.event.from_user, 'id', None) if hasattr(event.event, 'from_user') else None
            content = str(event.event)[:100]

        # Логируем если включено
        if settings.LOG_ALL_MESSAGES and user_id:
            logger.log_telegram_event(
                event_type=event_type,
                user_id=user_id,
                data=content[:200] if content else "[пусто]"
            )

        # Продолжаем обработку
        return await handler(event, data)