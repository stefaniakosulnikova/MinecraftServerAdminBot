# domain/services/session_manager.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from infrastructure.adapters.crypto import CryptoService


class SessionManager:
    """Менеджер сессий с интеграцией БД"""

    def __init__(self, database, session_duration_hours: int = 6):
        self.database = database
        self.session_duration = session_duration_hours
        self.crypto = CryptoService()
        self._memory_sessions: Dict[int, dict] = {}

    async def is_authorized(self, user_id: int) -> bool:
        """Проверка авторизации через БД"""
        # Сначала проверяем кэш
        if user_id in self._memory_sessions:
            session = self._memory_sessions[user_id]
            if session["is_active"] and datetime.now() < session["expires_at"]:
                return True
            else:
                del self._memory_sessions[user_id]

        # Проверяем в БД
        try:
            async with self.database.session_scope() as repos:
                session = await repos['sessions'].get_active_session(user_id)
                if session:
                    # Обновляем кэш
                    server = await repos['servers'].get_server(session.server_id)
                    if server:
                        self._memory_sessions[user_id] = {
                            "user_id": user_id,
                            "server_id": session.server_id,
                            "server_host": server.host,
                            "server_port": server.port,
                            "expires_at": session.expires_at,
                            "is_active": True
                        }
                    return True
        except Exception:
            pass
        return False

    async def create_session(self, user_id: int, host: str, port: int, password: str) -> bool:
        """Создание сессии с сохранением в БД"""
        try:
            # 1. Проверяем RCON подключение
            from infrastructure.adapters.rcon_client import RconClientAdapter
            rcon_client = RconClientAdapter(host, port, password)

            success, error = await rcon_client.test_connection()
            if not success:
                return False

            # 2. Шифруем пароль
            encrypted_password = self.crypto.encrypt(password)

            # 3. Сохраняем в БД
            async with self.database.session_scope() as repos:
                # Сохраняем/обновляем сервер
                server = await repos['servers'].save_server(
                    user_id=user_id,
                    host=host,
                    port=port,
                    encrypted_password=encrypted_password,
                    name=f"{host}:{port}"
                )

                # Создаем сессию
                await repos['sessions'].create_session(
                    user_id=user_id,
                    server_id=server.id,
                    duration_hours=self.session_duration
                )

                # Обновляем кэш
                self._memory_sessions[user_id] = {
                    "user_id": user_id,
                    "server_id": server.id,
                    "server_host": host,
                    "server_port": port,
                    "expires_at": datetime.now() + timedelta(hours=self.session_duration),
                    "is_active": True
                }

            return True

        except Exception as e:
            print(f"Ошибка создания сессии: {e}")
            return False

    async def get_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение сессии пользователя"""
        # Проверяем кэш
        if user_id in self._memory_sessions:
            session = self._memory_sessions[user_id]
            if session["is_active"] and datetime.now() < session["expires_at"]:
                return session

        # Получаем из БД
        try:
            async with self.database.session_scope() as repos:
                session_db = await repos['sessions'].get_active_session(user_id)
                if not session_db:
                    return None

                server = await repos['servers'].get_server(session_db.server_id)
                if not server:
                    return None

                session_data = {
                    "user_id": user_id,
                    "server_id": session_db.server_id,
                    "server_host": server.host,
                    "server_port": server.port,
                    "expires_at": session_db.expires_at,
                    "is_active": True
                }

                # Обновляем кэш
                self._memory_sessions[user_id] = session_data
                return session_data
        except Exception:
            return None

    async def get_server(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о сервере с паролем"""
        try:
            async with self.database.session_scope() as repos:
                session = await repos['sessions'].get_active_session(user_id)
                if not session:
                    return None

                server = await repos['servers'].get_server(session.server_id)
                if not server:
                    return None

                return {
                    "id": server.id,
                    "host": server.host,
                    "port": server.port,
                    "encrypted_password": server.encrypted_password,
                    "name": server.name
                }
        except Exception:
            return None

    async def end_session(self, user_id: int) -> bool:
        """Завершение сессии"""
        # Удаляем из кэша
        if user_id in self._memory_sessions:
            del self._memory_sessions[user_id]

        # Удаляем из БД
        try:
            async with self.database.session_scope() as repos:
                result = await repos['sessions'].delete_user_session(user_id)
                return result
        except Exception:
            return False

    async def get_remaining_time(self, user_id: int) -> Optional[str]:
        """Получение оставшегося времени сессии"""
        session = await self.get_session(user_id)
        if not session:
            return None

        remaining = session["expires_at"] - datetime.now()
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60

        return f"{hours}ч {minutes}м"