"""
Minecraft Server Admin Bot
Главный файл для запуска бота
"""

import asyncio
import loggers
import sys
from pathlib import Path

# Добавляем корневую директорию в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

# Импорты фреймворка
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Импорты конфигурации
from config.settings import settings

# Импорты базы данных
from infrastructure.adapters.database import Database

# Импорты логгера
from loggers.app_logger import logger

# ============= ИМПОРТ КОНТРОЛЛЕРОВ ПО ОТДЕЛЬНОСТИ =============
from bot.controllers.start_controller import router as start_router
from bot.controllers.auth_controller import router as auth_router
from bot.controllers.status_controller import router as status_router
from bot.controllers.help_controller import router as help_router
from bot.controllers.commands_controller import router as commands_router
from bot.controllers.sessions_controller import router as sessions_router
from bot.controllers.monitoring_controller import router as monitoring_router

# ============= ИМПОРТ MIDDLEWARE =============
from bot.middlewares.auth_middleware import AuthMiddleware
from bot.middlewares.logging_middleware import LoggingMiddleware
from bot.middlewares.database_middleware import DatabaseMiddleware

# Версия бота
__version__ = "1.0.0"


async def setup_database() -> Database:
    """Настройка и инициализация базы данных"""
    logger.info("🗄️  Инициализация базы данных...")

    try:
        database = Database(
            database_url=settings.DATABASE_URL,
            echo=settings.DB_ECHO_SQL
        )

        await database.initialize()
        logger.info("✅ База данных инициализирована")
        return database

    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}", exc_info=True)
        raise


async def setup_middlewares(dp: Dispatcher, database: Database):
    """Настройка middleware"""
    logger.info("🛠️  Настройка middleware...")

    # Middleware для логирования
    logging_middleware = LoggingMiddleware()
    dp.update.outer_middleware(logging_middleware)

    # Middleware для доступа к БД
    database_middleware = DatabaseMiddleware(database)
    dp.update.outer_middleware(database_middleware)

    # Middleware для проверки авторизации
    auth_middleware = AuthMiddleware()
    dp.message.middleware(auth_middleware)
    dp.callback_query.middleware(auth_middleware)

    logging_middleware = LoggingMiddleware()
    dp.update.outer_middleware(logging_middleware)

    database_middleware = DatabaseMiddleware(database)
    dp.update.outer_middleware(database_middleware)

    logger.info("✅ Middleware настроены")


async def setup_routers(dp: Dispatcher):
    """Настройка роутеров (обработчиков)"""
    logger.info("🔄 Настройка роутеров...")

    # Регистрируем все роутеры
    routers = [
        start_router,
        auth_router,
        status_router,
        help_router,
        commands_router,
        sessions_router,
        monitoring_router
    ]

    for router in routers:
        dp.include_router(router)

    logger.info(f"✅ Зарегистрировано {len(routers)} роутеров")


async def startup_tasks(database: Database):
    """Задачи выполняемые при запуске бота"""
    logger.info("🚀 Выполнение задач запуска...")

    # Очистка старых данных
    try:
        await database.cleanup()
        logger.info("🧹 Очистка старых данных выполнена")
    except Exception as e:
        logger.warning(f"⚠️  Ошибка при очистке данных: {e}")

    logger.info("✅ Задачи запуска выполнены")


async def periodic_tasks(database: Database):
    """Периодические фоновые задачи"""
    logger.info("⏰ Запуск фоновых задач...")

    try:
        while True:
            # Ожидание между запусками (1 час по умолчанию)
            await asyncio.sleep(3600)

            # Очистка просроченных сессий
            try:
                await database.cleanup()
                logger.debug("🧹 Периодическая очистка выполнена")
            except Exception as e:
                logger.warning(f"⚠️  Ошибка при периодической очистке: {e}")

    except asyncio.CancelledError:
        logger.info("⏹ Фоновые задачи остановлены")
    except Exception as e:
        logger.error(f"❌ Ошибка в фоновых задачах: {e}")


async def main():
    """Основная функция запуска бота"""

    # Вывод информации о запуске
    print("=" * 60)
    print(f"🏰 MINECRAFT SERVER ADMIN BOT v{__version__}")
    print("=" * 60)

    # Вывод конфигурации (если есть метод print_config)
    if hasattr(settings, 'print_config'):
        settings.print_config()

    # Проверка токена бота
    if not settings.BOT_TOKEN:
        logger.critical("❌ BOT_TOKEN не установлен. Проверьте .env файл.")
        return

    # Инициализация базы данных
    database = None
    try:
        database = await setup_database()
    except Exception as e:
        logger.critical(f"❌ Не удалось инициализировать БД: {e}")
        return

    # Инициализация бота
    try:
        logger.info("🤖 Инициализация Telegram бота...")

        bot = Bot(token=settings.BOT_TOKEN)

        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот инициализирован: @{bot_info.username} ({bot_info.full_name})")

    except Exception as e:
        logger.critical(f"❌ Ошибка инициализации бота: {e}")
        await database.close() if database else None
        return

    # Создаем диспетчер
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Настройка middleware
    await setup_middlewares(dp, database)

    # Настройка роутеров
    await setup_routers(dp)

    # Задачи при запуске
    await startup_tasks(database)

    # Запуск фоновых задач
    background_task = asyncio.create_task(periodic_tasks(database))

    # Запуск бота
    try:
        logger.info("🚀 Запуск бота...")
        logger.info("✅ Бот запущен и готов к работе!")
        logger.info("👉 Откройте Telegram и начните общение с ботом")
        print("\n" + "=" * 60)
        print("🤖 Бот запущен! Для остановки нажмите Ctrl+C")
        print("=" * 60 + "\n")

        await dp.start_polling(bot, skip_updates=True)

    except KeyboardInterrupt:
        logger.info("⏹ Остановка бота по запросу пользователя...")
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка при работе бота: {e}", exc_info=True)
    finally:
        # Остановка фоновых задач
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass

        # Закрытие соединений
        logger.info("🔌 Закрытие соединений...")

        try:
            await bot.session.close()
        except Exception as e:
            logger.warning(f"⚠️  Ошибка при закрытии сессии бота: {e}")

        try:
            await database.close() if database else None
        except Exception as e:
            logger.warning(f"⚠️  Ошибка при закрытии БД: {e}")

        logger.info("🛑 Бот остановлен")
        print("\n" + "=" * 60)
        print("🛑 Бот остановлен")
        print("=" * 60)


def run():
    """Точка входа для запуска бота"""
    try:
        # Создаем цикл событий
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Запуск main
        loop.run_until_complete(main())

    except KeyboardInterrupt:
        print("\n⚠️  Получен сигнал остановки...")
    except Exception as e:
        logger.critical(f"💥 Непредвиденная ошибка: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Проверяем Python версию
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        sys.exit(1)

    # Запуск бота
    run()