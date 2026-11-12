from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PermissionOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    module: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserPermissionToggle(BaseModel):
    permission_id: int
    allowed: bool = True


class UserPermissionState(PermissionOut):
    allowed: bool
    source: str


class UserPermissionMatrixItem(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: bool
    role_id: int
    role_name: str
    photo_url: Optional[str] = None
    created_at: Optional[str] = None
    permissions: List[UserPermissionState] = Field(default_factory=list)


class UserPermissionMatrixPage(BaseModel):
    items: List[UserPermissionMatrixItem]
    total: int
    page: int
    size: int
    pages: int
    permissions: List[PermissionOut]