from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Nombre del rol")


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(
        None, min_length=1, max_length=50, description="Nombre del rol"
    )


class RolePermissionToggle(BaseModel):
    permission_id: int
    allowed: bool = True


class RolePermissionState(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    module: str
    is_active: bool
    allowed: bool


class RolePermissionsItem(BaseModel):
    id: int
    name: str
    permissions: List[RolePermissionState] = Field(default_factory=list)


class RoleItem(BaseModel):
    id: int
    name: str
    user_count: int = 0
    has_custom_permissions: bool = False

    model_config = ConfigDict(from_attributes=True)


class RoleDetail(RoleItem):
    permissions: List[RolePermissionState] = Field(default_factory=list)


class RoleOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
