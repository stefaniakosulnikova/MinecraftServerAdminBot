# infrastructure/adapters/database/database.py
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, AsyncGenerator
from datetime import datetime, timedelta

from .connection import DatabaseConnection
from .models import Base
from .repositories import (
    ServerRepository, SessionRepository, AdminRepository,
    CommandLogRepository, StatsRepository
)


class Database:
    """Основной класс для работы с базой данных"""

    def __init__(self, database_url: str = None, echo: bool = False):
        self.connection = DatabaseConnection(database_url, echo)
        self._initialized = False

    async def initialize(self):
        """Инициализация базы данных"""
        if not self._initialized:
            await self.connection.connect()
            await self._create_tables()
            self._initialized = True

    async def _create_tables(self):
        """Создание таблиц в БД"""
        async with self.connection.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("✅ Таблицы базы данных созданы/проверены")

    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Контекстный менеджер для работы с репозиториями.

        Использование:
        async with database.session_scope() as repos:
            server = await repos['servers'].save_server(...)
            session = await repos['sessions'].create_session(...)
        """
        if not self._initialized:
            await self.initialize()

        async with self.connection.get_session() as session:
            # Создаем репозитории для этой сессии
            repos = {
                'servers': ServerRepository(session),
                'sessions': SessionRepository(session),
                'admins': AdminRepository(session),
                'logs': CommandLogRepository(session),
                'stats': StatsRepository(session),
                'raw': session  # Для прямых SQL запросов если нужно
            }

            yield repos

    async def get_servers_repo(self) -> ServerRepository:
        """Быстрый доступ к репозиторию серверов"""
        async with self.connection.get_session() as session:
            return ServerRepository(session)

    async def get_sessions_repo(self) -> SessionRepository:
        """Быстрый доступ к репозиторию сессий"""
        async with self.connection.get_session() as session:
            return SessionRepository(session)

    async def get_admins_repo(self) -> AdminRepository:
        """Быстрый доступ к репозиторию админов"""
        async with self.connection.get_session() as session:
            return AdminRepository(session)

    async def cleanup(self):
        """Очистка устаревших данных"""
        async with self.session_scope() as repos:
            # Очищаем просроченные сессии
            expired_count = await repos['sessions'].cleanup_expired_sessions()

            # Очищаем старые логи (старше 30 дней)
            thirty_days_ago = datetime.now() - timedelta(days=30)

            # Очищаем старую статистику (старше 7 дней)
            seven_days_ago = datetime.now() - timedelta(days=7)

            if expired_count > 0:
                print(f"🧹 Удалено {expired_count} просроченных сессий")

    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики базы данных"""
        async with self.session_scope() as repos:
            stats = {}

            # Подсчет записей в таблицах
            for table_name, repo in repos.items():
                if hasattr(repo, '__class__'):
                    table_name = repo.__class__.__name__.replace('Repository', '').lower()
                    # Здесь можно добавить подсчет записей

            return stats

    async def close(self):
        """Закрытие соединений"""
        await self.connection.disconnect()

    async def backup(self, backup_path: str = None):
        """Создание бэкапа базы данных (для SQLite)"""
        if "sqlite" in str(self.connection.engine.url):
            import shutil
            import os

            # Получаем путь к файлу БД
            db_path = str(self.connection.engine.url).split("///")[-1]

            if os.path.exists(db_path):
                if not backup_path:
                    backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                # Закрываем соединения перед бэкапом
                await self.close()

                # Копируем файл
                shutil.copy2(db_path, backup_path)
                print(f"✅ Бэкап создан: {backup_path}")

                # Переподключаемся
                await self.initialize()