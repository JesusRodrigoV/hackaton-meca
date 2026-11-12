from typing import Iterable, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.password_policy import validate_password_strength_func
from app.core.password_utils import generate_strong_password
from app.core.security import get_password_hash
from app.crud import token as crud_token
from app.crud import user as crud_user
from app.crud import role as crud_role
from app.models.security import Role, User


def _validate_roles(db: Session, role_ids: Iterable[int]) -> list[Role]:
    unique_ids = list(dict.fromkeys(role_ids))
    if not unique_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe asignar al menos un rol",
        )
    roles = crud_role.get_roles_by_ids(db, unique_ids)
    if len(roles) != len(unique_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uno o más roles no existen",
        )
    return roles


def _validate_password(password: str) -> None:
    try:
        validate_password_strength_func(password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


def create_user(
    db: Session,
    *,
    email: str,
    full_name: str,
    password: Optional[str],
    generate_password: bool,
    role_ids: Iterable[int],
    is_active: bool = True,
) -> tuple[User, Optional[str]]:
    normalized_email = crud_user.normalize_email(email)
    if crud_user.get_user_by_email(db, normalized_email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya está registrado",
        )

    roles = _validate_roles(db, role_ids)
    generated_password: Optional[str] = None
    if generate_password or not password:
        generated_password = generate_strong_password()
        password = generated_password

    _validate_password(password)
    user = crud_user.create_user(
        db,
        email=normalized_email,
        full_name=full_name,
        password_hash=get_password_hash(password),
        is_active=is_active,
        must_change_password=True,
    )
    crud_user.set_user_roles(db, user, roles)
    return user, generated_password


def update_user(
    db: Session,
    user: User,
    *,
    current_user_id: int,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    role_ids: Optional[Iterable[int]] = None,
    is_active: Optional[bool] = None,
) -> User:
    if is_active is False and user.id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta",
        )

    values: dict = {}
    if email is not None:
        normalized_email = crud_user.normalize_email(email)
        existing = crud_user.get_user_by_email(db, normalized_email)
        if existing and existing.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El correo ya está registrado por otro usuario",
            )
        values["email"] = normalized_email
    if full_name is not None:
        values["full_name"] = full_name
    if is_active is not None:
        values["is_active"] = is_active

    if values:
        crud_user.update_user(db, user, values)

    if is_active is False:
        crud_token.revoke_all_user_tokens(db, user.id)

    if role_ids is not None:
        roles = _validate_roles(db, role_ids)
        crud_user.set_user_roles(db, user, roles)

    return user


def deactivate_user(
    db: Session,
    user: User,
    *,
    current_user_id: int,
) -> User:
    if user.id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya está inactivo",
        )
    crud_user.deactivate_user(db, user)
    crud_token.revoke_all_user_tokens(db, user.id)
    return user


def get_user_or_404(db: Session, user_id: int) -> User:
    user = crud_user.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return user