import asyncio
from rcon.source import rcon

from loggers import logger


class RconClientAdapter:
    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password

    async def test_connection(self) -> bool:
        """Проверка подключения к RCON серверу с детальной отладкой"""
        logger.info(f"🔍 Попытка подключения к RCON: {self.host}:{self.port}")

        # 1. Сначала проверяем доступность хоста и порта
        try:
            logger.info(f"   Проверка доступности {self.host}:{self.port}...")
            # Пытаемся подключиться TCP сокетом
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5.0
            )
            writer.close()
            await writer.wait_closed()
            logger.info("   ✅ Хост и порт доступны")
        except asyncio.TimeoutError:
            logger.error("   ❌ Таймаут подключения к хосту")
            return False
        except ConnectionRefusedError:
            logger.error("   ❌ Подключение отклонено. Сервер не запущен или порт закрыт")
            return False
        except Exception as e:
            logger.error(f"   ❌ Ошибка подключения: {type(e).__name__}: {e}")
            return False

        # 2. Тестируем RCON подключение
        logger.info(f"   Тестируем RCON авторизацию...")
        try:
            response = await rcon(
                command="list",
                host=self.host,
                port=self.port,
                passwd=self.password,
                timeout=10
            )

            if response:
                logger.info(f"   ✅ RCON подключение успешно")
                logger.info(f"   Ответ сервера: {response[:100]}...")
                return True
            else:
                logger.warning("   ⚠️  Сервер ответил пустым сообщением")
                return False

        except Exception as e:
            logger.error(f"   ❌ Ошибка RCON: {type(e).__name__}: {e}")

            # Детализация ошибок
            if "Connection refused" in str(e):
                logger.error("   → Сервер не принимает подключения")
            elif "timed out" in str(e).lower():
                logger.error("   → Таймаут ожидания ответа")
            elif "incorrect" in str(e).lower() or "password" in str(e).lower():
                logger.error("   → Неверный пароль RCON")
            elif "authentication" in str(e).lower():
                logger.error("   → Ошибка аутентификации RCON")

            return False
