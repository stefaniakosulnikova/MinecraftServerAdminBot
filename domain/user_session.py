from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserSession:
    """Модель сессии пользователя."""
    user_id: int
    server_key: str
    expires_at: datetime

    def is_active(self) -> bool:
        return datetime.utcnow() < self.expires_at
