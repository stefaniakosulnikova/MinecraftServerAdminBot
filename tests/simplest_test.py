import socket
import time

def simplest_rcon_test():
    """Самый простой тест RCON"""
    print("Самый простой тест RCON подключения...")
    
    host = "65.21.24.204"
    port = 25575
    
    try:
        # 1. Простое TCP подключение
        print(f"1. Подключаемся к {host}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        print("    TCP подключение установлено")
        
        # 2. Пробуем отправить что-то и получить ответ
        print("2. Пробуем получить баннер сервера...")
        
        # Просто читаем что сервер отправляет при подключении
        try:
            data = sock.recv(1024)
            if data:
                print(f"    Сервер отправил: {data[:50]}")
            else:
                print("     Сервер ничего не отправил")
        except socket.timeout:
            print("     Таймаут при чтении")
        
        sock.close()
        print("\n Базовое соединение работает!")
        
        return True
        
    except Exception as e:
        print(f" Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = simplest_rcon_test()
    
    if success:
        print("\n" + "=" * 50)
        print("TCP соединение работает!")
        print("Проблема в RCON протоколе или пароле")
        print("=" * 50)
