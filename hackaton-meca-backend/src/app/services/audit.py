from typing import Any, Optional

from fastapi import Request

from app.core.enums import AuditAction, AuditEntity
from app.core.request_context import (
    current_client_ip,
    current_request_id,
    current_user_agent,
    resolve_client_ip,
    resolve_request_id,
    resolve_user_agent,
)
from app.crud import audit as crud_audit


def log_event(
    *,
    action: AuditAction | str,
    entity: AuditEntity | str,
    entity_id: Optional[str | int] = None,
    details: Optional[dict[str, Any]] = None,
    user_id: Optional[int] = None,
    request: Optional[Request] = None,
) -> None:
    crud_audit.create_audit_log(
        action=action,
        entity=entity,
        entity_id=entity_id,
        details_json=details,
        user_id=user_id,
        ip_address=resolve_client_ip(request) if request else current_client_ip.get(),
        user_agent=resolve_user_agent(request) if request else current_user_agent.get(),
        request_id=resolve_request_id(request) if request else current_request_id.get(),
    )