# custom_logging/app_logger.py
import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


class ColoredFormatter(logging.Formatter):
    """Кастомный форматтер с цветами"""

    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[41m',
        'RESET': '\033[0m'
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class MinecraftBotLogger:
    """Логгер для Minecraft Bot"""

    def __init__(self, name: str = "minecraft_bot", log_dir: str = "logs"):
        # Создаем папку для логов
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Настраиваем логгер
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Очищаем существующие обработчики
        self.logger.handlers.clear()

        # Форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        colored_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Консольный обработчик (цветной)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(colored_formatter)

        # Файловый обработчик
        file_handler = RotatingFileHandler(
            self.log_dir / 'bot.log',
            maxBytes=10_485_760,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # Добавляем обработчики
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

        self.info(f"Логгер инициализирован. Логи в: {self.log_dir.absolute()}")

    # Методы логирования
    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False):
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False):
        """Критическое сообщение с опциональным traceback"""
        self.logger.critical(message, exc_info=exc_info)

    def log_command(self, command: str, user_id: Optional[int] = None, success: bool = True):
        """Логирование команды"""
        user_info = f" 👤 {user_id}" if user_id else ""
        status = "✅" if success else "❌"
        self.info(f"Команда{user_info}: {command} {status}")

    def log_auth(self, user_id: int, server: str, success: bool):
        """Логирование авторизации"""
        status = "УСПЕШНО" if success else "ОШИБКА"
        self.info(f"Авторизация 👤 {user_id} 🌐 {server}: {status}")

    def log_telegram_event(self, event_type: str, user_id: int, data: str = None):
        """Логирование Telegram событий (заглушка для совместимости)"""
        # Просто логируем как обычное информационное сообщение
        self.info(f"Telegram event: {event_type} from user {user_id}")



# Создаем глобальный экземпляр
logger = MinecraftBotLogger()