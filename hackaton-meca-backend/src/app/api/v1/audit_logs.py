from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app.core.dependencies import require_permission
from app.core.enums import PermissionCode
from app.crud import audit as crud_audit
from app.db.session import get_db
from app.models.security import User
from app.schemas.audit import AuditLogOut

router = APIRouter()


@router.get("", response_model=Page[AuditLogOut])
def list_audit_logs(
    action: Optional[str] = Query(None),
    entity: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _: User = Depends(require_permission(PermissionCode.AUDITORIA_VER)),
    db: Session = Depends(get_db),
):
    query = crud_audit.get_audit_logs_query(
        db,
        action=action,
        entity=entity,
        entity_id=entity_id,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )
    return paginate(query, Params(page=page, size=size))


@router.get("/integrity")
def verify_audit_integrity(
    _: User = Depends(require_permission(PermissionCode.AUDITORIA_VER)),
    db: Session = Depends(get_db),
):
    logs = db.query(crud_audit.AuditLog).order_by(crud_audit.AuditLog.id.asc()).all()
    valid = True
    prev = None
    for l in logs:
        if l.prev_hash != prev:
            valid = False
            break
        prev = l.row_hash
    return {"valid": valid, "total_events": len(logs)}


@router.get("/{log_id}", response_model=AuditLogOut)
def get_audit_log(
    log_id: int,
    _: User = Depends(require_permission(PermissionCode.AUDITORIA_VER)),
    db: Session = Depends(get_db),
):
    log = crud_audit.get_audit_log(db, log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de auditoría no encontrado",
        )
    return log