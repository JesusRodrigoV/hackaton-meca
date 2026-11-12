from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.password_policy import validate_password_strength_func
from app.schemas.role import RoleOut


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=150)


class UserCreate(UserBase):
    password: Optional[str] = None
    generate_password: bool = False

    @field_validator("password")
    def validate_password_strength(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return validate_password_strength_func(v)
        return v


class AdminUserCreate(UserCreate):
    role_ids: List[int] = Field(default_factory=list)
    is_active: bool = True


class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=150)
    role_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None


class UserUpdateProfile(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=150)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    must_change_password: bool = False
    is_totp_enabled: bool = False
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    roles: List[RoleOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UserOutWithRole(UserOut):
    """Alias de compatibilidad; los roles ya vienen incluidos en UserOut."""


class UserProfileOut(UserOut):
    permissions: List[str] = Field(default_factory=list)


class UserCreateResponse(UserOut):
    generated_password: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)