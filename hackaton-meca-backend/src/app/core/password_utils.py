import secrets
import string
from typing import Optional

from app.core.password_policy import is_valid_password


def generate_strong_password(length: int = 12) -> str:
    """Genera una contraseña segura que cumpla la política.
    - Asegura mayúscula, minúscula, dígito y símbolo
    - Evita repetidos y secuencias según `is_valid_password`
    """
    if length < 8:
        length = 12

    pool = string.ascii_letters + string.digits + "!@#$%^&*()-_"

    while True:
        # Garantizar la presencia de cada clase requerida
        pwd_chars = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*()-_")
        ]
        remaining = length - len(pwd_chars)
        for _ in range(remaining):
            pwd_chars.append(secrets.choice(pool))

        # Barajar de forma segura
        for i in range(len(pwd_chars) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            pwd_chars[i], pwd_chars[j] = pwd_chars[j], pwd_chars[i]

        candidate = "".join(pwd_chars)
        if is_valid_password(candidate):
            return candidate
