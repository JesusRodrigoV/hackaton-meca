from typing import Iterable, Optional

from sqlalchemy import func
from sqlalchemy.orm import Query, Session, selectinload

from app.models.security import Permission, Role, UserRole


def list_roles(db: Session, search: Optional[str] = None) -> Query:
    query = db.query(Role).options(selectinload(Role.permissions)).order_by(Role.name)
    if search:
        query = query.filter(Role.name.ilike(f"%{search.strip()}%"))
    return query


def get_role(db: Session, role_id: int) -> Optional[Role]:
    return db.query(Role).filter(Role.id == role_id).first()


def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    return db.query(Role).filter(func.lower(Role.name) == name.strip().lower()).first()


def get_role_with_permissions(db: Session, role_id: int) -> Optional[Role]:
    return (
        db.query(Role)
        .options(selectinload(Role.permissions))
        .filter(Role.id == role_id)
        .first()
    )


def get_roles_by_ids(db: Session, role_ids: Iterable[int]) -> list[Role]:
    ids = list(dict.fromkeys(role_ids))
    if not ids:
        return []
    return db.query(Role).filter(Role.id.in_(ids)).order_by(Role.name).all()


def count_users_for_role(db: Session, role_id: int) -> int:
    return (
        db.query(func.count(UserRole.user_id))
        .filter(UserRole.role_id == role_id)
        .scalar()
        or 0
    )


def create_role(
    db: Session,
    *,
    name: str,
    description: Optional[str] = None,
    is_system: bool = False,
) -> Role:
    role = Role(
        name=name.strip(),
        description=description,
        is_system=is_system,
    )
    db.add(role)
    db.flush()
    return role


def update_role(
    db: Session,
    role: Role,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Role:
    if name is not None:
        cleaned = name.strip()
        if role.is_system and cleaned != role.name:
            raise ValueError("Los roles del sistema no se pueden renombrar")
        role.name = cleaned
    if description is not None:
        role.description = description
    db.add(role)
    db.flush()
    return role


def delete_role(db: Session, role: Role) -> None:
    if role.is_system:
        raise ValueError("Los roles del sistema no se pueden eliminar")
    if count_users_for_role(db, role.id) > 0:
        raise ValueError("No se puede eliminar un rol con usuarios asignados")

    db.delete(role)
    db.flush()


def get_role_permissions(db: Session, role_id: int) -> list[Permission]:
    role = get_role_with_permissions(db, role_id)
    return list(role.permissions) if role else []


def replace_role_permissions(
    db: Session,
    role: Role,
    permission_ids: Iterable[int],
) -> Role:
    ids = list(dict.fromkeys(permission_ids))
    permissions = (
        db.query(Permission)
        .filter(Permission.id.in_(ids), Permission.is_active.is_(True))
        .all()
        if ids
        else []
    )
    role.permissions = permissions
    db.add(role)
    db.flush()
    return role