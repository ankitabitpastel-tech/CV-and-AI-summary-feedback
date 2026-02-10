from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


class EncryptionService:

    cipher = Fernet(settings.FERNET_SECRET_KEY)

    @classmethod
    def encrypt_id(cls, raw_id):
        return cls.cipher.encrypt(str(raw_id).encode()).decode()

    @classmethod
    def decrypt_id(cls, masked_id):
        try:
            return int(cls.cipher.decrypt(masked_id.encode()).decode())
        except InvalidToken:
            return None
