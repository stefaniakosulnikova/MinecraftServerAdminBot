# domain/use_cases/authorize_user.py
from datetime import datetime, timedelta
from infrastructure.adapters.crypto import CryptoService
from infrastructure.adapters.rcon_client import RconClientAdapter


class AuthorizeUserUseCase:
    def __init__(self, database):
        self.database = database
        self.crypto = CryptoService()

    async def execute(self, user_id: int, host: str, port: int, password: str) -> bool:
        # 1. Проверяем подключение через RCON
        rcon_client = RconClientAdapter(host, port, password)
        if not await rcon_client.test_connection():
            return False

        # 2. Шифруем пароль
        encrypted_password = self.crypto.encrypt(password)

        # 3. Сохраняем в БД
        async with self.database.session_scope() as repos:
            # Сохраняем сервер
            server = await repos['servers'].save_server(
                user_id=user_id,
                host=host,
                port=port,
                encrypted_password=encrypted_password,
                name=f"{host}:{port}"  # Автоматическое имя
            )

            # Создаем сессию
            session = await repos['sessions'].create_session(
                user_id=user_id,
                server_id=server.id,
                duration_hours=6
            )

            # Логируем событие
            await repos['logs'].log_command(
                server_id=server.id,
                user_id=user_id,
                command="auth",
                response="Авторизация успешна",
                success=True
            )

        return True