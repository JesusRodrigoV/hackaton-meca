from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_permission
from app.core.enums import AuditAction, AuditEntity, PermissionCode
from app.crud import permission as crud_permission
from app.db.session import get_db
from app.models.security import User
from app.schemas.auth import MessageResponse
from app.schemas.permission import (
    PermissionCreate,
    PermissionOut,
    PermissionUpdate,
)
from app.services import audit as audit_service
from app.services import rbac as rbac_service

router = APIRouter()


@router.get("", response_model=List[PermissionOut])
def list_permissions(
    _: User = Depends(require_permission(PermissionCode.ROLES_ADMIN)),
    db: Session = Depends(get_db),
):
    return crud_permission.list_permissions(db)


@router.post(
    "",
    response_model=PermissionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_permission(
    payload: PermissionCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(require_permission(PermissionCode.ROLES_ADMIN)),
    db: Session = Depends(get_db),
):
    permission = rbac_service.create_permission(
        db,
        code=payload.code,
        name=payload.name,
        module=payload.module,
        description=payload.description,
    )
    db.commit()
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.PERMISSION_CREATE,
        entity=AuditEntity.PERMISSION,
        entity_id=permission.id,
        details={"code": permission.code, "module": permission.module},
        user_id=current_user.id,
        request=request,
    )
    return permission


@router.put("/{permission_id}", response_model=PermissionOut)
def update_permission(
    permission_id: int,
    payload: PermissionUpdate,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(require_permission(PermissionCode.ROLES_ADMIN)),
    db: Session = Depends(get_db),
):
    permission = rbac_service.update_permission(
        db,
        permission_id,
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
    )
    db.commit()
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.PERMISSION_UPDATE,
        entity=AuditEntity.PERMISSION,
        entity_id=permission.id,
        details={
            "code": permission.code,
            "is_active": permission.is_active,
        },
        user_id=current_user.id,
        request=request,
    )
    return permission


@router.delete("/{permission_id}", response_model=MessageResponse)
def deactivate_permission(
    permission_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(require_permission(PermissionCode.ROLES_ADMIN)),
    db: Session = Depends(get_db),
):
    permission = rbac_service.deactivate_permission(db, permission_id)
    db.commit()
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.PERMISSION_DELETE,
        entity=AuditEntity.PERMISSION,
        entity_id=permission.id,
        details={"code": permission.code},
        user_id=current_user.id,
        request=request,
    )
    return MessageResponse(message="Permiso desactivado correctamente")