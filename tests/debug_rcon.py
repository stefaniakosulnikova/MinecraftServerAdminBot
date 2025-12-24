import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def debug_rcon_connection():
    """Отладочный тест RCON соединения"""
    print("=" * 50)
    print("ОТЛАДКА RCON ПОДКЛЮЧЕНИЯ")
    print("=" * 50)
    
    host = "65.21.24.204"
    port = 25575
    password = "123456789"
    
    print(f"\nКонфигурация:")
    print(f"  Хост: {host}")
    print(f"  Порт: {port}")
    print(f"  Пароль: {password}")
    
    # Тест 1: Проверяем библиотеку rcon
    print("\n1. Проверка библиотеки rcon...")
    try:
        import rcon
        print(f"    Библиотека rcon установлена: версия {rcon.__version__ if hasattr(rcon, '__version__') else 'unknown'}")
    except ImportError:
        print("    Библиотека rcon не установлена!")
        print("   Установите: pip install rcon")
        return
    
    # Тест 2: Пробуем прямое подключение
    print("\n2. Прямое подключение через rcon...")
    try:
        # Прямой вызов rcon без asyncio
        import rcon as rcon_lib
        
        print(f"   Пытаемся подключиться...")
        response = rcon_lib.rcon(host, port, password, "list")
        
        if response:
            print(f"    УСПЕХ! Ответ сервера:")
            print(f"   '{response}'")
        else:
            print("    Пустой ответ от сервера")
            print("   Возможные причины:")
            print("   - Неправильный пароль")
            print("   - Сервер не отвечает на команду list")
            
    except Exception as e:
        print(f"    Ошибка при прямом подключении: {type(e).__name__}: {e}")
        
        # Проверяем конкретные ошибки
        if "Connection refused" in str(e):
            print("    Ошибка: Connection refused - возможно порт занят другим процессом")
        elif "timed out" in str(e).lower():
            print("    Таймаут соединения")
        elif "auth" in str(e).lower():
            print("    Ошибка аутентификации - неправильный пароль")
        elif "password" in str(e).lower():
            print("    Ошибка пароля")
    
    # Тест 3: Пробуем другие команды
    print("\n3. Пробуем другие команды...")
    test_commands = ["list", "help", "version", "say Hello"]
    
    for cmd in test_commands:
        try:
            import rcon as rcon_lib
            response = rcon_lib.rcon(host, port, password, cmd)
            print(f"   Команда '{cmd}': ", end="")
            if response:
                print(f" Ответ: {response[:50]}..." if len(response) > 50 else f" Ответ: {response}")
            else:
                print(" Пустой ответ")
        except Exception as e:
            print(f"   Команда '{cmd}':  {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(debug_rcon_connection())
