from pydantic import BaseModel, Field, constr
from typing import Annotated, List

class TOTPSetupResponse(BaseModel):
    secret: str
    otpauth_uri: str

TOTPCode = Annotated[str, Field(strip_whitespace=True, pattern=r'^[0-9]{6}$', min_length=6, max_length=6)]

class TOTPVerifyRequest(BaseModel):
    totp_code: TOTPCode
    
class TOTPBackupCodesResponse(BaseModel):
    backup_codes: List[str]

class TOTPDisableRequest(BaseModel):
    password: str