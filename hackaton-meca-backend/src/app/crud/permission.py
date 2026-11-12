from typing import Iterable, Optional

from sqlalchemy.orm import Query, Session

from app.models.security import Permission, RolePermission, UserRole


def list_permissions(db: Session, include_inactive: bool = False) -> list[Permission]:
    query = db.query(Permission)
    if not include_inactive:
        query = query.filter(Permission.is_active.is_(True))
    return query.order_by(Permission.module, Permission.name).all()


def get_permissions_query(db: Session, include_inactive: bool = False) -> Query:
    query = db.query(Permission)
    if not include_inactive:
        query = query.filter(Permission.is_active.is_(True))
    return query.order_by(Permission.module, Permission.name)


def get_permission(db: Session, permission_id: int) -> Optional[Permission]:
    return db.query(Permission).filter(Permission.id == permission_id).first()


def get_permission_by_code(db: Session, code: str) -> Optional[Permission]:
    return db.query(Permission).filter(Permission.code == code.strip()).first()


def get_permissions_by_ids(db: Session, permission_ids: Iterable[int]) -> list[Permission]:
    ids = list(dict.fromkeys(permission_ids))
    if not ids:
        return []
    return (
        db.query(Permission)
        .filter(Permission.id.in_(ids), Permission.is_active.is_(True))
        .all()
    )


def get_permissions_by_codes(
    db: Session,
    permission_codes: Iterable[str],
) -> list[Permission]:
    codes = [code.strip() for code in permission_codes if code and code.strip()]
    if not codes:
        return []
    return (
        db.query(Permission)
        .filter(Permission.code.in_(codes), Permission.is_active.is_(True))
        .all()
    )


def get_effective_permission_codes(db: Session, user_id: int) -> list[str]:
    rows = (
        db.query(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .filter(
            UserRole.user_id == user_id,
            Permission.is_active.is_(True),
        )
        .distinct()
        .order_by(Permission.code)
        .all()
    )
    return [row[0] for row in rows]


def has_all_permissions(
    effective_permissions: Iterable[str],
    required_permissions: Iterable[str],
) -> bool:
    required = set(required_permissions)
    if not required:
        return True
    return required.issubset(set(effective_permissions))


def user_has_permissions(
    db: Session,
    user_id: int,
    required_permissions: Iterable[str],
) -> bool:
    required = set(required_permissions)
    if not required:
        return True
    return has_all_permissions(
        get_effective_permission_codes(db, user_id),
        required,
    )


def create_permission(
    db: Session,
    *,
    code: str,
    name: str,
    module: str,
    description: Optional[str] = None,
    is_active: bool = True,
) -> Permission:
    permission = Permission(
        code=code.strip(),
        name=name.strip(),
        module=module.strip(),
        description=description,
        is_active=is_active,
    )
    db.add(permission)
    db.flush()
    return permission


def update_permission(
    db: Session,
    permission: Permission,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Permission:
    if name is not None:
        permission.name = name.strip()
    if description is not None:
        permission.description = description
    if is_active is not None:
        permission.is_active = is_active
    db.add(permission)
    db.flush()
    return permission