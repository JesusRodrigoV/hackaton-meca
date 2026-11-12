from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field


class TOTPSetupResponse(BaseModel):
    secret: str
    otpauth_uri: str


TOTPCode = Annotated[
    str,
    Field(
        strip_whitespace=True,
        pattern=r"^[0-9]{6}$",
        min_length=6,
        max_length=6,
    ),
]


class TOTPVerifyRequest(BaseModel):
    totp_code: TOTPCode


class TOTPBackupCodesResponse(BaseModel):
    backup_codes: List[str]


class TOTPDisableRequest(BaseModel):
    password: str
    totp_code: str = Field(..., strip_whitespace=True, min_length=6, max_length=10)


class TOTPStatusResponse(BaseModel):
    is_enabled: bool
    enabled_at: Optional[datetime] = None