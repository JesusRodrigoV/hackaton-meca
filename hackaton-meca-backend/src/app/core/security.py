from datetime import datetime, timedelta, timezone
from jose import jwt
import bcrypt
import uuid
from app.core.config import settings

_BCRYPT_MAX_PASSWORD_BYTES = 72


def _bcrypt_password_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_PASSWORD_BYTES]

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(_bcrypt_password_bytes(password), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False

    try:
        return bcrypt.checkpw(
            _bcrypt_password_bytes(plain_password),
            hashed_password.encode("utf-8"),
        )
    except (TypeError, ValueError):
        return False

def create_access_token(subject: str, expires_minutes: int | None = None, extra_claims: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=(expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": expires,
        "type": "access"
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(subject: str, expires_days: int | None = None, device_info: str | None = None) -> dict:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=(expires_days or settings.REFRESH_TOKEN_EXPIRE_DAYS))
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": expires,
        "jti": jti,
        "type": "refresh"
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"token": token, "jti": jti, "expires_at": expires, "device_info": device_info}
#sistema actual stateless, el token se mantiene activo
#implementacion de hibrido: Access Tokens Stateless y Refresh Tokens Stateful.

#token 5 minutitos 2fa
def create_2fa_session_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=5) 
    
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": expires,
        "type": "pre_2fa"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
