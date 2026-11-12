import logging

from cryptography.fernet import Fernet

from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    cipher_suite = Fernet(settings.TOTP_ENCRYPTION_KEY.encode())
except Exception:
    logger.exception("TOTP_ENCRYPTION_KEY no es una clave Fernet válida")
    cipher_suite = None


def encrypt_data(data: str) -> str:
    if cipher_suite is None:
        raise ValueError("El cifrado 2FA no está configurado")
    return cipher_suite.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    if cipher_suite is None:
        raise ValueError("El cifrado 2FA no está configurado")
    return cipher_suite.decrypt(encrypted_data.encode()).decode()