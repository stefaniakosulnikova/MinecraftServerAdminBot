import socket
import struct
import time

def raw_rcon_test():
    """Raw RCON тест через сокеты"""
    print("=" * 50)
    print("RAW RCON ТЕСТ (как веб-консоль)")
    print("=" * 50)
    
    host = "65.21.24.204"
    port = 25575
    password = "123456789"
    
    print(f"\nПодключаемся к {host}:{port}...")
    
    try:
        # Создаем сокет
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)  # Увеличиваем таймаут
        
        # Подключаемся
        sock.connect((host, port))
        print(" TCP соединение установлено")
        
        # ===== ШАГ 1: Аутентификация =====
        print("\n Отправляем аутентификацию...")
        
        # Создаем пакет аутентификации
        request_id = 1
        packet_type = 3  # 3 = SERVERDATA_AUTH
        
        # Тело пакета: пароль + два нулевых байта
        body = password.encode('ascii') + b'\x00\x00'
        
        # Длина пакета (без 4 байт самой длины)
        packet_len = len(body) + 8  # 8 байт для request_id и packet_type
        
        # Собираем пакет
        packet = b''
        packet += struct.pack('<i', packet_len)  # Длина
        packet += struct.pack('<i', request_id)   # ID
        packet += struct.pack('<i', packet_type)  # Тип
        packet += body                            # Тело
        
        print(f" Отправляем {len(packet)} байт...")
        sock.send(packet)
        
        # Получаем ответ на аутентификацию
        print(" Ждем ответ на аутентификацию...")
        time.sleep(1)
        
        # Читаем ответ
        response = sock.recv(4096)
        if response:
            print(f" Получено {len(response)} байт ответа")
            
            # Парсим ответ
            if len(response) >= 12:
                resp_len = struct.unpack('<i', response[0:4])[0]
                resp_id = struct.unpack('<i', response[4:8])[0]
                resp_type = struct.unpack('<i', response[8:12])[0]
                
                print(f"   Длина: {resp_len}, ID: {resp_id}, Тип: {resp_type}")
                
                if resp_id == request_id and resp_id != -1:
                    print("    Аутентификация успешна!")
                elif resp_id == -1:
                    print("    Аутентификация failed (ID = -1)")
                else:
                    print(f"     Неожиданный ID ответа: {resp_id}")
        
        # ===== ШАГ 2: Отправляем команду list =====
        print("\n Отправляем команду 'list'...")
        
        request_id = 2
        packet_type = 2  # 2 = SERVERDATA_EXECCOMMAND
        command = "list"
        
        # Тело пакета: команда + два нулевых байта
        body = command.encode('ascii') + b'\x00\x00'
        packet_len = len(body) + 8
        
        # Собираем пакет
        packet = b''
        packet += struct.pack('<i', packet_len)
        packet += struct.pack('<i', request_id)
        packet += struct.pack('<i', packet_type)
        packet += body
        
        print(f" Отправляем команду...")
        sock.send(packet)
        
        # Получаем ответ
        print(" Ждем ответ на команду...")
        time.sleep(2)  # Даем время серверу
        
        response = sock.recv(4096)
        if response:
            print(f" Получено {len(response)} байт")
            
            if len(response) >= 12:
                # Парсим ответ
                offset = 0
                while offset < len(response):
                    if offset + 4 > len(response):
                        break
                        
                    resp_len = struct.unpack('<i', response[offset:offset+4])[0]
                    resp_id = struct.unpack('<i', response[offset+4:offset+8])[0]
                    resp_type = struct.unpack('<i', response[offset+8:offset+12])[0]
                    
                    # Текст ответа (если есть)
                    if resp_len > 10:  # Есть текст помимо заголовка
                        text_start = offset + 12
                        text_end = offset + 4 + resp_len - 2  # -2 для нулевых байт
                        if text_end <= len(response):
                            text = response[text_start:text_end].decode('ascii', errors='ignore')
                            print(f"\n ОТВЕТ СЕРВЕРА:")
                            print(f"'{text}'")
                    
                    offset += 4 + resp_len  # Переходим к следующему пакету
        
        sock.close()
        print("\n Raw RCON тест завершен!")
        
    except Exception as e:
        print(f" Ошибка: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    raw_rcon_test()
