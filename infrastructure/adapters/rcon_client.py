# infrastructure/adapters/rcon_client.py
import asyncio
from typing import Optional, Tuple
from rcon.source import rcon as rcon_async
from rcon.exceptions import EmptyResponse, SessionTimeout

from loggers.app_logger import logger
from config.settings import settings


class RconClientAdapter:
    """
    Адаптер для работы с RCON протоколом Minecraft серверов.
    Объединяет функционал из rcon_client.py и rcon_service.py
    """

    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password

    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Проверка подключения к RCON серверу с детальной отладкой

        Returns:
            Tuple[bool, Optional[str]]: (успешность подключения, сообщение об ошибке)
        """
        logger.info(f"🔍 Попытка подключения к RCON: {self.host}:{self.port}")

        # Если режим разработки - пропускаем проверку
        if settings.DEBUG and hasattr(settings, 'DEV_SKIP_RCON_CHECK') and settings.DEV_SKIP_RCON_CHECK:
            logger.info(f"[DEV MODE] Пропускаем RCON проверку для {self.host}:{self.port}")
            return True, None

        # 1. Сначала проверяем доступность хоста и порта
        try:
            logger.info(f"   Проверка доступности {self.host}:{self.port}...")
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=settings.RCON_TIMEOUT
            )
            writer.close()
            await writer.wait_closed()
            logger.info("   ✅ Хост и порт доступны")
        except asyncio.TimeoutError:
            error_msg = "Таймаут подключения к хосту"
            logger.error(f"   ❌ {error_msg}")
            return False, error_msg
        except ConnectionRefusedError:
            error_msg = "Подключение отклонено. Сервер не запущен или порт закрыт"
            logger.error(f"   ❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Ошибка подключения: {type(e).__name__}: {e}"
            logger.error(f"   ❌ {error_msg}")
            return False, error_msg

        # 2. Тестируем RCON авторизацию и выполнение команды
        logger.info(f"   Тестируем RCON авторизацию...")
        try:
            # Пробуем выполнить простую команду
            response = await self._execute_rcon_command("list")

            if response:
                logger.info(f"   ✅ RCON подключение успешно")
                logger.info(f"   Ответ сервера: {response[:100]}...")
                return True, None
            else:
                warning_msg = "Сервер ответил пустым сообщением"
                logger.warning(f"   ⚠️  {warning_msg}")
                return True, warning_msg  # Считаем успехом, но с предупреждением

        except Exception as e:
            error_msg = self._parse_rcon_error(e)
            logger.error(f"   ❌ {error_msg}")
            return False, error_msg

    async def execute_command(self, command: str) -> str:
        """
        Выполняет команду на сервере

        Args:
            command: Команда для выполнения

        Returns:
            str: Ответ сервера или сообщение об ошибке
        """
        try:
            response = await self._execute_rcon_command(command)
            return response or "Команда выполнена"
        except Exception as e:
            error_msg = self._parse_rcon_error(e)
            return f"❌ Ошибка выполнения команды: {error_msg}"

    async def send_command(self, command: str) -> Tuple[bool, str]:
        """
        Альтернативное название для execute_command (для обратной совместимости)

        Returns:
            Tuple[bool, str]: (успех, результат/ошибка)
        """
        try:
            result = await self.execute_command(command)
            return True, result
        except Exception as e:
            error_msg = self._parse_rcon_error(e)
            return False, f"Ошибка: {error_msg}"

    async def _execute_rcon_command(self, command: str) -> str:
        """
        Внутренний метод выполнения RCON команды с повторными попытками

        Args:
            command: Команда для выполнения

        Returns:
            str: Ответ сервера

        Raises:
            Exception: При ошибке выполнения после всех попыток
        """
        last_exception = None

        for attempt in range(settings.RCON_MAX_RETRIES):
            try:
                logger.debug(f"RCON команда [{attempt + 1}/{settings.RCON_MAX_RETRIES}]: {command}")

                response = await rcon_async(
                    command=command,
                    host=self.host,
                    port=self.port,
                    passwd=self.password,
                    timeout=settings.RCON_TIMEOUT
                )
                return response.strip() if response else ""

            except EmptyResponse:
                # Пустой ответ - не ошибка для некоторых команд
                logger.debug("RCON: получен пустой ответ")
                return ""
            except SessionTimeout as e:
                last_exception = e
                logger.warning(f"RCON таймаут [{attempt + 1}/{settings.RCON_MAX_RETRIES}]")
                if attempt < settings.RCON_MAX_RETRIES - 1:
                    await asyncio.sleep(settings.RCON_RETRY_DELAY)
            except Exception as e:
                last_exception = e
                logger.error(f"RCON ошибка [{attempt + 1}/{settings.RCON_MAX_RETRIES}]: {e}")
                if attempt < settings.RCON_MAX_RETRIES - 1:
                    await asyncio.sleep(settings.RCON_RETRY_DELAY)

        # Если дошли сюда - все попытки неудачны
        raise last_exception or Exception("Неизвестная ошибка RCON")

    def _parse_rcon_error(self, error: Exception) -> str:
        """
        Анализ ошибки RCON и возврат понятного сообщения

        Args:
            error: Исключение

        Returns:
            str: Понятное описание ошибки
        """
        error_str = str(error).lower()

        if "connection refused" in error_str:
            return "Сервер не принимает подключения"
        elif "timed out" in error_str:
            return "Таймаут ожидания ответа от сервера"
        elif "incorrect" in error_str or "password" in error_str:
            return "Неверный пароль RCON"
        elif "authentication" in error_str:
            return "Ошибка аутентификации RCON"
        elif "empty response" in error_str:
            return "Пустой ответ от сервера"
        elif isinstance(error, SessionTimeout):
            return "Таймаут сессии RCON"
        else:
            return f"{type(error).__name__}: {error}"

    async def get_server_info(self) -> dict:
        """
        Получение базовой информации о сервере

        Returns:
            dict: Информация о сервере
        """
        info = {
            "host": self.host,
            "port": self.port,
            "online": False,
            "players": "0/0",
            "version": "Неизвестно",
            "motd": "Неизвестно"
        }

        try:
            # Пробуем получить список игроков
            list_response = await self.execute_command("list")
            if list_response and "players online" in list_response.lower():
                info["online"] = True

                # Парсим информацию об игроках
                # Пример ответа: "There are 2/20 players online:"
                import re
                match = re.search(r'(\d+)/(\d+)', list_response)
                if match:
                    info["players"] = f"{match.group(1)}/{match.group(2)}"

            # Пробуем получить версию
            version_response = await self.execute_command("version")
            if version_response:
                info["version"] = version_response.split('\n')[0] if '\n' in version_response else version_response

            # Пробуем получить MOTD (если есть плагин)
            try:
                motd_response = await self.execute_command("motd")
                if motd_response:
                    info["motd"] = motd_response
            except:
                pass

        except Exception as e:
            logger.warning(f"Не удалось получить информацию о сервере: {e}")

        return info


# Фабрика для создания RCON клиентов (для удобства)
class RconClientFactory:
    """Фабрика для создания RCON клиентов"""

    @staticmethod
    async def create_and_test(host: str, port: int, password: str) -> Tuple[Optional[RconClientAdapter], Optional[str]]:
        """
        Создает и тестирует RCON клиент

        Returns:
            Tuple[Optional[RconClientAdapter], Optional[str]]: (клиент, ошибка)
        """
        client = RconClientAdapter(host, port, password)
        success, error = await client.test_connection()

        if success:
            return client, None
        else:
            return None, error