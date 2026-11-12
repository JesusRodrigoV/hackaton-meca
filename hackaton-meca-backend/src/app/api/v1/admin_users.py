from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.crud import user as crud_user
from app.schemas.user import UserOut, AdminUserCreate, AdminUserUpdate
from app.core.dependencies import require_permission, get_current_active_user
from app.core.enums import AuditLogType, PermissionCode
from app.core.email_service import send_generated_password_email
from app.core.sms_service import send_sms
from app.core.password_utils import generate_strong_password
from app.models.user import User
from app.crud import permission as crud_permission

# pagination
from fastapi_pagination import Page, Params
from app.schemas.user import UserOutWithRole
from fastapi_pagination.ext.sqlalchemy import paginate

# auditoria
from app.schemas.audit import AuditLogOut
from app.crud import audit as crud_audit

# password history
from app.models.password_history import PasswordHistory
from app.schemas.auth import PasswordHistoryOut

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/users/{user_id}/password-history",
    response_model=List[PasswordHistoryOut],
    summary="Obtener histórico de contraseñas de un usuario",
)
def get_user_password_history(
    user_id: str,
    limit: int = Query(10, description="Número máximo de registros a retornar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene el histórico de contraseñas de un usuario específico."""
    logger.debug("get_user_password_history CALLED - current_user.id=%s, requested=%s", current_user.id, user_id)
    
    # Verificar si es admin con permiso MANAGE_USERS o si es el propio usuario
    is_admin = getattr(current_user, "is_admin", False)
    if not is_admin:
        is_admin = crud_permission.user_has_permissions(
            db, current_user.id, [PermissionCode.MANAGE_USERS.value]
        )

    if not is_admin and current_user.id != user_id:
        logger.warning(f"Permiso denegado: Usuario {current_user.id} intentó ver historial de {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tienes permiso para ver el historial de otro usuario (Tu ID: {current_user.id}, Solicitado: {user_id})"
        )

    user = crud_user.get_user(db=db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    history = crud_user.get_password_history(db=db, user_id=user_id, limit=limit)
    return [
        {
            "id": record.id,
            "user_id": record.user_id,
            "password_hash": record.password_hash,
            "created_at": record.created_at,
        }
        for record in history
    ]

@router.delete(
    "/users/{user_id}/password-history",
    status_code=status.HTTP_200_OK,
    summary="Limpiar histórico de contraseñas de un usuario",
)
def clear_user_password_history(
    user_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Elimina todo el histórico de contraseñas de un usuario específico."""
    is_admin = getattr(current_user, "is_admin", False)
    if not is_admin:
        is_admin = crud_permission.user_has_permissions(
            db, current_user.id, [PermissionCode.MANAGE_USERS.value]
        )
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes para realizar esta accion"
        )

    user = crud_user.get_user(db=db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    db.query(PasswordHistory).filter(PasswordHistory.user_id == user_id).delete()
    db.commit()

    return {
        "msg": "Historial de contraseñas eliminado exitosamente"
    }

@router.get(
    "/users",
    response_model=Page[UserOutWithRole],
    dependencies=[Depends(require_permission(PermissionCode.MANAGE_USERS))],
)
def admin_list_users(
    role_id: Optional[int] = Query(
        None, description="Filtrar por ID de Rol (1:Admin, 3:Cuidador, 4:Vet)"
    ),
    is_active: Optional[bool] = Query(
        None, description="Filtrar por estado activo/inactivo"
    ),
    search: Optional[str] = Query(None, description="Buscar por nombre o email"),
    sort_by: Optional[str] = Query(
        "id", description="Campo para ordenar: id, email, username, created_at"
    ),
    sort_type: Optional[str] = Query("desc", description="Dirección: asc o desc"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    db: Session = Depends(get_db),
):
    return paginate(
        crud_user.get_users_query(
            db=db,
            role_id=role_id,
            is_active=is_active,
            search=search,
            sort_by=sort_by,
            sort_type=sort_type,
        ),
        Params(page=page, size=size),
    )

@router.get(
    "/users/{user_id}", 
    response_model=UserOut,
    dependencies=[Depends(require_permission(PermissionCode.MANAGE_USERS))]
)
def admin_get_user(user_id: str, db: Session = Depends(get_db)):
    user = crud_user.get_user(db=db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
    return user

@router.post(
    "/users",
    response_model=UserOut,
    status_code=201,
    dependencies=[Depends(require_permission(PermissionCode.MANAGE_USERS))]
)
async def admin_create_user(user_in: AdminUserCreate, db: Session = Depends(get_db)):
    if user_in.email and crud_user.get_user_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email ya registrado"
        )

    if user_in.generate_password:
        generated = generate_strong_password()
        user_in.password = generated
    elif not user_in.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe enviar una contraseña o indicar generate_password=true",
        )

    user = crud_user.create_user_by_admin(db=db, user_in=user_in)

    if user_in.generate_password:
        try:
            if user.email:
                await send_generated_password_email(
                    email_to=user.email,
                    password=user_in.password,
                    username=user.username,
                )
            if user.phone_number:
                msg = (
                    f"ZooConnect: tu cuenta ha sido creada. "
                    f"Tu contraseña temporal es: {user_in.password}. "
                    f"Debes cambiarla al iniciar sesión."
                )
                await send_sms(user.phone_number, msg)
        except Exception as e:
            logger.exception("Error enviando credenciales a %s", user.email or user.phone_number)

    return user

@router.put(
    "/users/{user_id}", 
    response_model=UserOut,
    dependencies=[Depends(require_permission(PermissionCode.MANAGE_USERS))]
)
def admin_update_user(
    user_id: str, user_in: AdminUserUpdate, db: Session = Depends(get_db)
):
    user_db = crud_user.get_user(db, user_id)
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
    return crud_user.update_user_by_admin(
        db=db, db_user_to_update=user_db, user_in=user_in
    )

@router.delete(
    "/users/{user_id}", 
    response_model=UserOut,
    dependencies=[Depends(require_permission(PermissionCode.MANAGE_USERS))]
)
def admin_delete_user(user_id: str, db: Session = Depends(get_db)):
    user_db = crud_user.get_user(db, user_id)
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
    return crud_user.delete_user_by_admin(db=db, user_id_to_delete=user_id)

@router.get(
    "/audit-logs",
    response_model=Page[AuditLogOut],
    dependencies=[Depends(require_permission(PermissionCode.AUDIT_SECURITY_LOGS))],
    summary="Obtener logs de auditoria de autenticacion",
)
def get_audit_logs(db: Session = Depends(get_db)):
    return paginate(
        crud_audit.get_audit_logs_by_type_query(db=db, log_type=AuditLogType.SECURITY)
    )
