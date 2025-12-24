# infrastructure/adapters/database/models.py
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    Boolean, Text, LargeBinary, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class ServerModel(Base):
    """Модель сервера Minecraft"""
    __tablename__ = 'servers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)  # ID пользователя Telegram
    name = Column(String(100), nullable=True)  # Имя сервера (для отображения)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False, default=25575)
    encrypted_password = Column(LargeBinary, nullable=False)  # Зашифрованный RCON пароль
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Один пользователь может иметь только один сервер с таким host:port
    __table_args__ = (
        UniqueConstraint('user_id', 'host', 'port', name='uq_user_server'),
        Index('idx_server_user_host', 'user_id', 'host'),
    )

    # Связи
    sessions = relationship("UserSessionModel", back_populates="server", cascade="all, delete-orphan")
    commands = relationship("CommandLogModel", back_populates="server", cascade="all, delete-orphan")


class UserSessionModel(Base):
    """Модель сессии пользователя"""
    __tablename__ = 'user_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)  # Одна сессия на пользователя
    server_id = Column(Integer, ForeignKey('servers.id', ondelete="CASCADE"), nullable=False)
    token = Column(String(64), nullable=True)  # Токен сессии (можно использовать для API)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    server = relationship("ServerModel", back_populates="sessions")

    __table_args__ = (
        Index('idx_session_expires', 'expires_at'),
        Index('idx_session_user_server', 'user_id', 'server_id'),
    )


class AdminModel(Base):
    """Модель администратора (белый список)"""
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=True)  # Имя пользователя Telegram
    is_superadmin = Column(Boolean, default=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    added_by = Column(Integer, nullable=True)  # Кто добавил этого админа


class CommandLogModel(Base):
    """Лог выполненных RCON команд"""
    __tablename__ = 'command_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(Integer, ForeignKey('servers.id', ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    command = Column(String(500), nullable=False)
    response = Column(Text, nullable=True)
    success = Column(Boolean, default=True)
    execution_time = Column(Integer)  # Время выполнения в миллисекундах
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Связи
    server = relationship("ServerModel", back_populates="commands")

    __table_args__ = (
        Index('idx_command_user', 'user_id', 'created_at'),
        Index('idx_command_server', 'server_id', 'created_at'),
    )


class ServerStatsModel(Base):
    """Статистика сервера (для мониторинга)"""
    __tablename__ = 'server_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(Integer, ForeignKey('servers.id', ondelete="CASCADE"), nullable=False)
    online = Column(Boolean, default=False)
    player_count = Column(Integer, default=0)
    max_players = Column(Integer, default=20)
    tps = Column(Integer, default=20)  # TPS * 10 для хранения как integer
    memory_used_mb = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_stats_server_time', 'server_id', 'created_at'),
    )