# config/settings.py
import os
import loggers
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()


class Settings:
    """Настройки приложения"""

    def __init__(self):
        # ================= TELEGRAM =================
        self.BOT_TOKEN = self._get_required("BOT_TOKEN")
        self.ADMIN_IDS = self._parse_int_list("ADMIN_IDS", [])
        self.BOT_NAME = self._get("BOT_NAME", "Minecraft Admin Bot")

        # ================= БАЗА ДАННЫХ ==============
        self.DATABASE_URL = self._get(
            "DATABASE_URL",
            "sqlite+aiosqlite:///./data/minecraft_bot.db"
        )
        self.DB_ECHO_SQL = self._get_bool("DB_ECHO_SQL", False)
        self.DB_CLEANUP_INTERVAL_HOURS = self._get_int("DB_CLEANUP_INTERVAL_HOURS", 1)

        # ================= ЛОГИРОВАНИЕ ==============
        log_dir_str = self._get("LOG_DIR", "./logs")
        self.LOG_DIR = Path(log_dir_str)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

        self.LOG_LEVEL_CONSOLE = self._get("LOG_LEVEL_CONSOLE", "INFO")
        self.LOG_LEVEL_FILE = self._get("LOG_LEVEL_FILE", "DEBUG")
        self.LOG_MAX_SIZE_MB = self._get_int("LOG_MAX_SIZE_MB", 10)
        self.LOG_BACKUP_COUNT = self._get_int("LOG_BACKUP_COUNT", 5)
        self.ENABLE_JSON_LOGS = self._get_bool("ENABLE_JSON_LOGS", False)

        # ================= RCON =====================
        self.RCON_TIMEOUT = self._get_int("RCON_TIMEOUT", 10)
        self.RCON_MAX_RETRIES = self._get_int("RCON_MAX_RETRIES", 3)
        self.RCON_RETRY_DELAY = self._get_int("RCON_RETRY_DELAY", 1)

        # ================= СЕССИИ ===================
        self.SESSION_DURATION_HOURS = self._get_int("SESSION_DURATION_HOURS", 6)
        self.SESSION_AUTO_RENEW = self._get_bool("SESSION_AUTO_RENEW", True)

        # ================= БЕЗОПАСНОСТЬ =============
        self.ENCRYPTION_KEY = self._get("ENCRYPTION_KEY", None)
        self.ALLOWED_HOSTS = self._parse_str_list("ALLOWED_HOSTS", ["localhost", "127.0.0.1"])
        self.BLOCK_SUSPICIOUS_IPS = self._get_bool("BLOCK_SUSPICIOUS_IPS", True)

        # ================= УВЕДОМЛЕНИЯ ==============
        self.NOTIFY_NEW_CONNECTIONS = self._get_bool("NOTIFY_NEW_CONNECTIONS", True)
        self.NOTIFY_SERVER_ERRORS = self._get_bool("NOTIFY_SERVER_ERRORS", True)
        self.NOTIFY_ADMIN_COMMANDS = self._get_bool("NOTIFY_ADMIN_COMMANDS", True)

        # ================= МОНИТОРИНГ ===============
        self.MONITORING_INTERVAL_MINUTES = self._get_int("MONITORING_INTERVAL_MINUTES", 5)
        self.TPS_WARNING_THRESHOLD = self._get_float("TPS_WARNING_THRESHOLD", 15.0)
        self.TPS_CRITICAL_THRESHOLD = self._get_float("TPS_CRITICAL_THRESHOLD", 10.0)

        # ================= РЕЖИМ РАЗРАБОТКИ =========
        self.DEBUG = self._get_bool("DEBUG", False)
        self.DEV_SKIP_RCON_CHECK = self._get_bool("DEV_SKIP_RCON_CHECK", False)
        self.LOG_ALL_MESSAGES = self._get_bool("LOG_ALL_MESSAGES", False)

        # ================= ПРОЧЕЕ ===================
        self.BOT_LANGUAGE = self._get("BOT_LANGUAGE", "ru")
        self.TIMEZONE = self._get("TIMEZONE", "Europe/Moscow")
        self.COMMAND_HISTORY_LIMIT = self._get_int("COMMAND_HISTORY_LIMIT", 50)

        # Создаем необходимые папки
        self._create_directories()

        # Проверяем обязательные поля
        self._validate()

    def _get(self, key: str, default: any = None) -> any:
        """Получение значения из окружения"""
        value = os.getenv(key)
        if value is None:
            return default
        return value

    def _get_required(self, key: str) -> str:
        """Получение обязательного значения"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"❌ Обязательная переменная {key} не установлена в .env файле")
        return value

    def _get_int(self, key: str, default: int) -> int:
        """Получение целого числа"""
        value = self._get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            print(f"⚠️  Предупреждение: {key}={value} не число, используется {default}")
            return default

    def _get_float(self, key: str, default: float) -> float:
        """Получение числа с плавающей точкой"""
        value = self._get(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            print(f"⚠️  Предупреждение: {key}={value} не число, используется {default}")
            return default

    def _get_bool(self, key: str, default: bool) -> bool:
        """Получение булевого значения"""
        value = self._get(key)
        if value is None:
            return default
        value_lower = value.lower()
        if value_lower in ('true', '1', 'yes', 'y', 'on'):
            return True
        elif value_lower in ('false', '0', 'no', 'n', 'off'):
            return False
        else:
            print(f"⚠️  Предупреждение: {key}={value} не булево значение, используется {default}")
            return default

    def _parse_int_list(self, key: str, default: List[int]) -> List[int]:
        """Парсинг списка целых чисел"""
        value = self._get(key)
        if not value:
            return default

        try:
            return [int(x.strip()) for x in value.split(',')]
        except ValueError:
            print(f"⚠️  Предупреждение: {key}={value} не список чисел, используется {default}")
            return default

    def _parse_str_list(self, key: str, default: List[str]) -> List[str]:
        """Парсинг списка строк"""
        value = self._get(key)
        if not value:
            return default

        return [x.strip() for x in value.split(',')]

    def _create_directories(self):
        """Создание необходимых директорий"""
        directories = [
            Path("./data"),
            self.LOG_DIR,
            Path("./temp")
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _validate(self):
        """Валидация настроек"""
        # Проверка токена бота
        if not self.BOT_TOKEN or self.BOT_TOKEN == "your_telegram_bot_token_here":
            raise ValueError(
                "❌ BOT_TOKEN не установлен или имеет значение по умолчанию.\n"
                "Получите токен у @BotFather и добавьте в .env файл"
            )

        # Проверка ключа шифрования в продакшене
        if not self.DEBUG and not self.ENCRYPTION_KEY:
            print("⚠️  ВНИМАНИЕ: ENCRYPTION_KEY не установлен. Сгенерируйте ключ командой:")
            print("   python -c \"import secrets; print(secrets.token_hex(32))\"")

        # Проверка админов
        if not self.ADMIN_IDS:
            print("⚠️  ВНИМАНИЕ: ADMIN_IDS пуст. Бот будет доступен всем пользователям.")

        # Проверка уровня логирования
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.LOG_LEVEL_CONSOLE not in valid_log_levels:
            print(f"⚠️  ВНИМАНИЕ: Неверный LOG_LEVEL_CONSOLE={self.LOG_LEVEL_CONSOLE}")
            self.LOG_LEVEL_CONSOLE = "INFO"

        if self.LOG_LEVEL_FILE not in valid_log_levels:
            print(f"⚠️  ВНИМАНИЕ: Неверный LOG_LEVEL_FILE={self.LOG_LEVEL_FILE}")
            self.LOG_LEVEL_FILE = "DEBUG"

    # Методы для удобного доступа

    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        if not self.ADMIN_IDS:  # Если список пустой - все админы (для разработки)
            return self.DEBUG  # В продакшене лучше запретить
        return user_id in self.ADMIN_IDS

    def get_log_level(self, handler_type: str = "console") -> int:
        """Получение уровня логирования как константы loggers"""
        level_name = self.LOG_LEVEL_CONSOLE if handler_type == "console" else self.LOG_LEVEL_FILE
        return getattr(loggers, level_name.upper())

    def get_database_config(self) -> dict:
        """Конфигурация базы данных"""
        return {
            "url": self.DATABASE_URL,
            "echo": self.DB_ECHO_SQL,
            "cleanup_interval_hours": self.DB_CLEANUP_INTERVAL_HOURS,
        }

    def get_rcon_config(self) -> dict:
        """Конфигурация RCON"""
        return {
            "timeout": self.RCON_TIMEOUT,
            "max_retries": self.RCON_MAX_RETRIES,
            "retry_delay": self.RCON_RETRY_DELAY,
        }

    def get_logging_config(self) -> dict:
        """Конфигурация логирования"""
        return {
            "log_dir": self.LOG_DIR,
            "console_level": self.LOG_LEVEL_CONSOLE,
            "file_level": self.LOG_LEVEL_FILE,
            "max_size_mb": self.LOG_MAX_SIZE_MB,
            "backup_count": self.LOG_BACKUP_COUNT,
            "enable_json": self.ENABLE_JSON_LOGS,
        }

    def print_config(self):
        """Вывод текущей конфигурации"""
        print("=" * 60)
        print("ТЕКУЩАЯ КОНФИГУРАЦИЯ")
        print("=" * 60)

        print(f"🤖 Бот: {self.BOT_NAME}")
        print(f"   Токен: {'✅ Установлен' if self.BOT_TOKEN else '❌ Отсутствует'}")
        print(f"   Админы: {self.ADMIN_IDS or 'Все пользователи (режим разработки)'}")

        print(f"🗄️  База данных: {self.DATABASE_URL}")
        print(f"   SQL логи: {'ВКЛ' if self.DB_ECHO_SQL else 'ВЫКЛ'}")

        print(f"📝 Логирование:")
        print(f"   Папка: {self.LOG_DIR}")
        print(f"   Консоль: {self.LOG_LEVEL_CONSOLE}")
        print(f"   Файл: {self.LOG_LEVEL_FILE}")

        print(f"🔐 Безопасность:")
        print(f"   Ключ шифрования: {'✅ Установлен' if self.ENCRYPTION_KEY else '❌ Отсутствует'}")
        print(f"   Разрешенные хосты: {self.ALLOWED_HOSTS}")

        print(f"⚡ RCON:")
        print(f"   Таймаут: {self.RCON_TIMEOUT}с")
        print(f"   Попытки: {self.RCON_MAX_RETRIES}")

        print(f"🔄 Сессии: {self.SESSION_DURATION_HOURS}ч")
        print(f"🔧 Режим отладки: {'ВКЛ' if self.DEBUG else 'ВЫКЛ'}")
        print("=" * 60)


# Создаем глобальный экземпляр настроек
settings = Settings()