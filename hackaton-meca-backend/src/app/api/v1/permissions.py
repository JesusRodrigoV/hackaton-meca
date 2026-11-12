from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, require_permission
from app.core.enums import AuditEvent, AuditLogType, PermissionCode
from app.crud import audit as crud_audit
from app.crud import permission as crud_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.permission import (
    PermissionOut,
    UserPermissionMatrixItem,
    UserPermissionMatrixPage,
    UserPermissionToggle,
)


router = APIRouter(
    dependencies=[Depends(require_permission(PermissionCode.MANAGE_PERMISSIONS))]
)


def _build_user_item(db: Session, user: User) -> UserPermissionMatrixItem:
    effective_permissions = crud_permission.get_effective_permission_entries(db, user.id)
    return UserPermissionMatrixItem(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        role_id=user.role_id,
        role_name=user.role.name if user.role else "",
        photo_url=user.photo_url,
        created_at=user.created_at.isoformat() if user.created_at else None,
        permissions=[
            {
                "id": entry["permission"].id,
                "code": entry["permission"].code,
                "name": entry["permission"].name,
                "description": entry["permission"].description,
                "module": entry["permission"].module,
                "is_active": entry["permission"].is_active,
                "allowed": entry["allowed"],
                "source": entry["source"],
            }
            for entry in effective_permissions
        ],
    )


@router.get("/catalog", response_model=List[PermissionOut])
def get_permissions_catalog(db: Session = Depends(get_db)):
    return crud_permission.list_permissions(db)


@router.get("/users", response_model=UserPermissionMatrixPage)
def list_users_with_permissions(
    role_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = crud_permission.get_users_with_permissions_query(db)

    if role_id is not None:
        query = query.filter(User.role_id == role_id)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        query = query.filter((User.username.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%")))

    users = query.all()
    permissions = crud_permission.list_permissions(db)
    items = [_build_user_item(db, user) for user in users]

    return UserPermissionMatrixPage(
        items=items,
        total=len(items),
        page=1,
        size=len(items) or 1,
        pages=1 if items else 0,
        permissions=permissions,
    )


@router.get("/users/{user_id}", response_model=UserPermissionMatrixItem)
def get_user_permissions(user_id: str, db: Session = Depends(get_db)):
    user = crud_permission.get_users_with_permissions_query(db).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return _build_user_item(db, user)


@router.put("/users/{user_id}", response_model=UserPermissionMatrixItem)
def update_user_permissions(
    user_id: str,
    payload: List[UserPermissionToggle] = Body(default_factory=list),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    updated_user = crud_permission.replace_user_permissions(
        db=db,
        user_id=user_id,
        permissions_payload=[item.model_dump() for item in payload],
    )

    crud_audit.create_audit_log(
        event=AuditEvent.PERMISSION_UPDATE,
        log_type=AuditLogType.SECURITY,
        action="Actualizar permisos de usuario",
        detail=f"Se actualizaron permisos específicos del usuario {updated_user.email}",
        user_id=current_user.id,
        attempted_email=updated_user.email,
    )

    return _build_user_item(db, updated_user)
