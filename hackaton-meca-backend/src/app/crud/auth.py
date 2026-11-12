from fastapi import Response
from sqlalchemy.orm import Session
from typing import Optional
from app.models.user import User
from app.core.security import verify_password
from app.crud.user import get_user_by_identifier
from app.core.config import settings

def authenticate_user(db: Session, identifier: str, password: str) -> Optional[User]:
    user = get_user_by_identifier(db, identifier)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if getattr(user, "is_active", True) is False:
        return None
    return user


def set_refresh_cookie(response: Response, token: str):
    expires_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/zooconnect/",
        max_age=expires_seconds
    )

def clear_refresh_cookie(response: Response):
    """
    Helper para limpiar cookies
    """
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="none",
        path="/zooconnect/"
    )
