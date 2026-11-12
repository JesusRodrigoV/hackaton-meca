import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings
from app.core.enums import TokenType

_BCRYPT_MAX_PASSWORD_BYTES = 72


def _bcrypt_password_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_PASSWORD_BYTES]


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        _bcrypt_password_bytes(password),
        bcrypt.gensalt(),
    ).decode("utf-8")


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


def _create_token(
    *,
    subject: str | int,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
    jti: str | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
        "type": token_type.value,
    }
    if jti:
        payload["jti"] = jti
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    subject: str | int,
    expires_minutes: int | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    return _create_token(
        subject=subject,
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(
            minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        extra_claims=extra_claims,
    )


def create_refresh_token(
    subject: str | int,
    expires_days: int | None = None,
    device_info: str | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=expires_days or settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())
    token = _create_token(
        subject=subject,
        token_type=TokenType.REFRESH,
        expires_delta=expires_at - now,
        jti=jti,
        extra_claims={"device_info": device_info} if device_info else None,
    )
    return {
        "token": token,
        "jti": jti,
        "expires_at": expires_at,
        "device_info": device_info,
    }


def create_2fa_session_token(subject: str | int) -> str:
    return _create_token(
        subject=subject,
        token_type=TokenType.PRE_2FA,
        expires_delta=timedelta(minutes=settings.TWO_FACTOR_SESSION_EXPIRE_MINUTES),
    )


def create_change_password_token(subject: str | int) -> str:
    return _create_token(
        subject=subject,
        token_type=TokenType.CHANGE_PASSWORD,
        expires_delta=timedelta(
            minutes=settings.CHANGE_PASSWORD_TOKEN_EXPIRE_MINUTES
        ),
    )


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    if expected_type is not None and payload.get("type") != expected_type.value:
        raise JWTError("Tipo de token inválido")
    return payload


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_secure_token() -> str:
    return secrets.token_urlsafe(32)