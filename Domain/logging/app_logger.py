import logging
from datetime import datetime
from pathlib import Path


class AppLogger:
    """Простой логгер для записи событий бота"""

    def __init__(self, log_dir: str = "logs"):
        """
        Инициализация логгера
        :param log_dir: Папка для логов (по умолчанию "logs")
        """
        # Создаём папку для логов, если её нет
        Path(log_dir).mkdir(exist_ok=True)

        # Настраиваем базовый логгер
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler(Path(log_dir) / 'bot.log'),
                logging.StreamHandler()  # Вывод в консоль
            ]
        )

        self.logger = logging.getLogger('minecraft_bot')

    def log_command(self, command: str, user: str = "", success: bool = True):
        """Логируем выполнение команды"""
        status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
        user_info = f" ({user})" if user else ""

        message = f"КОМАНДА{user_info}: {command} - {status}"
        self.logger.info(message)

    def log_server_status(self, online: bool, players: int, tps: float):
        """Логируем статус сервера"""
        status = "🟢 ONLINE" if online else "🔴 OFFLINE"
        message = f"СТАТУС: {status} | Игроки: {players} | TPS: {tps}"
        self.logger.info(message)

    def log_error(self, error_msg: str, where: str = ""):
        """Логируем ошибку"""
        location = f" [{where}]" if where else ""
        self.logger.error(f"ОШИБКА{location}: {error_msg}")

    def info(self, message: str):
        """Общее информационное сообщение"""
        self.logger.info(f"ИНФО: {message}")

    def warning(self, message: str):
        """Предупреждение"""
        self.logger.warning(f"ВНИМАНИЕ: {message}")


# Создаём глобальный экземпляр логгера для удобства
# Теперь можно импортировать logger и сразу использовать
logger = AppLogger()