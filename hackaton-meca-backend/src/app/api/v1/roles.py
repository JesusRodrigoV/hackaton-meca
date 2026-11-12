from typing import List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Query,
    Request,
    status,
)
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app.core.dependencies import require_permission
from app.core.enums import AuditAction, AuditEntity, PermissionCode
from app.crud import permission as crud_permission
from app.crud import role as crud_role
from app.db.session import get_db
from app.models.security import User
from app.schemas.auth import MessageResponse
from app.schemas.permission import PermissionOut
from app.schemas.role import (
    RoleCreate,
    RoleDetail,
    RoleItem,
    RolePermissionUpdate,
    RoleUpdate,
)
from app.services import audit as audit_service
from app.services import rbac as rbac_service

router = APIRouter()


@router.get("", response_model=Page[RoleItem])
def list_roles(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _: User = Depends(require_permission(PermissionCode.ROLES_ADMIN)),
    db: Session = Depends(get_db),
):
    page_obj = paginate(
        crud_role.list_roles(db, search=search),
        Params(page=page, size=size),
    )
    page_obj.items = [
        rbac_service.build_role_item(db, role) for role in page_obj.items
    ]
    return page_obj


@router.get("/permissions/catalog", response_model=List[PermissionOut])
def permissions_catalog(
    _: User = Depends(require_permission(PermissionCode.ROLES_ADMIN)),
    db: Session = Depends(get_db),
):
    return crud_permission.list_permissions(db)


@router.post("", response_model=RoleItem, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(require_permission(PermissionCode.ROLES_ADMIN)),
    db: Session = Depends(get_db),
):
    role = rbac_service.create_role(
        db,
        name=payload.name,
        description=payload.description,
    )
    db.commit()
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.ROLE_CREATE,
        entity=AuditEntity.ROLE,
        entity_id=role.id,
        details={"name": role.name},
        user_id=current_user.id,
        request=request,
    )
    return rbac_service.build_role_item(db, role)


@router.get("/{role_id}", response_model=RoleDetail)
def get_role(
    role_id: int,
    _: User = Depends(require_permission(PermissionCode.ROLES_ADMIN)),
    db: Session = Depends(get_db),
):
    role = rbac_service.get_role_or_404(db, role_id)
    return rbac_service.build_role_detail(db, role)


@router.put("/{role_id}", response_model=RoleItem)
def update_role(
    role_id: int,
    payload: RoleUpdate,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(require_permission(PermissionCode.ROLES_ADMIN)),
    db: Session = Depends(get_db),
):
    role = rbac_service.get_role_or_404(db, role_id)
    rbac_service.update_role(
        db,
        role,
        name=payload.name,
        description=payload.description,
    )
    db.commit()
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.ROLE_UPDATE,
        entity=AuditEntity.ROLE,
        entity_id=role.id,
        details={"name": role.name},
        user_id=current_user.id,
        request=request,
    )
    return rbac_service.build_role_item(db, role)


@router.delete("/{role_id}", response_model=MessageResponse)
def delete_role(
    role_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(require_permission(PermissionCode.ROLES_ADMIN)),
    db: Session = Depends(get_db),
):
    role = rbac_service.get_role_or_404(db, role_id)
    role_name = role.name
    rbac_service.delete_role(db, role)
    db.commit()
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.ROLE_DELETE,
        entity=AuditEntity.ROLE,
        entity_id=role_id,
        details={"name": role_name},
        user_id=current_user.id,
        request=request,
    )
    return MessageResponse(message="Rol eliminado correctamente")


@router.get("/{role_id}/permissions", response_model=RoleDetail)
def get_role_permissions(
    role_id: int,
    _: User = Depends(require_permission(PermissionCode.ROLES_ADMIN)),
    db: Session = Depends(get_db),
):
    role = rbac_service.get_role_or_404(db, role_id)
    return rbac_service.build_role_detail(db, role)


@router.put("/{role_id}/permissions", response_model=RoleDetail)
def update_role_permissions(
    role_id: int,
    payload: RolePermissionUpdate,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(require_permission(PermissionCode.ROLES_ADMIN)),
    db: Session = Depends(get_db),
):
    role = rbac_service.get_role_or_404(db, role_id)
    rbac_service.replace_role_permissions(db, role, payload.permission_ids)
    db.commit()
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.ROLE_PERMISSIONS_UPDATE,
        entity=AuditEntity.ROLE,
        entity_id=role.id,
        details={
            "name": role.name,
            "permission_ids": payload.permission_ids,
        },
        user_id=current_user.id,
        request=request,
    )
    return rbac_service.build_role_detail(db, role)