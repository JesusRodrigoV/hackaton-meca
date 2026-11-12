from typing import Iterable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import PermissionCode, TokenType
from app.core.security import decode_token
from app.crud import permission as crud_permission
from app.crud import user as crud_user
from app.db.session import get_db
from app.models.security import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
)


def _unauthorized(detail: str = "No autorizado") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _user_id_from_payload(payload: dict) -> int:
    subject = payload.get("sub")
    if subject is None:
        raise _unauthorized()
    try:
        return int(subject)
    except (TypeError, ValueError) as exc:
        raise _unauthorized() from exc


def _load_active_user(db: Session, user_id: int) -> User:
    user = crud_user.get_user(db, user_id)
    if not user or not user.is_active:
        raise _unauthorized("Usuario inactivo o inexistente")
    return user


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise _unauthorized()
    try:
        payload = decode_token(token, TokenType.ACCESS)
    except JWTError as exc:
        raise _unauthorized("Token inválido o expirado") from exc

    user = _load_active_user(db, _user_id_from_payload(payload))
    if user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debes cambiar la contraseña antes de continuar",
        )
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )
    return current_user


def get_current_user_allow_change(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Accept normal access tokens and short-lived change-password tokens."""
    if not token:
        raise _unauthorized()
    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise _unauthorized("Token inválido o expirado") from exc

    token_type = payload.get("type")
    if token_type not in (TokenType.ACCESS.value, TokenType.CHANGE_PASSWORD.value):
        raise _unauthorized("Token inválido para esta operación")

    user = _load_active_user(db, _user_id_from_payload(payload))
    if token_type == TokenType.ACCESS.value and user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debes cambiar la contraseña antes de continuar",
        )
    return user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None
    try:
        payload = decode_token(token, TokenType.ACCESS)
    except JWTError:
        return None
    try:
        user = crud_user.get_user(db, _user_id_from_payload(payload))
    except HTTPException:
        return None
    if not user or not user.is_active:
        return None
    return user


def _permission_values(required: Iterable[PermissionCode | str]) -> list[str]:
    return [
        item.value if isinstance(item, PermissionCode) else str(item)
        for item in required
    ]


def require_permission(*required_permissions: PermissionCode | str):
    required_codes = _permission_values(required_permissions)

    def dependency(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ) -> User:
        if not required_codes:
            return current_user
        if not crud_permission.user_has_permissions(
            db, current_user.id, required_codes
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes para realizar esta acción",
            )
        return current_user

    return dependency


def require_any_permission(*required_permissions: PermissionCode | str):
    required_codes = _permission_values(required_permissions)

    def dependency(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ) -> User:
        if not required_codes:
            return current_user
        effective = set(
            crud_permission.get_effective_permission_codes(db, current_user.id)
        )
        if not any(code in effective for code in required_codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes para realizar esta acción",
            )
        return current_user

    return dependency