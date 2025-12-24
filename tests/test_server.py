import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_server_connection():
    """Тестируем подключение к реальному серверу"""
    print("=" * 50)
    print("Тест подключения к Minecraft серверу")
    print("=" * 50)
    
    # Данные из .env или напрямую
    host = "65.21.24.204"
    port = 25575
    password = "123456789"
    
    print(f"\nПодключаемся к:")
    print(f"  Сервер: {host}:{port}")
    print(f"  Пароль: {'*' * len(password)}")
    
    try:
        from infrastructure.adapters.rcon_service import RconService
        rcon = RconService(host, port, password)
        
        print("\n Проверяем подключение...")
        connected = await rcon.test_connection()
        
        if connected:
            print(" УСПЕХ! Сервер доступен и пароль верный!")
            print("\nТеперь можно:")
            print("1. Запустить бота: python -m bot.bot")
            print("2. Открыть Telegram")
            print("3. Написать боту /start")
            print("4. Пройти авторизацию с этими данными")
        else:
            print(" Не удалось подключиться")
            print("\nВозможные причины:")
            print("1. Сервер выключен")
            print("2. RCON не включен на сервере")
            print("3. Неправильный пароль")
            print("4. Блокировка firewall")
            
    except Exception as e:
        print(f"\n Ошибка: {e}")
        print("\nПроверь:")
        print("1. Установлена ли библиотека rcon: pip install rcon")
        print("2. Есть ли интернет-подключение")

if __name__ == "__main__":
    asyncio.run(test_server_connection())
