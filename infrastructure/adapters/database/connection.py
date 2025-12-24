# infrastructure/adapters/database/connection.py
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker
)
from sqlalchemy.pool import NullPool


class DatabaseConnection:
    """Управление подключением к базе данных"""

    def __init__(self, database_url: str, echo: bool = False):
        """
        :param database_url: SQLAlchemy URL
        :param echo: Логировать SQL запросы
        """
        self.database_url = database_url
        self.echo = echo
        self.engine = None
        self.session_factory = None

    async def connect(self):
        """Создание engine и session factory"""
        # Для SQLite используем NullPool для асинхронности
        if "sqlite" in self.database_url:
            self.engine = create_async_engine(
                self.database_url,
                echo=self.echo,
                poolclass=NullPool,  # Важно для async SQLite
                connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
            )
        else:
            # Для PostgreSQL/MySQL
            self.engine = create_async_engine(
                self.database_url,
                echo=self.echo,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
            )

        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Тестируем подключение
        await self.test_connection()

    async def test_connection(self):
        """Тестирование подключения к БД"""
        try:
            async with self.session_factory() as session:
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
                print("✅ Подключение к БД успешно")
                return True
        except Exception as e:
            print(f"❌ Ошибка подключения к БД: {e}")
            return False

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Контекстный менеджер для получения сессии"""
        if not self.session_factory:
            await self.connect()

        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def disconnect(self):
        """Закрытие соединений"""
        if self.engine:
            await self.engine.dispose()
            print("🔌 Соединение с БД закрыто")