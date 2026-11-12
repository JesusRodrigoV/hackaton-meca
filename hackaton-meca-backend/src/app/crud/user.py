from datetime import datetime, timezone
from typing import Iterable, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Query, Session, selectinload

from app.core.config import settings
from app.core.policia import lockout_deadline
from app.core.security import get_password_hash
from app.models.security import Role, User, UserDataScope


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _user_query(db: Session) -> Query:
    return db.query(User).options(
        selectinload(User.roles).selectinload(Role.permissions)
    )


def get_user(db: Session, user_id: int) -> Optional[User]:
    return _user_query(db).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    normalized = normalize_email(email)
    return _user_query(db).filter(func.lower(User.email) == normalized).first()


def get_users_query(
    db: Session,
    role_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "id",
    sort_type: Optional[str] = "desc",
) -> Query:
    query = _user_query(db)

    if role_id is not None:
        query = query.filter(User.roles.any(Role.id == role_id))
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.email.ilike(pattern),
                User.full_name.ilike(pattern),
            )
        )

    valid_sort_fields = {
        "id": User.id,
        "email": User.email,
        "full_name": User.full_name,
        "is_active": User.is_active,
        "last_login_at": User.last_login_at,
        "created_at": User.created_at,
    }
    sort_field = valid_sort_fields.get(sort_by or "id", User.id)
    if (sort_type or "desc").lower() == "asc":
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())
    return query


def create_user(
    db: Session,
    *,
    email: str,
    full_name: str,
    password_hash: str,
    is_active: bool = True,
    must_change_password: bool = True,
) -> User:
    user = User(
        email=normalize_email(email),
        full_name=full_name.strip(),
        password_hash=password_hash,
        is_active=is_active,
        must_change_password=must_change_password,
    )
    db.add(user)
    db.flush()
    return user


def update_user(db: Session, user: User, values: dict) -> User:
    for field, value in values.items():
        if field == "email" and value is not None:
            value = normalize_email(value)
        setattr(user, field, value)
    db.add(user)
    db.flush()
    return user


def deactivate_user(db: Session, user: User) -> User:
    user.is_active = False
    db.add(user)
    db.flush()
    return user


def set_user_roles(db: Session, user: User, roles: Iterable[Role]) -> User:
    user.roles = list(roles)
    db.add(user)
    db.flush()
    return user


def increment_failed_attempts(db: Session, user: User) -> bool:
    attempts = int(user.failed_attempts or 0) + 1
    locked = attempts >= settings.MAX_FAILED_ATTEMPTS
    if locked:
        user.failed_attempts = 0
        user.locked_until = lockout_deadline()
    else:
        user.failed_attempts = attempts
    db.add(user)
    db.flush()
    return locked


def reset_failed_attempts(db: Session, user: User) -> User:
    user.failed_attempts = 0
    user.locked_until = None
    db.add(user)
    db.flush()
    return user


def mark_login_success(db: Session, user: User) -> User:
    user.last_login_at = datetime.now(timezone.utc)
    user.failed_attempts = 0
    user.locked_until = None
    db.add(user)
    db.flush()
    return user


def set_password(
    db: Session,
    user: User,
    new_password: str,
    *,
    must_change_password: bool = False,
) -> User:
    user.password_hash = get_password_hash(new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    user.must_change_password = must_change_password
    db.add(user)
    db.flush()
    return user


def get_user_data_scopes(db: Session, user_id: int) -> list[UserDataScope]:
    return (
        db.query(UserDataScope)
        .filter(UserDataScope.user_id == user_id)
        .order_by(UserDataScope.dimension_type, UserDataScope.dimension_id)
        .all()
    )


def replace_user_data_scopes(
    db: Session,
    user_id: int,
    scopes: Iterable[dict],
) -> list[UserDataScope]:
    db.query(UserDataScope).filter(UserDataScope.user_id == user_id).delete(
        synchronize_session=False
    )
    for item in scopes:
        db.add(
            UserDataScope(
                user_id=user_id,
                dimension_type=item["dimension_type"],
                dimension_id=item["dimension_id"],
            )
        )
    db.flush()
    return get_user_data_scopes(db, user_id)