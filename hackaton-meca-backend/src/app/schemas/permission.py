from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PermissionBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=120)
    module: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PermissionOut(PermissionBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PermissionGroup(BaseModel):
    module: str
    permissions: List[PermissionOut] = Field(default_factory=list)