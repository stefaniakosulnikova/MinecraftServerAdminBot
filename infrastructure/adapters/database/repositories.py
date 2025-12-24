# infrastructure/adapters/database/repositories.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    ServerModel, UserSessionModel, AdminModel,
    CommandLogModel, ServerStatsModel
)


class ServerRepository:
    """Репозиторий для работы с серверами"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_server(self, user_id: int, host: str, port: int,
                          encrypted_password: bytes, name: str = None) -> ServerModel:
        """Сохранение или обновление сервера"""
        # Ищем существующий сервер
        stmt = select(ServerModel).where(
            ServerModel.user_id == user_id,
            ServerModel.host == host,
            ServerModel.port == port
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Обновляем существующий
            existing.encrypted_password = encrypted_password
            existing.name = name or existing.name
            existing.updated_at = datetime.utcnow()
            server = existing
        else:
            # Создаем новый
            server = ServerModel(
                user_id=user_id,
                host=host,
                port=port,
                encrypted_password=encrypted_password,
                name=name
            )
            self.session.add(server)

        await self.session.flush()
        return server

    async def get_server(self, server_id: int) -> Optional[ServerModel]:
        """Получение сервера по ID"""
        stmt = select(ServerModel).where(ServerModel.id == server_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_servers(self, user_id: int) -> List[ServerModel]:
        """Получение всех серверов пользователя"""
        stmt = select(ServerModel).where(
            ServerModel.user_id == user_id,
            ServerModel.is_active == True
        ).order_by(ServerModel.created_at.desc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_server(self, server_id: int, user_id: int) -> bool:
        """Удаление сервера (только если принадлежит пользователю)"""
        stmt = delete(ServerModel).where(
            ServerModel.id == server_id,
            ServerModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0


class SessionRepository:
    """Репозиторий для работы с сессиями"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, user_id: int, server_id: int,
                             duration_hours: int = 6) -> UserSessionModel:
        """Создание новой сессии"""
        # Удаляем старую сессию если есть
        await self.delete_user_session(user_id)

        # Создаем новую
        session = UserSessionModel(
            user_id=user_id,
            server_id=server_id,
            expires_at=datetime.utcnow() + timedelta(hours=duration_hours),
            token=self._generate_token(),
            last_activity=datetime.utcnow()
        )

        self.session.add(session)
        await self.session.flush()
        return session

    async def get_active_session(self, user_id: int) -> Optional[UserSessionModel]:
        """Получение активной сессии пользователя"""
        stmt = select(UserSessionModel).where(
            UserSessionModel.user_id == user_id,
            UserSessionModel.expires_at > datetime.utcnow()
        )
        result = await self.session.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            # Обновляем время последней активности
            session.last_activity = datetime.utcnow()
            await self.session.flush()

        return session

    async def delete_user_session(self, user_id: int) -> bool:
        """Удаление сессии пользователя"""
        stmt = delete(UserSessionModel).where(UserSessionModel.user_id == user_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def cleanup_expired_sessions(self) -> int:
        """Очистка просроченных сессий"""
        stmt = delete(UserSessionModel).where(
            UserSessionModel.expires_at <= datetime.utcnow()
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    def _generate_token(self) -> str:
        """Генерация токена сессии"""
        import secrets
        return secrets.token_urlsafe(32)


class AdminRepository:
    """Репозиторий для работы с администраторами"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        stmt = select(AdminModel).where(AdminModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def add_admin(self, user_id: int, username: str = None,
                        added_by: int = None, is_superadmin: bool = False) -> AdminModel:
        """Добавление администратора"""
        # Проверяем, не является ли уже админом
        existing = await self.is_admin(user_id)
        if existing:
            # Обновляем существующего
            stmt = select(AdminModel).where(AdminModel.user_id == user_id)
            result = await self.session.execute(stmt)
            admin = result.scalar_one_or_none()
            if admin:
                admin.username = username or admin.username
                admin.is_superadmin = is_superadmin
                return admin

        # Создаем нового
        admin = AdminModel(
            user_id=user_id,
            username=username,
            added_by=added_by,
            is_superadmin=is_superadmin
        )
        self.session.add(admin)
        await self.session.flush()
        return admin

    async def remove_admin(self, user_id: int) -> bool:
        """Удаление администратора"""
        stmt = delete(AdminModel).where(AdminModel.user_id == user_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def get_all_admins(self) -> List[AdminModel]:
        """Получение всех администраторов"""
        stmt = select(AdminModel).order_by(AdminModel.added_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class CommandLogRepository:
    """Репозиторий для логов команд"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_command(self, server_id: int, user_id: int, command: str,
                          response: str = None, success: bool = True,
                          execution_time: int = None) -> CommandLogModel:
        """Логирование выполнения команды"""
        log = CommandLogModel(
            server_id=server_id,
            user_id=user_id,
            command=command[:500],  # Обрезаем если слишком длинная
            response=response[:10000] if response else None,  # Ограничиваем размер
            success=success,
            execution_time=execution_time
        )

        self.session.add(log)
        await self.session.flush()
        return log

    async def get_user_command_history(self, user_id: int, limit: int = 50) -> List[CommandLogModel]:
        """История команд пользователя"""
        stmt = select(CommandLogModel).where(
            CommandLogModel.user_id == user_id
        ).order_by(
            CommandLogModel.created_at.desc()
        ).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_server_command_history(self, server_id: int, limit: int = 100) -> List[CommandLogModel]:
        """История команд для сервера"""
        stmt = select(CommandLogModel).where(
            CommandLogModel.server_id == server_id
        ).order_by(
            CommandLogModel.created_at.desc()
        ).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class StatsRepository:
    """Репозиторий для статистики серверов"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_stats(self, server_id: int, online: bool, player_count: int = 0,
                         max_players: int = 20, tps: float = 20.0,
                         memory_used_mb: int = 0) -> ServerStatsModel:
        """Сохранение статистики сервера"""
        stats = ServerStatsModel(
            server_id=server_id,
            online=online,
            player_count=player_count,
            max_players=max_players,
            tps=int(tps * 10),  # Сохраняем как integer (20.0 -> 200)
            memory_used_mb=memory_used_mb
        )

        self.session.add(stats)
        await self.session.flush()
        return stats

    async def get_server_stats(self, server_id: int, hours: int = 24) -> List[ServerStatsModel]:
        """Получение статистики сервера за период"""
        time_threshold = datetime.utcnow() - timedelta(hours=hours)

        stmt = select(ServerStatsModel).where(
            ServerStatsModel.server_id == server_id,
            ServerStatsModel.created_at >= time_threshold
        ).order_by(ServerStatsModel.created_at.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_server_uptime(self, server_id: int, hours: int = 24) -> float:
        """Расчет аптайма сервера за период"""
        time_threshold = datetime.utcnow() - timedelta(hours=hours)

        # Подсчитываем статусы
        stmt = select(
            func.count().label('total'),
            func.sum(func.cast(ServerStatsModel.online, int)).label('online')
        ).where(
            ServerStatsModel.server_id == server_id,
            ServerStatsModel.created_at >= time_threshold
        )

        result = await self.session.execute(stmt)
        row = result.fetchone()

        if row and row.total > 0:
            return (row.online or 0) / row.total * 100
        return 0.0