# infrastructure/adapters/rcon_client.py
import asyncio
import socket
from typing import Optional, Tuple
from rcon.source import rcon as rcon_async
from rcon.exceptions import EmptyResponse, SessionTimeout, WrongPassword

from loggers.app_logger import logger
from config.settings import settings


class RconClientAdapter:
    """
    Адаптер для работы с RCON протоколом Minecraft серверов.
    """

    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password

    async def test_connection(self) -> Tuple[bool, str]:
        """
        Детальная проверка подключения к RCON серверу

        Returns:
            Tuple[bool, str]: (успешность подключения, детальное сообщение)
        """
        logger.info(f"🔍 Детальная проверка RCON: {self.host}:{self.port}")

        # Если режим разработки - пропускаем реальную проверку
        if settings.DEBUG and hasattr(settings, 'DEV_SKIP_RCON_CHECK') and settings.DEV_SKIP_RCON_CHECK:
            logger.info(f"[DEV MODE] Пропускаем реальную RCON проверку")
            return True, "Режим разработки: проверка пропущена"

        # 1. Проверка DNS разрешения
        try:
            logger.info("  1. Проверка DNS...")
            ip_address = socket.gethostbyname(self.host)
            logger.info(f"     ✅ DNS разрешен: {self.host} -> {ip_address}")
        except socket.gaierror:
            error_msg = f"DNS ошибка: хост '{self.host}' не найден"
            logger.error(f"     ❌ {error_msg}")
            return False, error_msg

        # 2. Проверка доступности порта
        try:
            logger.info(f"  2. Проверка порта {self.port}...")
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5.0
            )
            writer.close()
            await writer.wait_closed()
            logger.info(f"     ✅ Порт {self.port} доступен")
        except asyncio.TimeoutError:
            error_msg = f"Таймаут: сервер {self.host} не отвечает на порту {self.port}"
            logger.error(f"     ❌ {error_msg}")
            return False, error_msg
        except ConnectionRefusedError:
            error_msg = f"Соединение отклонено: порт {self.port} закрыт или сервер не запущен"
            logger.error(f"     ❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Ошибка подключения: {type(e).__name__}: {e}"
            logger.error(f"     ❌ {error_msg}")
            return False, error_msg

        # 3. Проверка RCON авторизации
        logger.info("  3. Проверка RCON авторизации...")
        try:
            # Пытаемся выполнить команду list с проверкой ответа
            response = await rcon_async(
                command="list",
                host=self.host,
                port=self.port,
                passwd=self.password,
                timeout=10
            )

            # Проверяем, что ответ содержит валидные данные
            if response is None:
                error_msg = "RCON: получен пустой ответ"
                logger.warning(f"     ⚠️  {error_msg}")
                return True, error_msg  # Считаем успехом, но с предупреждением

            response_str = str(response).strip().lower()

            # Проверяем типичные ответы Minecraft
            if "there are" in response_str and "players online" in response_str:
                logger.info(f"     ✅ RCON авторизация успешна")
                logger.info(f"       Ответ: {response[:100]}")
                return True, "RCON подключение успешно"
            elif "cannot execute" in response_str or "unknown command" in response_str:
                # Сервер ответил, но команда не распознана (может быть другая версия)
                logger.info(f"     ⚠️  Сервер ответил, но команда не распознана")
                logger.info(f"       Ответ: {response[:100]}")
                return True, "RCON подключение установлено (команда не распознана)"
            else:
                # Нестандартный ответ, но соединение есть
                logger.info(f"     ⚠️  Нестандартный ответ сервера")
                logger.info(f"       Ответ: {response[:100]}")
                return True, f"RCON подключение установлено: {response[:50]}..."

        except WrongPassword:
            error_msg = "Неверный пароль RCON"
            logger.error(f"     ❌ {error_msg}")
            return False, error_msg
        except SessionTimeout:
            error_msg = "Таймаут сессии RCON. Проверьте настройки сервера"
            logger.error(f"     ❌ {error_msg}")
            return False, error_msg
        except ConnectionRefusedError:
            error_msg = "RCON порт закрыт или сервер не принимает RCON соединения"
            logger.error(f"     ❌ {error_msg}")
            return False, error_msg
        except asyncio.TimeoutError:
            error_msg = "Таймаут ожидания ответа RCON"
            logger.error(f"     ❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = self._parse_rcon_error(e)
            logger.error(f"     ❌ {error_msg}")
            return False, error_msg

    async def execute_command(self, command: str) -> str:
        """
        Выполняет команду на сервере с повторными попытками
        """
        return await self._execute_with_retry(command)

    async def send_command(self, command: str) -> Tuple[bool, str]:
        """
        Выполняет команду и возвращает результат
        """
        try:
            result = await self.execute_command(command)
            return True, result
        except Exception as e:
            error_msg = self._parse_rcon_error(e)
            return False, f"Ошибка: {error_msg}"

    async def _execute_with_retry(self, command: str) -> str:
        """
        Внутренний метод с повторными попытками
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
                return ""
            except Exception as e:
                last_exception = e
                logger.warning(f"Попытка {attempt + 1} неудачна: {e}")
                if attempt < settings.RCON_MAX_RETRIES - 1:
                    await asyncio.sleep(settings.RCON_RETRY_DELAY)

        raise last_exception or Exception("Все попытки выполнения команды неудачны")

    def _parse_rcon_error(self, error: Exception) -> str:
        """
        Парсинг ошибок RCON для понятного сообщения
        """
        error_str = str(error).lower()

        if "wrong password" in error_str or "incorrect password" in error_str:
            return "Неверный пароль RCON"
        elif "connection refused" in error_str:
            return "Соединение отклонено. Проверьте RCON порт"
        elif "timed out" in error_str:
            return "Таймаут ожидания ответа"
        elif "authentication" in error_str:
            return "Ошибка аутентификации RCON"
        elif isinstance(error, WrongPassword):
            return "Неверный пароль RCON"
        elif isinstance(error, SessionTimeout):
            return "Таймаут сессии RCON"
        else:
            return f"Ошибка RCON: {type(error).__name__}: {error}"

    async def get_server_status(self) -> dict:
        """
        Получение статуса сервера с проверкой
        """
        status = {
            "online": False,
            "players": "0/0",
            "version": "Неизвестно",
            "motd": "Неизвестно",
            "error": None
        }

        try:
            # Проверяем базовое подключение
            success, message = await self.test_connection()

            if not success:
                status["error"] = message
                return status

            status["online"] = True

            # Получаем список игроков
            try:
                list_response = await self.execute_command("list")
                if list_response:
                    import re
                    # Ищем паттерн "There are X/Y players online:"
                    match = re.search(r'(\d+)/(\d+)', list_response)
                    if match:
                        status["players"] = f"{match.group(1)}/{match.group(2)}"
            except:
                pass

            # Получаем версию
            try:
                version_response = await self.execute_command("version")
                if version_response:
                    status["version"] = version_response.split('\n')[0]
            except:
                pass

            return status

        except Exception as e:
            status["error"] = str(e)
            return status


# Фабрика с улучшенной проверкой
class RconClientFactory:
    @staticmethod
    async def create_and_test(host: str, port: int, password: str) -> Tuple[
        Optional['RconClientAdapter'], Optional[str]]:
        """
        Создает клиент и выполняет полную проверку
        """
        client = RconClientAdapter(host, port, password)
        success, message = await client.test_connection()

        if success:
            return client, None
        else:
            return None, message