import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def simple_rcon_test():
    """Простой тест RCON без загрузки Config"""
    print("=" * 50)
    print("ПРОСТОЙ ТЕСТ RCON")
    print("=" * 50)
    
    host = "65.21.24.204"
    port = 25575
    password = "123456789"
    
    print(f"\nКонфигурация:")
    print(f"  Хост: {host}")
    print(f"  Порт: {port}")
    print(f"  Пароль: {'*' * len(password)}")
    
    # Тест 1: Прямой вызов асинхронного rcon
    print("\n1. Асинхронное подключение...")
    try:
        from rcon.source import rcon
        
        print("   Отправляем команду 'list'...")
        response = await rcon(
            command="list",
            host=host,
            port=port,
            passwd=password
        )
        
        if response:
            print(f"    УСПЕХ! Ответ сервера:")
            print(f"   '{response.strip()}'")
            
            # Проверяем формат ответа
            if "players" in response.lower() or "online" in response.lower():
                print("    Обнаружен ответ о игроках - всё работает!")
            else:
                print("   ℹ  Получен ответ, но не похож на 'list'")
        else:
            print("    Пустой ответ от сервера")
            
    except Exception as e:
        print(f"    Ошибка: {type(e).__name__}: {e}")
    
    # Тест 2: Через наш сервис (без Config)
    print("\n2. Тест через наш RconService...")
    try:
        # Временный класс без зависимости от Config
        from rcon.source import rcon as rcon_async
        
        class SimpleRconService:
            def __init__(self, host: str, port: int, password: str):
                self.host = host
                self.port = port
                self.password = password
            
            async def test_connection(self) -> bool:
                try:
                    response = await rcon_async(
                        command="list",
                        host=self.host,
                        port=self.port,
                        passwd=self.password
                    )
                    return response is not None
                except Exception:
                    return False
        
        rcon_client = SimpleRconService(host, port, password)
        connected = await rcon_client.test_connection()
        
        if connected:
            print("    RconService работает корректно!")
            print("    ВСЁ ГОТОВО К ИСПОЛЬЗОВАНИЮ В БОТЕ!")
        else:
            print("    Не удалось подключиться")
            
    except Exception as e:
        print(f"    Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(simple_rcon_test())
