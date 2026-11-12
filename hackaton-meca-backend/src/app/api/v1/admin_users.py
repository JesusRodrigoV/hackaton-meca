from typing import Optional

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
from app.core.email_service import send_generated_password_email
from app.core.enums import AuditAction, AuditEntity, PermissionCode
from app.crud import user as crud_user
from app.db.session import get_db
from app.models.security import User
from app.schemas.auth import MessageResponse
from app.schemas.user import (
    AdminUserCreate,
    AdminUserUpdate,
    UserCreateResponse,
    UserOut,
)
from app.services import audit as audit_service
from app.services import users as user_service

router = APIRouter()


@router.get("", response_model=Page[UserOut])
def list_users(
    role_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("id"),
    sort_type: str = Query("desc"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _: User = Depends(require_permission(PermissionCode.USUARIOS_ADMIN)),
    db: Session = Depends(get_db),
):
    query = crud_user.get_users_query(
        db,
        role_id=role_id,
        is_active=is_active,
        search=search,
        sort_by=sort_by,
        sort_type=sort_type,
    )
    return paginate(query, Params(page=page, size=size))


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    _: User = Depends(require_permission(PermissionCode.USUARIOS_ADMIN)),
    db: Session = Depends(get_db),
):
    return user_service.get_user_or_404(db, user_id)


@router.post("", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminUserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(require_permission(PermissionCode.USUARIOS_ADMIN)),
    db: Session = Depends(get_db),
):
    user, generated_password = user_service.create_user(
        db,
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        generate_password=payload.generate_password,
        role_ids=payload.role_ids,
        is_active=payload.is_active,
    )
    db.commit()

    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.USER_CREATE,
        entity=AuditEntity.USER,
        entity_id=user.id,
        details={
            "email": user.email,
            "role_ids": [role.id for role in user.roles],
            "generated_password": bool(generated_password),
        },
        user_id=current_user.id,
        request=request,
    )

    if generated_password:
        background_tasks.add_task(
            send_generated_password_email,
            user.email,
            generated_password,
            user.full_name,
        )

    response = UserCreateResponse.model_validate(user)
    response.generated_password = generated_password
    return response


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(require_permission(PermissionCode.USUARIOS_ADMIN)),
    db: Session = Depends(get_db),
):
    user = user_service.get_user_or_404(db, user_id)
    user_service.update_user(
        db,
        user,
        current_user_id=current_user.id,
        email=payload.email,
        full_name=payload.full_name,
        role_ids=payload.role_ids,
        is_active=payload.is_active,
    )
    db.commit()

    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.USER_UPDATE,
        entity=AuditEntity.USER,
        entity_id=user.id,
        details={
            "email": user.email,
            "is_active": user.is_active,
            "role_ids": [role.id for role in user.roles],
        },
        user_id=current_user.id,
        request=request,
    )
    return UserOut.model_validate(user)


@router.delete("/{user_id}", response_model=MessageResponse)
def deactivate_user(
    user_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(require_permission(PermissionCode.USUARIOS_ADMIN)),
    db: Session = Depends(get_db),
):
    user = user_service.get_user_or_404(db, user_id)
    user_service.deactivate_user(
        db,
        user,
        current_user_id=current_user.id,
    )
    db.commit()

    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.USER_DEACTIVATE,
        entity=AuditEntity.USER,
        entity_id=user.id,
        details={"email": user.email},
        user_id=current_user.id,
        request=request,
    )
    return MessageResponse(message="Usuario desactivado correctamente")


@router.get("/{user_id}/scopes")
def get_user_scopes(
    user_id: int,
    _: User = Depends(require_permission(PermissionCode.USUARIOS_ADMIN)),
    db: Session = Depends(get_db),
):
    user_service.get_user_or_404(db, user_id)
    scopes = crud_user.get_user_data_scopes(db, user_id)
    return [
        {"dimension_type": s.dimension_type, "dimension_id": s.dimension_id}
        for s in scopes
    ]


@router.put("/{user_id}/scopes")
def update_user_scopes(
    user_id: int,
    payload: list[dict],
    current_user: User = Depends(require_permission(PermissionCode.USUARIOS_ADMIN)),
    db: Session = Depends(get_db),
):
    user_service.get_user_or_404(db, user_id)
    updated = crud_user.replace_user_data_scopes(db, user_id, payload)
    db.commit()
    return [
        {"dimension_type": s.dimension_type, "dimension_id": s.dimension_id}
        for s in updated
    ]
