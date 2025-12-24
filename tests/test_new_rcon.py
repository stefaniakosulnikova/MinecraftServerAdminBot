import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_new_rcon_api():
    """Тестируем новое API RCON"""
    print("=" * 50)
    print("ТЕСТ НОВОГО API RCON")
    print("=" * 50)
    
    host = "65.21.24.204"
    port = 25575
    password = "123456789"
    
    print(f"\nКонфигурация:")
    print(f"  Хост: {host}")
    print(f"  Порт: {port}")
    print(f"  Пароль: {password}")
    
    # Тест нового API напрямую
    print("\n1. Тестируем прямое подключение...")
    try:
        from rcon.source import rcon
        
        print("   Отправляем команду 'list'...")
        response = rcon(
            command="list",
            host=host,
            port=port,
            passwd=password
        )
        
        if response:
            print(f"    УСПЕХ! Ответ сервера:")
            print(f"   '{response}'")
            print("\n RCON работает корректно!")
            print("Теперь можно использовать в боте.")
        else:
            print("    Пустой ответ от сервера")
            
    except Exception as e:
        print(f"    Ошибка: {type(e).__name__}: {e}")
        
        # Анализируем ошибку
        error_str = str(e).lower()
        
        if "connection refused" in error_str:
            print("\n Ошибка: Connection refused")
            print("   Возможно сервер не запущен или порт занят")
        elif "timed out" in error_str:
            print("\n Ошибка: Таймаут")
            print("   Сервер не отвечает. Проверь:")
            print("   - Запущен ли сервер")
            print("   - Правильный ли IP и порт")
        elif "authentication" in error_str or "password" in error_str:
            print("\n Ошибка аутентификации")
            print("   Неправильный пароль RCON")
            print("   Проверь пароль в server.properties")
        elif "cannot assign requested address" in error_str:
            print("\n Ошибка адреса")
            print("   Проблема с сетевым подключением")
        else:
            print(f"\n Неизвестная ошибка: {e}")
    
    # Тест через наш сервис
    print("\n2. Тестируем через RconService...")
    try:
        from infrastructure.adapters.rcon_service import RconService
        
        rcon_client = RconService(host, port, password)
        connected = await rcon_client.test_connection()
        
        if connected:
            print("    RconService работает корректно!")
        else:
            print("    RconService не смог подключиться")
            
    except Exception as e:
        print(f"    Ошибка RconService: {e}")

if __name__ == "__main__":
    asyncio.run(test_new_rcon_api())
