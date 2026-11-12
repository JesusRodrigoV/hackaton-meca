from typing import List, Optional

from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.enums import UserRole
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.schemas.role import (
    RoleCreate,
    RoleDetail,
    RoleItem,
    RolePermissionToggle,
    RoleUpdate,
)


def list_roles(db: Session) -> List[Role]:
    return db.query(Role).order_by(Role.name).all()


def get_role(db: Session, role_id: int) -> Optional[Role]:
    return db.query(Role).filter(Role.id == role_id).first()


def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    return db.query(Role).filter(func.lower(Role.name) == name.lower()).first()


def get_role_with_permissions(db: Session, role_id: int) -> Optional[Role]:
    return (
        db.query(Role)
        .options(
            joinedload(Role.role_permissions).joinedload(RolePermission.permission)
        )
        .filter(Role.id == role_id)
        .first()
    )


def _get_role_permission_entries(db: Session, role: Role) -> List[dict]:
    entries: List[dict] = []
    for role_permission in getattr(role, "role_permissions", []):
        permission = role_permission.permission
        if not permission or not permission.is_active:
            continue
        entries.append(
            {
                "id": permission.id,
                "code": permission.code,
                "name": permission.name,
                "description": permission.description,
                "module": permission.module,
                "is_active": permission.is_active,
                "allowed": bool(role_permission.allowed),
            }
        )
    return entries


def _build_role_item(db: Session, role: Role) -> RoleItem:
    user_count = db.query(User).filter(User.role_id == role.id, User.is_active == True).count()
    has_custom = (
        db.query(RolePermission).filter(RolePermission.role_id == role.id).first()
        is not None
    )
    return RoleItem(
        id=role.id,
        name=role.name,
        user_count=user_count,
        has_custom_permissions=has_custom,
    )


def _build_role_detail(db: Session, role: Role) -> RoleDetail:
    user_count = db.query(User).filter(User.role_id == role.id, User.is_active == True).count()
    permissions = _get_role_permission_entries(db, role)
    return RoleDetail(
        id=role.id,
        name=role.name,
        user_count=user_count,
        has_custom_permissions=len(permissions) > 0,
        permissions=permissions,
    )


def create_role(db: Session, role_in: RoleCreate) -> Role:
    role_name = role_in.name.strip()
    if not role_name:
        raise ValueError("El nombre del rol es requerido")

    existing = get_role_by_name(db, role_name)
    if existing:
        raise ValueError(f"El rol '{role_name}' ya existe")

    if role_name.lower() in [r.value.lower() for r in UserRole]:
        raise ValueError(f"El nombre '{role_name}' esta reservado para el sistema")

    _sync_role_id_sequence(db)
    role = Role(name=role_name)
    db.add(role)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        existing = get_role_by_name(db, role_name)
        if existing:
            raise ValueError(f"El rol '{role_name}' ya existe") from exc

        _sync_role_id_sequence(db)
        role = Role(name=role_name)
        db.add(role)
        db.commit()

    db.refresh(role)
    return role


def update_role(db: Session, role_id: int, role_in: RoleUpdate) -> Optional[Role]:
    role = get_role(db, role_id)
    if not role:
        return None

    if role_in.name is not None:
        role_name = role_in.name.strip()
        if not role_name:
            raise ValueError("El nombre del rol es requerido")

        existing = get_role_by_name(db, role_name)
        if existing and existing.id != role_id:
            raise ValueError(f"El rol '{role_name}' ya existe")

        if role_name.lower() in [r.value.lower() for r in UserRole]:
            raise ValueError(
                f"El nombre '{role_name}' esta reservado para el sistema"
            )

        role.name = role_name

    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role_id: int) -> bool:
    role = get_role(db, role_id)
    if not role:
        return False

    user_count = db.query(User).filter(User.role_id == role_id).count()
    if user_count > 0:
        raise ValueError(
            f"No se puede eliminar el rol porque Tiene {user_count} usuario(s) asignado(s)"
        )

    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    db.delete(role)
    db.commit()
    return True


def get_role_permissions(db: Session, role_id: int) -> List[dict]:
    role = get_role_with_permissions(db, role_id)
    if not role:
        return []
    return _get_role_permission_entries(db, role)


def get_role_permissions_query(db: Session):
    return db.query(Role).options(
        joinedload(Role.role_permissions).joinedload(RolePermission.permission)
    )


def replace_role_permissions(
    db: Session, role_id: int, permissions_payload: List[dict]
) -> Role:
    role = get_role_with_permissions(db, role_id)
    if not role:
        raise ValueError("Rol no encontrado")

    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()

    permission_ids = [item["permission_id"] for item in permissions_payload]
    permissions_by_id = {
        permission.id: permission
        for permission in db.query(Permission)
        .filter(Permission.id.in_(permission_ids))
        .all()
    }

    for item in permissions_payload:
        permission = permissions_by_id.get(item["permission_id"])
        if not permission:
            continue
        db.add(
            RolePermission(
                role_id=role_id,
                permission_id=permission.id,
                allowed=bool(item.get("allowed", True)),
            )
        )

    db.commit()
    return get_role_with_permissions(db, role_id)


def _sync_role_id_sequence(db: Session) -> None:
    if db.bind and db.bind.dialect.name == "postgresql":
        db.execute(
            text(
                """
                SELECT setval(
                    pg_get_serial_sequence('roles', 'id'),
                    COALESCE((SELECT MAX(id) FROM roles), 0) + 1,
                    false
                )
                """
            )
        )
