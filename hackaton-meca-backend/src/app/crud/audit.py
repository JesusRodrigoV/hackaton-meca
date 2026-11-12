import json
import logging
from datetime import date, datetime, time, timezone
from enum import Enum
from typing import Any, Optional

from sqlalchemy.orm import Query, Session, joinedload

from app.core.enums import AuditAction, AuditEntity
from app.db.session import SessionLocal
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


def _enum_value(value: Enum | str) -> str:
    return value.value if isinstance(value, Enum) else str(value)


def _clip(value: Optional[str], max_length: int) -> Optional[str]:
    if value is None:
        return None
    return value[:max_length]


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    return json.loads(json.dumps(value, default=str))


def create_audit_log(
    *,
    action: AuditAction | str,
    entity: AuditEntity | str,
    entity_id: Optional[str | int] = None,
    details_json: Optional[dict] = None,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    """Write an audit row in an isolated session.

    The caller must commit its own transaction first. This function never raises:
    an audit failure must not break the business response.
    """
    db: Session = SessionLocal()
    try:
        db.add(
            AuditLog(
                user_id=user_id,
                action=_clip(_enum_value(action), 80),
                entity=_clip(_enum_value(entity), 80),
                entity_id=_clip(
                    None if entity_id is None else str(entity_id),
                    50,
                ),
                details_json=_json_safe(details_json),
                ip_address=_clip(ip_address, 45),
                user_agent=_clip(user_agent, 300),
                request_id=_clip(request_id, 64),
            )
        )
        db.commit()
    except Exception:
        logger.exception("No se pudo registrar el evento de auditoría")
        db.rollback()
    finally:
        db.close()


def get_audit_logs_query(
    db: Session,
    *,
    action: Optional[str] = None,
    entity: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
) -> Query:
    query = db.query(AuditLog).options(joinedload(AuditLog.user))

    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action.strip()}%"))
    if entity:
        query = query.filter(AuditLog.entity == entity.strip())
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id.strip())
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if date_from:
        query = query.filter(
            AuditLog.created_at
            >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to:
        query = query.filter(
            AuditLog.created_at
            <= datetime.combine(date_to, time.max, tzinfo=timezone.utc)
        )
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            AuditLog.action.ilike(pattern)
            | AuditLog.entity.ilike(pattern)
            | AuditLog.entity_id.ilike(pattern)
            | AuditLog.ip_address.ilike(pattern)
            | AuditLog.user_agent.ilike(pattern)
        )

    return query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())


def get_audit_log(db: Session, log_id: int) -> Optional[AuditLog]:
    return (
        db.query(AuditLog)
        .options(joinedload(AuditLog.user))
        .filter(AuditLog.id == log_id)
        .first()
    )