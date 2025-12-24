from datetime import datetime, timedelta
from typing import Dict, Optional


class SessionManager:
    """Менеджер сессий авторизации"""
    def __init__(self, session_duration_hours: int = 6):
        self.sessions: Dict[int, dict] = {}
        self.session_duration = session_duration_hours

    def create_session(self, user_id: int, server_host: str, server_port: int) -> dict:
        """Создание новой сессии"""
        expires_at = datetime.now() + timedelta(hours=self.session_duration)

        session = {
            "user_id": user_id,
            "server_host": server_host,
            "server_port": server_port,
            "created_at": datetime.now(),
            "expires_at": expires_at,
            "is_active": True
        }

        self.sessions[user_id] = session
        return session

    def get_session(self, user_id: int) -> Optional[dict]:
        """Получение сессии пользователя"""
        session = self.sessions.get(user_id)

        if session and session["is_active"] and datetime.now() < session["expires_at"]:
            return session
        elif session:
            del self.sessions[user_id]

        return None

    def end_session(self, user_id: int) -> bool:
        """Завершение сессии"""
        if user_id in self.sessions:
            del self.sessions[user_id]
            return True
        return False

    def is_authorized(self, user_id: int) -> bool:
        """Проверка авторизации пользователя"""
        session = self.get_session(user_id)
        if session and session["is_active"] and datetime.now() < session["expires_at"]:
            return True
        return False

    def get_remaining_time(self, user_id: int) -> Optional[str]:
        """Получение оставшегося времени сессии"""
        session = self.sessions.get(user_id)

        if session and session["is_active"] and datetime.now() < session["expires_at"]:
            return session
        elif session:
            # Удаляем просроченную сессию
            del self.sessions[user_id]

        return None


session_manager = SessionManager()