# test_rcon.py
import asyncio
import sys


async def test_rcon_connection(host: str, port: int, password: str):
    """Тестирует RCON подключение независимо от бота"""
    print(f"\n🧪 Тест RCON подключения к {host}:{port}")
    print("=" * 50)

    try:
        # Попробуем разные библиотеки
        print("1. Тест через mcrcon...")
        try:
            import mcrcon
            rcon = mcrcon.MCRcon(host, password, port)
            rcon.connect()
            response = rcon.command("list")
            print(f"   ✅ Успешно! Ответ: {response[:50]}...")
            rcon.disconnect()
            return True
        except ImportError:
            print("   ⚠️  mcrcon не установлен")
        except Exception as e:
            print(f"   ❌ Ошибка mcrcon: {e}")

        print("2. Тест через rcon...")
        try:
            from rcon.source import rcon
            response = await rcon(
                command="list",
                host=host,
                port=port,
                passwd=password,
                timeout=10.0
            )
            print(f"   ✅ Успешно! Ответ: {response[:50]}...")
            return True
        except ImportError:
            print("   ⚠️  rcon не установлен")
        except Exception as e:
            print(f"   ❌ Ошибка rcon: {e}")

        print("3. Тест через сырое TCP соединение...")
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=5.0
            )
            print(f"   ✅ TCP порт {port} открыт")

            # Отправляем тестовые байты RCON
            test_data = b'\x00\x00\x00\x00\x00\x00\x00\x00'
            writer.write(test_data)
            await writer.drain()

            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print(f"   ❌ TCP ошибка: {e}")

        return False

    except Exception as e:
        print(f"💥 Общая ошибка: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Использование: python test_rcon.py <host> <port> <password>")
        print("Пример: python test_rcon.py localhost 25575 mypassword")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    password = sys.argv[3]

    result = asyncio.run(test_rcon_connection(host, port, password))

    if result:
        print("\n✅ RCON подключение работает!")
    else:
        print("\n❌ Не удалось подключиться к RCON")
        print("\n📋 Что проверить:")
        print("1. Сервер Minecraft запущен?")
        print("2. В server.properties:")
        print("   enable-rcon=true")
        print(f"   rcon.port={port}")
        print(f"   rcon.password={password}")
        print("3. Брандмауэр разрешает подключение?")