import secrets
from datetime import datetime, timezone
from typing import Optional

import pyotp
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.encryption import decrypt_data, encrypt_data
from app.core.security import get_password_hash, verify_password
from app.models.auth import TwoFactorBackupCode
from app.models.security import User


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_otpauth_uri(
    secret: str,
    email: str,
    issuer_name: Optional[str] = None,
) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=issuer_name or settings.TOTP_ISSUER,
    )


def save_totp_secret_for_user(db: Session, user: User, secret: str) -> None:
    user.totp_secret = encrypt_data(secret)
    user.is_totp_enabled = False
    user.totp_enabled_at = None
    db.add(user)
    db.flush()


def get_user_totp_secret(user: User) -> str:
    if not user.totp_secret:
        raise ValueError("El usuario no tiene un secreto TOTP configurado")
    return decrypt_data(user.totp_secret)


def verify_totp_code(secret: str, code: str) -> bool:
    if not code:
        return False
    return pyotp.TOTP(secret).verify(code.strip(), valid_window=1)


def activate_totp_for_user(db: Session, user: User) -> None:
    user.is_totp_enabled = True
    user.totp_enabled_at = datetime.now(timezone.utc)
    db.add(user)
    db.flush()


def disable_totp_for_user(db: Session, user: User) -> None:
    user.totp_secret = None
    user.is_totp_enabled = False
    user.totp_enabled_at = None
    db.add(user)
    db.query(TwoFactorBackupCode).filter(
        TwoFactorBackupCode.user_id == user.id
    ).delete(synchronize_session=False)
    db.flush()


def generate_and_store_backup_codes(
    db: Session,
    user: User,
    count: Optional[int] = None,
) -> list[str]:
    db.query(TwoFactorBackupCode).filter(
        TwoFactorBackupCode.user_id == user.id
    ).delete(synchronize_session=False)

    plaintext_codes: list[str] = []
    for _ in range(count or settings.BACKUP_CODE_COUNT):
        code = f"{secrets.token_hex(2)}-{secrets.token_hex(2)}"
        plaintext_codes.append(code)
        db.add(
            TwoFactorBackupCode(
                user_id=user.id,
                code_hash=get_password_hash(code),
            )
        )
    db.flush()
    return plaintext_codes


def validate_backup_code(db: Session, user: User, code: str) -> bool:
    normalized = code.strip()
    if not normalized:
        return False

    candidates = (
        db.query(TwoFactorBackupCode)
        .filter(
            TwoFactorBackupCode.user_id == user.id,
            TwoFactorBackupCode.is_used.is_(False),
        )
        .all()
    )
    for candidate in candidates:
        if verify_password(normalized, candidate.code_hash):
            candidate.is_used = True
            candidate.used_at = datetime.now(timezone.utc)
            db.add(candidate)
            db.flush()
            return True
    return False


def count_unused_backup_codes(db: Session, user_id: int) -> int:
    return (
        db.query(TwoFactorBackupCode)
        .filter(
            TwoFactorBackupCode.user_id == user_id,
            TwoFactorBackupCode.is_used.is_(False),
        )
        .count()
    )