import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_multiple_commands():
    """Тестируем разные команды RCON"""
    print("=" * 50)
    print("ТЕСТ РАЗНЫХ КОМАНД RCON")
    print("=" * 50)
    
    host = "65.21.24.204"
    port = 25575
    password = "123456789"
    
    print(f"\nКонфигурация:")
    print(f"  Хост: {host}")
    print(f"  Порт: {port}")
    print(f"  Пароль: {'*' * len(password)}")
    
    # Тестируем разные команды
    test_commands = [
        "list",           # Список игроков
        "help",           # Помощь
        "version",        # Версия
        "time query day", # Время
        "say Test",       # Сообщение в чат
        "seed",           # Сид мира
        "save-all",       # Сохранение
        "tps",            # Производительность
    ]
    
    try:
        from rcon.source import rcon
        
        for cmd in test_commands:
            print(f"\n Команда: '{cmd}'")
            try:
                response = await rcon(
                    command=cmd,
                    host=host,
                    port=port,
                    passwd=password
                )
                
                if response:
                    print(f"    Ответ: {response.strip()[:100]}{'...' if len(response) > 100 else ''}")
                else:
                    print(f"     Пустой ответ (EmptyResponse)")
                    
            except Exception as e:
                print(f"    Ошибка: {type(e).__name__}: {str(e)[:100]}")
    
    except ImportError:
        print(" Библиотека rcon не установлена!")
        print("Установите: pip install rcon")

if __name__ == "__main__":
    asyncio.run(test_multiple_commands())
