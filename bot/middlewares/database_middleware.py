from aiogram import BaseMiddleware
from aiogram.types import Update
from typing import Callable, Dict, Any, Awaitable

from infrastructure.adapters.database import Database


class DatabaseMiddleware(BaseMiddleware):
    """Middleware для предоставления доступа к базе данных"""

    def __init__(self, database: Database):
        super().__init__()
        self.database = database

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any]
    ) -> Any:
        # Добавляем БД в данные обработчика
        data['database'] = self.database

        # Добавляем быстрый доступ к репозиториям
        try:
            async with self.database.session_scope() as repos:
                data['repositories'] = repos
                return await handler(event, data)
        except Exception as e:
            # Если что-то пошло не так, все равно передаем БД
            return await handler(event, data)