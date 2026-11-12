from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app.core.dependencies import require_permission
from app.core.enums import AuditLogType, PermissionCode
from app.crud import audit as crud_audit
from app.db.session import get_db
from app.schemas.audit import AuditLogOut

router = APIRouter()


from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query as FastAPIQuery

@router.get(
    "/application",
    response_model=Page[AuditLogOut],
    dependencies=[Depends(require_permission(PermissionCode.AUDIT_APPLICATION_LOGS))],
    summary="Obtener log de aplicación",
)
def get_application_logs(
    db: Session = Depends(get_db),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    user_id: Optional[str] = None,
):
    return paginate(
        crud_audit.get_audit_logs_by_type_query(
            db=db, 
            log_type=AuditLogType.APPLICATION,
            date_from=date_from,
            date_to=date_to,
            search=search,
            user_id=user_id
        )
    )


@router.get(
    "/security",
    response_model=Page[AuditLogOut],
    dependencies=[Depends(require_permission(PermissionCode.AUDIT_SECURITY_LOGS))],
    summary="Obtener log de seguridad OSI",
)
def get_security_logs(
    db: Session = Depends(get_db),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    user_id: Optional[str] = None,
):
    return paginate(
        crud_audit.get_audit_logs_by_type_query(
            db=db, 
            log_type=AuditLogType.SECURITY,
            date_from=date_from,
            date_to=date_to,
            search=search,
            user_id=user_id
        )
    )
