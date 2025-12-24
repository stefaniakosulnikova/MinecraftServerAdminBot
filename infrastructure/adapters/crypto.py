import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class CryptoService:
    def __init__(self, secret_key: str = None):
        if secret_key:
            # Если есть ключ из .env, используем его
            self.cipher_suite = Fernet(self._generate_key_from_secret(secret_key))
        else:
            # Или генерируем новый (для разработки)
            key = Fernet.generate_key()
            self.cipher_suite = Fernet(key)
            print(f"Сгенерирован ключ шифрования: {key.decode()}")

    def _generate_key_from_secret(self, secret: str) -> bytes:
        """Генерирует ключ из секретной фразы"""
        salt = b'minecraft_admin_bot_salt'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
        return key

    def encrypt(self, data: str) -> bytes:
        """Шифрует данные"""
        return self.cipher_suite.encrypt(data.encode())

    def decrypt(self, encrypted_data: bytes) -> str:
        """Расшифровывает данные"""
        return self.cipher_suite.decrypt(encrypted_data).decode()
