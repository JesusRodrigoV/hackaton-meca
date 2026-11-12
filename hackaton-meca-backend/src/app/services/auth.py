from typing import Optional

from fastapi import HTTPException, Response, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import TokenType
from app.core.password_policy import validate_password_strength_func
from app.core.security import (
    create_2fa_session_token,
    create_access_token,
    create_change_password_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.crud import auth as crud_auth
from app.crud import token as crud_token
from app.crud import two_factor as crud_2fa
from app.crud import user as crud_user
from app.models.security import User


def authenticate(db: Session, email: str, password: str) -> Optional[User]:
    return crud_auth.authenticate_credentials(db, email, password)


def _validate_new_password(password: str) -> None:
    try:
        validate_password_strength_func(password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


def issue_tokens(
    db: Session,
    user: User,
    *,
    device_info: Optional[str] = None,
) -> tuple[str, str]:
    access_token = create_access_token(user.id)
    refresh = create_refresh_token(user.id, device_info=device_info)
    crud_token.create_refresh_token_record(
        db,
        user_id=user.id,
        jti=refresh["jti"],
        expires_at=refresh["expires_at"],
        device_info=device_info,
    )
    return access_token, refresh["token"]


def _subject_to_user_id(payload: dict) -> int:
    try:
        return int(payload.get("sub"))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        ) from exc


def refresh_session(db: Session, raw_refresh_token: str) -> tuple[str, str]:
    try:
        payload = decode_token(raw_refresh_token, TokenType.REFRESH)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
        ) from exc

    jti = payload.get("jti")
    if not jti or not crud_token.is_refresh_token_valid(db, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o revocado",
        )

    user = crud_user.get_user(db, _subject_to_user_id(payload))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo o inexistente",
        )
    if user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debes cambiar la contraseña antes de continuar",
        )

    token_record = crud_token.get_refresh_token_by_jti(db, jti)
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido",
        )
    crud_token.revoke_refresh_token(db, token_record)
    return issue_tokens(
        db,
        user,
        device_info=token_record.device_info,
    )


def revoke_session(db: Session, raw_refresh_token: str) -> None:
    try:
        payload = decode_token(raw_refresh_token, TokenType.REFRESH)
    except JWTError:
        return
    jti = payload.get("jti")
    if not jti:
        return
    token_record = crud_token.get_refresh_token_by_jti(db, jti)
    if token_record:
        crud_token.revoke_refresh_token(db, token_record)


def change_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> User:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual no es correcta",
        )
    _validate_new_password(new_password)
    crud_user.set_password(
        db,
        user,
        new_password,
        must_change_password=False,
    )
    crud_token.revoke_all_user_tokens(db, user.id)
    return user


def create_change_token(user: User) -> str:
    return create_change_password_token(user.id)


def create_two_factor_session_token(user: User) -> str:
    return create_2fa_session_token(user.id)


def verify_two_factor_session(db: Session, session_token: str) -> User:
    try:
        payload = decode_token(session_token, TokenType.PRE_2FA)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de sesión 2FA inválido o expirado",
        ) from exc

    user = crud_user.get_user(db, _subject_to_user_id(payload))
    if not user or not user.is_active or not user.is_totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no válido para 2FA",
        )
    return user


def validate_two_factor_code(
    db: Session,
    user: User,
    code: str,
    *,
    allow_backup: bool = True,
) -> bool:
    normalized = code.strip()
    if not normalized:
        return False

    if len(normalized) == 6 and user.totp_secret:
        try:
            if crud_2fa.verify_totp_code(
                crud_2fa.get_user_totp_secret(user),
                normalized,
            ):
                return True
        except Exception:
            # If the stored secret cannot be decrypted, fall through to backup codes.
            pass

    if not allow_backup:
        return False
    return crud_2fa.validate_backup_code(db, user, normalized)


def request_password_reset(
    db: Session,
    email: str,
) -> Optional[tuple[str, User]]:
    user = crud_user.get_user_by_email(db, email)
    if not user or not user.is_active:
        return None
    raw_token = crud_token.create_password_reset_token(db, user.id)
    return raw_token, user


def reset_password(
    db: Session,
    raw_token: str,
    new_password: str,
) -> User:
    token_record = crud_token.get_password_reset_token(db, raw_token)
    if not token_record or crud_token.is_password_reset_token_expired(token_record):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de recuperación inválido o expirado",
        )

    user = crud_user.get_user(db, token_record.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de recuperación inválido o expirado",
        )

    _validate_new_password(new_password)
    crud_user.set_password(
        db,
        user,
        new_password,
        must_change_password=False,
    )
    crud_token.revoke_all_user_tokens(db, user.id)
    crud_token.delete_password_reset_token(db, token_record)
    return user


def setup_totp(db: Session, user: User) -> tuple[str, str]:
    if user.is_totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA ya está habilitado para este usuario",
        )
    secret = crud_2fa.generate_totp_secret()
    crud_2fa.save_totp_secret_for_user(db, user, secret)
    uri = crud_2fa.get_otpauth_uri(secret, user.email)
    return secret, uri


def enable_totp(db: Session, user: User, code: str) -> list[str]:
    if user.is_totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA ya está habilitado para este usuario",
        )
    if not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Primero debes iniciar la configuración de 2FA",
        )

    secret = crud_2fa.get_user_totp_secret(user)
    if not crud_2fa.verify_totp_code(secret, code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código 2FA inválido",
        )

    crud_2fa.activate_totp_for_user(db, user)
    return crud_2fa.generate_and_store_backup_codes(db, user)


def disable_totp(
    db: Session,
    user: User,
    password: str,
    code: str,
) -> None:
    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña no es correcta",
        )
    if not user.is_totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA no está habilitado para este usuario",
        )
    if not validate_two_factor_code(db, user, code, allow_backup=False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código 2FA inválido",
        )
    crud_2fa.disable_totp_for_user(db, user)


def set_refresh_cookie(response: Response, raw_refresh_token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=raw_refresh_token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
    )