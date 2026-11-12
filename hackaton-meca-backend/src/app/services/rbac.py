from typing import Iterable, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.crud import permission as crud_permission
from app.crud import role as crud_role
from app.models.security import Permission, Role
from app.schemas.role import RoleDetail, RoleItem, RolePermissionState


def get_role_or_404(db: Session, role_id: int) -> Role:
    role = crud_role.get_role_with_permissions(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado",
        )
    return role


def build_role_item(db: Session, role: Role) -> RoleItem:
    return RoleItem(
        id=role.id,
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        user_count=crud_role.count_users_for_role(db, role.id),
    )


def build_role_detail(db: Session, role: Role) -> RoleDetail:
    assigned_ids = {permission.id for permission in role.permissions}
    permissions = [
        RolePermissionState(
            id=permission.id,
            code=permission.code,
            name=permission.name,
            description=permission.description,
            module=permission.module,
            is_active=permission.is_active,
            assigned=permission.id in assigned_ids,
        )
        for permission in crud_permission.list_permissions(db)
    ]
    return RoleDetail(
        id=role.id,
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        user_count=crud_role.count_users_for_role(db, role.id),
        permissions=permissions,
    )


def _validate_role_name(
    db: Session,
    name: str,
    *,
    role_id: Optional[int] = None,
) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre del rol es obligatorio",
        )
    existing = crud_role.get_role_by_name(db, cleaned)
    if existing and existing.id != role_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre del rol ya existe",
        )
    return cleaned


def create_role(
    db: Session,
    *,
    name: str,
    description: Optional[str] = None,
) -> Role:
    cleaned = _validate_role_name(db, name)
    return crud_role.create_role(
        db,
        name=cleaned,
        description=description,
        is_system=False,
    )


def update_role(
    db: Session,
    role: Role,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Role:
    cleaned_name = None
    if name is not None:
        cleaned_name = _validate_role_name(db, name, role_id=role.id)
        if role.is_system and cleaned_name != role.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los roles del sistema no se pueden renombrar",
            )
    return crud_role.update_role(
        db,
        role,
        name=cleaned_name,
        description=description,
    )


def delete_role(db: Session, role: Role) -> None:
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los roles del sistema no se pueden eliminar",
        )
    if crud_role.count_users_for_role(db, role.id) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar un rol con usuarios asignados",
        )
    crud_role.delete_role(db, role)


def replace_role_permissions(
    db: Session,
    role: Role,
    permission_ids: Iterable[int],
) -> Role:
    ids = list(dict.fromkeys(permission_ids))
    permissions = crud_permission.get_permissions_by_ids(db, ids)
    if len(permissions) != len(ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uno o más permisos no existen o están inactivos",
        )
    return crud_role.replace_role_permissions(db, role, ids)


def create_permission(
    db: Session,
    *,
    code: str,
    name: str,
    module: str,
    description: Optional[str] = None,
) -> Permission:
    cleaned_code = code.strip()
    if crud_permission.get_permission_by_code(db, cleaned_code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El código de permiso ya existe",
        )
    return crud_permission.create_permission(
        db,
        code=cleaned_code,
        name=name,
        module=module,
        description=description,
    )


def update_permission(
    db: Session,
    permission_id: int,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Permission:
    permission = crud_permission.get_permission(db, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado",
        )
    return crud_permission.update_permission(
        db,
        permission,
        name=name,
        description=description,
        is_active=is_active,
    )


def deactivate_permission(db: Session, permission_id: int) -> Permission:
    permission = crud_permission.get_permission(db, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado",
        )
    if not permission.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El permiso ya está inactivo",
        )
    return crud_permission.update_permission(db, permission, is_active=False)