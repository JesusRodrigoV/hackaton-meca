from pydantic import BaseModel, EmailStr, Field, constr, validator
from typing import List, Optional, Annotated, Union
from datetime import datetime

# ret token
import re

class LoginRequest(BaseModel):
    identifier: str
    password: str
    recaptcha_token: Optional[str] = None

# cambios refresh token jesus
# class TokenRefreshRequest(BaseModel):
#    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    # refresh_token: str
    token_type: str = "bearer"
    # expires_in: int | None = None

    # class Config:
    #    from_attributes = True


from app.core.password_policy import validate_password_strength_func

class ForgotPasswordRequest(BaseModel):
    identifier: str


class ResetPasswordRequest(BaseModel):
    identifier: str
    code: str
    new_password: str

    @validator("new_password")
    def validate_password_strength(cls, v):
        return validate_password_strength_func(v)

class EmailVerificationRequest(BaseModel):
    phone_number: str
    code: str
    recaptcha_token: Optional[str] = None

class ResendVerificationRequest(BaseModel):
    phone_number: Optional[str] = None
    email: Optional[str] = None

class UpdatePhoneRequest(BaseModel):
    phone_number: str
    recaptcha_token: Optional[str] = None

# 2fa
class LoginStep2Response(BaseModel):
    step: str = "2fa_required"
    session_token: str


TOTPCodem = Annotated[
    str, Field(..., strip_whitespace=True, min_length=6, max_length=10)
]


class TOTPLoginRequest(BaseModel):
    session_token: str
    code: TOTPCodem

class MustChangePasswordResponse(BaseModel):
    status: str = "must_change_password"
    reset_token: str


# Password History
class PasswordHistoryOut(BaseModel):
    id: int
    user_id: str
    password_hash: str
    created_at: datetime

    class Config:
        from_attributes = True

