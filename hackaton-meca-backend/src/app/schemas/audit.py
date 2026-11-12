from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Any, Optional

class AuditLogUser(BaseModel):
    id: str
    username: str
    email: EmailStr

    class Config:
        from_attributes = True

class AuditLogOut(BaseModel):
    id: int
    event: str
    log_type: str = "security"
    action: Optional[str] = None
    detail: Optional[str] = None
    timestamp: datetime
    attempted_email: Optional[str] = None
    ip_address: Optional[str] = None
    ip_country: Optional[str] = None
    ip_asn: Optional[int] = None
    ip_organization: Optional[str] = None
    ip_guide_data: Optional[dict[str, Any]] = None

    user: Optional[AuditLogUser] = None 

    class Config:
        from_attributes = True
