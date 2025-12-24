from dataclasses import dataclass

@dataclass
class Server:
    """Модель сервера. Связывает пользователя и его RCON данные."""
    server_key: str  # Уникальный ключ (например, host:port)
    user_id: int
    encrypted_password: bytes  # Зашифрованный пароль
    host: str
    port: int
