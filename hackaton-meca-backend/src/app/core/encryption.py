import logging

from cryptography.fernet import Fernet
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    cipher_suite = Fernet(settings.TOTP_ENCRYPTION_KEY.encode())
except Exception:
    logger.error("Error fatal: TOTP_ENCRYPTION_KEY no es valida")
    cipher_suite = None

def encrypt_data(data: str) -> str:
    if not cipher_suite:
        raise ValueError("El cifrado 2FA no esta configurado")
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    if not cipher_suite:
        raise ValueError("El cifrado 2FA no esta configrado")
    return cipher_suite.decrypt(encrypted_data.encode()).decode()