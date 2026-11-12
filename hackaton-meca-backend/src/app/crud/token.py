from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_secure_token, hash_token
from app.models.auth import PasswordResetToken, RefreshToken


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def create_refresh_token_record(
    db: Session,
    *,
    user_id: int,
    jti: str,
    expires_at: datetime,
    device_info: Optional[str] = None,
) -> RefreshToken:
    token = RefreshToken(
        user_id=user_id,
        jti=jti,
        expires_at=expires_at,
        device_info=device_info,
        revoked=False,
    )
    db.add(token)
    db.flush()
    return token


def get_refresh_token_by_jti(db: Session, jti: str) -> Optional[RefreshToken]:
    return db.query(RefreshToken).filter(RefreshToken.jti == jti).first()


def revoke_refresh_token(db: Session, token: RefreshToken) -> RefreshToken:
    if not token.revoked:
        token.revoked = True
        db.add(token)
        db.flush()
    return token


def revoke_all_user_tokens(db: Session, user_id: int) -> None:
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked.is_(False),
    ).update({"revoked": True}, synchronize_session=False)
    db.flush()


def is_refresh_token_valid(db: Session, jti: str) -> bool:
    token = (
        db.query(RefreshToken)
        .filter(RefreshToken.jti == jti, RefreshToken.revoked.is_(False))
        .first()
    )
    if not token:
        return False
    return _as_utc(token.expires_at) > datetime.now(timezone.utc)


def create_password_reset_token(db: Session, user_id: int) -> str:
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user_id
    ).delete(synchronize_session=False)

    raw_token = generate_secure_token()
    db.add(
        PasswordResetToken(
            user_id=user_id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
        )
    )
    db.flush()
    return raw_token


def get_password_reset_token(
    db: Session,
    raw_token: str,
) -> Optional[PasswordResetToken]:
    return (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == hash_token(raw_token))
        .first()
    )


def is_password_reset_token_expired(token: PasswordResetToken) -> bool:
    return _as_utc(token.expires_at) <= datetime.now(timezone.utc)


def delete_password_reset_token(db: Session, token: PasswordResetToken) -> None:
    db.delete(token)
    db.flush()