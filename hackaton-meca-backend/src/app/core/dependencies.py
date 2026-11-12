from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import PermissionCode
from app.crud import permission as crud_permission
from app.crud import user as crud_user
from app.db.session import get_db
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autorizado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise credentials_exception
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = crud_user.get_user(db, user_id)
    if not user:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not getattr(current_user, "is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")
    return current_user


def get_optional_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
    except JWTError:
        return None

    user = crud_user.get_user(db, user_id)
    if not user or not user.is_active:
        return None
    return user


def require_permission(*required_permissions: PermissionCode):
    required_permission_codes = [permission.value for permission in required_permissions]

    def dependency(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ):
        if getattr(current_user, "is_admin", False):
            return current_user

        if not crud_permission.user_has_permissions(db, current_user.id, required_permission_codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes para realizar esta accion",
            )

        return current_user

    return dependency


def require_admin_user(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.VIEW_ADMIN_DASHBOARD)(current_user=current_user, db=db)


def require_animal_management_permission(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.MANAGE_ANIMALS)(current_user=current_user, db=db)


def require_animal_catalog_permission(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.MANAGE_ANIMAL_CATALOG)(current_user=current_user, db=db)


def require_animals_create_permission(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.ANIMALS_CREATE_ANIMALS)(current_user=current_user, db=db)


def require_species_create_permission(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.ANIMALS_CREATE_SPECIES)(current_user=current_user, db=db)


def require_habitats_create_permission(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.ANIMALS_CREATE_HABITATS)(current_user=current_user, db=db)


def require_task_management_permission(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.MANAGE_TASKS)(current_user=current_user, db=db)


def require_task_config_permission(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.TASKS_TYPES_CONFIG)(current_user=current_user, db=db)


def require_task_planner_permission(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.TASKS_ROUTINES_PLANNER)(current_user=current_user, db=db)


def require_task_operations_permission(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.TASKS_OPERATIONS_BOARD)(current_user=current_user, db=db)


def require_inventory_read_permission(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.VIEW_INVENTORY)(current_user=current_user, db=db)


def require_inventory_manage_permission(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.MANAGE_INVENTORY)(current_user=current_user, db=db)


def require_inventory_create_product_permission(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.INVENTORY_CREATE_PRODUCT)(current_user=current_user, db=db)


def require_inventory_create_supplier_permission(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.INVENTORY_CREATE_SUPPLIER)(current_user=current_user, db=db)


def require_inventory_movements_permission(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.INVENTORY_MOVEMENTS_HISTORY)(current_user=current_user, db=db)


def require_veterinario(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return require_permission(PermissionCode.MANAGE_VETERINARY_MODULE)(current_user=current_user, db=db)
