import socket

def check_rcon_port(host, port, timeout=5):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

# Использование
if check_rcon_port("65.21.24.204", 25575):
    print("Порт RCON открыт")
else:
    print("Порт недоступен")