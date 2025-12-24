import asyncio
from rcon.source import rcon as rcon_async
from bot.config import Config


class RconService:
    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password

    async def test_connection(self) -> bool:
        """Проверяет подключение к RCON серверу"""
        
        # Если режим разработки - пропускаем проверку
        if hasattr(Config, 'DEVELOPMENT_MODE') and Config.DEVELOPMENT_MODE:
            print(f"[DEV MODE] Пропускаем RCON проверку для {self.host}:{self.port}")
            return True
        
        # Реальная проверка
        try:
            response = await self._execute_rcon_command("list")
            return response is not None and "error" not in response.lower()
        except Exception as e:
            print(f"RCON ошибка: {e}")
            return False

    async def _execute_rcon_command(self, command: str) -> str:
        """Выполняет команду RCON (асинхронная версия)"""
        try:
            response = await rcon_async(
                command=command,
                host=self.host,
                port=self.port,
                passwd=self.password
            )
            return response
        except Exception as e:
            raise e

    async def execute_command(self, command: str) -> str:
        """Выполняет команду на сервере"""
        try:
            response = await self._execute_rcon_command(command)
            return response or "Команда выполнена"
        except Exception as e:
            return f"Ошибка: {str(e)}"
