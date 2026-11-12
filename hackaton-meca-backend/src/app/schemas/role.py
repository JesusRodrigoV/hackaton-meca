from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None


class RolePermissionUpdate(BaseModel):
    """Reemplaza la matriz del rol. La presencia del permiso significa permitido."""

    permission_ids: List[int] = Field(default_factory=list)


class RolePermissionState(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    module: str
    is_active: bool
    assigned: bool = False


class RolePermissionsItem(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[RolePermissionState] = Field(default_factory=list)


class RoleItem(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_system: bool = False
    user_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class RoleDetail(RoleItem):
    permissions: List[RolePermissionState] = Field(default_factory=list)


class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_system: bool = False

    model_config = ConfigDict(from_attributes=True)