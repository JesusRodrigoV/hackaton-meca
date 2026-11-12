from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class AuditLogUser(BaseModel):
    id: int
    email: EmailStr
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class AuditLogOut(BaseModel):
    id: int
    action: str
    entity: str
    entity_id: Optional[str] = None
    details_json: Optional[Any] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    created_at: datetime
    prev_hash: Optional[str] = None
    row_hash: Optional[str] = None
    user: Optional[AuditLogUser] = None

    model_config = ConfigDict(from_attributes=True)