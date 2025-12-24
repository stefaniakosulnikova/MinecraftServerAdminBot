import socket
import time

def diagnose_rcon_issue():
    """Диагностика проблемы RCON"""
    print("=" * 50)
    print("ДИАГНОСТИКА ПРОБЛЕМЫ RCON")
    print("=" * 50)
    
    host = "65.21.24.204"
    port = 25575
    
    print(f"\n1. Проверка порта {host}:{port}")
    
    # Проверяем доступность порта
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        
        if result == 0:
            print("    Порт открыт и доступен")
            
            # Пробуем получить баннер сервера
            print("\n2. Пробуем получить данные от сервера...")
            try:
                # Отправляем пустой пакет чтобы увидеть ответ
                data = sock.recv(1024)
                if data:
                    print(f"    Получены данные: {data[:100]}")
                else:
                    print("     Сервер не отправил данных")
            except socket.timeout:
                print("     Таймаут при чтении данных")
            except Exception as e:
                print(f"     Ошибка чтения: {e}")
                
        else:
            print(f"    Порт закрыт (код ошибки: {result})")
            
    except Exception as e:
        print(f"    Ошибка подключения: {e}")
    finally:
        try:
            sock.close()
        except:
            pass
    
    print("\n3. Рекомендации:")
    print("    Проверь на сервере:")
    print("   - Файл server.properties перезагружен?")
    print("   - Сервер перезапущен после изменений?")
    print("   - Логи сервера (обычно logs/latest.log)")
    print("\n    Быстрое решение:")
    print("   - Перезапусти сервер через панель управления")
    print("   - Подожди 2 минуты после запуска")
    print("   - Попробуй подключиться через веб-консоль хостинга")

if __name__ == "__main__":
    diagnose_rcon_issue()
