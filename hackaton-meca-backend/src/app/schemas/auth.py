from typing import Annotated, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.password_policy import validate_password_strength_func


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str

    @field_validator("new_password")
    def validate_password_strength(cls, v: str) -> str:
        return validate_password_strength_func(v)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    def validate_password_strength(cls, v: str) -> str:
        return validate_password_strength_func(v)


class LoginStep2Response(BaseModel):
    step: str = "2fa_required"
    session_token: str


TOTPCode = Annotated[
    str,
    Field(..., strip_whitespace=True, min_length=6, max_length=10),
]


class TOTPLoginRequest(BaseModel):
    session_token: str
    code: TOTPCode


class MustChangePasswordResponse(BaseModel):
    status: str = "must_change_password"
    change_token: str


class MessageResponse(BaseModel):
    message: str