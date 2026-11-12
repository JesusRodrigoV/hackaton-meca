from __future__ import annotations

from typing import Dict, Iterable, List

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.enums import PermissionCode
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_permission import UserPermission


DEFAULT_PERMISSIONS = [
    {"code": PermissionCode.MANAGE_USERS.value, "name": "Gestionar usuarios", "description": "Crear, editar y desactivar usuarios del sistema.", "module": "admin"},
    {"code": PermissionCode.MANAGE_PERMISSIONS.value, "name": "Gestionar permisos", "description": "Asignar permisos funcionales por rol.", "module": "admin"},
    {"code": PermissionCode.VIEW_AUDIT_LOGS.value, "name": "Ver auditoría", "description": "Consultar los registros de auditoría del sistema.", "module": "admin"},
    {"code": PermissionCode.VIEW_ADMIN_DASHBOARD.value, "name": "Ver panel administrativo", "description": "Acceso al panel principal de administración.", "module": "admin"},
    {"code": PermissionCode.MANAGE_ANIMALS.value, "name": "Gestionar animales", "description": "Crear y editar animales y su información operativa.", "module": "animales"},
    {"code": PermissionCode.MANAGE_ANIMAL_CATALOG.value, "name": "Gestionar catálogo animal", "description": "Administrar especies, hábitats y archivos de catálogo.", "module": "animales"},
    {"code": PermissionCode.MANAGE_VETERINARY_MODULE.value, "name": "Gestionar módulo veterinario", "description": "Acceso a historiales, recetas y procedimientos veterinarios.", "module": "veterinario"},
    {"code": PermissionCode.MANAGE_TASKS.value, "name": "Gestionar tareas", "description": "Crear, asignar y administrar tareas operativas.", "module": "tareas"},
    {"code": PermissionCode.VIEW_INVENTORY.value, "name": "Ver inventario", "description": "Consultar inventario y reportes asociados.", "module": "inventario"},
    {"code": PermissionCode.MANAGE_INVENTORY.value, "name": "Gestionar inventario", "description": "Crear, editar y eliminar recursos del inventario.", "module": "inventario"},
    {"code": PermissionCode.MANAGE_SURVEYS.value, "name": "Gestionar encuestas", "description": "Crear y administrar encuestas y preguntas.", "module": "encuestas"},
    {"code": PermissionCode.ACCESS_ANIMALS_MANAGEMENT.value, "name": "Gestión de Animales", "description": "Habilita el grupo de gestión de animales en el menú.", "module": "animales"},
    {"code": PermissionCode.ANIMALS_LIST_SPECIES.value, "name": "Lista de Especies", "description": "Acceso a la lista de especies.", "module": "animales"},
    {"code": PermissionCode.ANIMALS_CREATE_SPECIES.value, "name": "Añadir Especie", "description": "Acceso al formulario de creación de especies.", "module": "animales"},
    {"code": PermissionCode.ANIMALS_LIST_HABITATS.value, "name": "Lista de Hábitats", "description": "Acceso a la lista de hábitats.", "module": "animales"},
    {"code": PermissionCode.ANIMALS_CREATE_HABITATS.value, "name": "Añadir Hábitat", "description": "Acceso al formulario de creación de hábitats.", "module": "animales"},
    {"code": PermissionCode.ANIMALS_LIST_ANIMALS.value, "name": "Lista de Animales", "description": "Acceso a la lista de animales.", "module": "animales"},
    {"code": PermissionCode.ANIMALS_CREATE_ANIMALS.value, "name": "Añadir Animal", "description": "Acceso al formulario de creación de animales.", "module": "animales"},
    {"code": PermissionCode.ACCESS_TASKS_MANAGEMENT.value, "name": "Gestión de Tareas", "description": "Habilita el grupo de gestión de tareas en el menú.", "module": "tareas"},
    {"code": PermissionCode.TASKS_OPERATIONS_BOARD.value, "name": "Tablero de Operaciones", "description": "Acceso al tablero de operaciones.", "module": "tareas"},
    {"code": PermissionCode.TASKS_ROUTINES_PLANNER.value, "name": "Planificador de Rutinas", "description": "Acceso al planificador de rutinas.", "module": "tareas"},
    {"code": PermissionCode.TASKS_TYPES_CONFIG.value, "name": "Configuración Tipos", "description": "Acceso a la configuración de tipos de tareas.", "module": "tareas"},
    {"code": PermissionCode.ACCESS_INVENTORY_MANAGEMENT.value, "name": "Gestión de Inventario", "description": "Habilita el grupo de gestión de inventario en el menú.", "module": "inventario"},
    {"code": PermissionCode.INVENTORY_CREATE_PRODUCT.value, "name": "Crear producto", "description": "Acceso al formulario de creación de productos.", "module": "inventario"},
    {"code": PermissionCode.INVENTORY_LIST_PRODUCTS.value, "name": "Lista de Productos", "description": "Acceso a la lista de productos.", "module": "inventario"},
    {"code": PermissionCode.INVENTORY_CREATE_SUPPLIER.value, "name": "Crear proveedor", "description": "Acceso al formulario de creación de proveedores.", "module": "inventario"},
    {"code": PermissionCode.INVENTORY_LIST_SUPPLIERS.value, "name": "Lista de Proveedores", "description": "Acceso a la lista de proveedores.", "module": "inventario"},
    {"code": PermissionCode.INVENTORY_LIST_TYPES.value, "name": "Lista de tipos", "description": "Acceso a la lista de tipos de producto.", "module": "inventario"},
    {"code": PermissionCode.INVENTORY_LIST_UNITS.value, "name": "Lista de unidades", "description": "Acceso a la lista de unidades de medida.", "module": "inventario"},
    {"code": PermissionCode.INVENTORY_MOVEMENTS_HISTORY.value, "name": "Historial de movimientos", "description": "Acceso al historial de movimientos de inventario.", "module": "inventario"},
    {"code": PermissionCode.ACCESS_USERS_MANAGEMENT.value, "name": "Gestión de Usuarios", "description": "Habilita el grupo de gestión de usuarios en el menú.", "module": "admin"},
    {"code": PermissionCode.USERS_CREATE.value, "name": "Crear Usuario", "description": "Acceso al formulario de creación de usuarios.", "module": "admin"},
    {"code": PermissionCode.USERS_LIST.value, "name": "Lista de Usuarios", "description": "Acceso a la lista de usuarios.", "module": "admin"},
    {"code": PermissionCode.ACCESS_SURVEYS_MANAGEMENT.value, "name": "Gestión de Encuestas", "description": "Habilita el grupo de gestión de encuestas en el menú.", "module": "encuestas"},
    {"code": PermissionCode.SURVEYS_LIST.value, "name": "Lista", "description": "Acceso a la lista de encuestas.", "module": "encuestas"},
    {"code": PermissionCode.SURVEYS_CREATE.value, "name": "Crear Encuesta", "description": "Acceso al formulario de creación de encuestas.", "module": "encuestas"},
    {"code": PermissionCode.ACCESS_AUDIT_ASSISTANT.value, "name": "Auditoría", "description": "Habilita el grupo de auditoría en el menú.", "module": "admin"},
    {"code": PermissionCode.AUDIT_APPLICATION_LOGS.value, "name": "Log de Aplicación", "description": "Acceso a registros funcionales y operativos de la aplicación.", "module": "admin"},
    {"code": PermissionCode.AUDIT_SECURITY_LOGS.value, "name": "Log de Seguridad OSI", "description": "Acceso OSI a eventos de seguridad, autenticación y cambios de permisos.", "module": "admin"},
    {"code": PermissionCode.RISK_MATRIX_ACCESS.value, "name": "Matriz de Riesgos", "description": "Acceso OSI a la matriz de analisis de riesgos de seguridad de la informacion.", "module": "osi"},
    {"code": PermissionCode.CAREGIVER_MY_TASKS.value, "name": "Mis tareas (Cuidador)", "description": "Acceso a tareas asignadas del cuidador.", "module": "cuidador"},
    {"code": PermissionCode.MEDICAL_MY_TASKS.value, "name": "Mis Tareas (Médico)", "description": "Acceso a tareas asignadas del médico.", "module": "veterinario"},
    {"code": PermissionCode.MEDICAL_DIETS.value, "name": "Gestión de Dietas", "description": "Acceso a gestión de dietas.", "module": "veterinario"},
    {"code": PermissionCode.MEDICAL_CLINICAL_RECORDS.value, "name": "Historiales Clínicos", "description": "Acceso a historiales clínicos.", "module": "veterinario"},
]

DEPRECATED_PERMISSION_CODES = {
    PermissionCode.AUDIT_USER_LOGS.value,
}


def ensure_permissions_catalog(db: Session) -> List[Permission]:
    permissions: List[Permission] = []
    for permission_data in DEFAULT_PERMISSIONS:
        permission = db.query(Permission).filter(Permission.code == permission_data["code"]).first()
        if not permission:
            permission = Permission(**permission_data)
            db.add(permission)
            db.flush()
        else:
            permission.name = permission_data["name"]
            permission.description = permission_data["description"]
            permission.module = permission_data["module"]
            permission.is_active = True
        permissions.append(permission)

    if DEPRECATED_PERMISSION_CODES:
        (
            db.query(Permission)
            .filter(Permission.code.in_(DEPRECATED_PERMISSION_CODES))
            .update({"is_active": False}, synchronize_session=False)
        )
    db.commit()
    return permissions


def ensure_role_permissions(db: Session) -> None:
    permissions_by_code = {
        permission.code: permission
        for permission in db.query(Permission).filter(Permission.is_active.is_(True)).all()
    }
    role_by_name = {role.name: role for role in db.query(Role).all()}
    all_permission_codes = list(permissions_by_code.keys())

    role_permissions_map = {
        "administrador": all_permission_codes,
        "osi": [
            PermissionCode.MANAGE_USERS.value,
            PermissionCode.MANAGE_PERMISSIONS.value,
            PermissionCode.ACCESS_AUDIT_ASSISTANT.value,
            PermissionCode.AUDIT_SECURITY_LOGS.value,
            PermissionCode.RISK_MATRIX_ACCESS.value,
            PermissionCode.VIEW_AUDIT_LOGS.value,
            PermissionCode.VIEW_ADMIN_DASHBOARD.value,
        ],
        "veterinario": [
            PermissionCode.MANAGE_VETERINARY_MODULE.value,
            PermissionCode.MEDICAL_MY_TASKS.value,
            PermissionCode.MEDICAL_DIETS.value,
            PermissionCode.MEDICAL_CLINICAL_RECORDS.value,
        ],
        "cuidador": [
            PermissionCode.MANAGE_TASKS.value,
            PermissionCode.CAREGIVER_MY_TASKS.value,
        ],
        "visitante": [],
    }

    for role_name, permission_codes in role_permissions_map.items():
        role = role_by_name.get(role_name)
        if not role:
            continue
        for permission_code in permission_codes:
            permission = permissions_by_code.get(permission_code)
            if not permission:
                continue
            rp = db.query(RolePermission).filter(RolePermission.role_id == role.id, RolePermission.permission_id == permission.id).first()
            if rp:
                if not rp.allowed:
                    rp.allowed = True
            else:
                db.add(RolePermission(role_id=role.id, permission_id=permission.id, allowed=True))

    db.commit()


def list_permissions(db: Session) -> List[Permission]:
    return db.query(Permission).filter(Permission.is_active.is_(True)).order_by(Permission.module, Permission.name).all()


def _load_user_with_permissions(db: Session, user_id: str) -> User:
    user = (
        db.query(User)
        .options(
            joinedload(User.role).joinedload(Role.role_permissions).joinedload(RolePermission.permission),
            joinedload(User.user_permissions).joinedload(UserPermission.permission),
        )
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


def get_effective_permission_entries(db: Session, user_id: str) -> List[dict]:
    user = _load_user_with_permissions(db, user_id)
    entries: Dict[str, dict] = {}

    for role_permission in getattr(user.role, "role_permissions", []):
        permission = role_permission.permission
        if not permission or not permission.is_active:
            continue
        entries[permission.code] = {"permission": permission, "allowed": bool(role_permission.allowed), "source": "role"}

    for user_perm in getattr(user, "user_permissions", []):
        permission = user_perm.permission
        if not permission or not permission.is_active:
            continue
        entries[permission.code] = {"permission": permission, "allowed": bool(user_perm.allowed), "source": "user"}

    return list(entries.values())


def get_effective_permission_codes(db: Session, user_id: str) -> List[str]:
    return [entry["permission"].code for entry in get_effective_permission_entries(db, user_id) if entry["allowed"]]


def user_has_permissions(db: Session, user_id: str, required_permissions: Iterable[str]) -> bool:
    effective = set(get_effective_permission_codes(db, user_id))
    return all(permission in effective for permission in required_permissions)


def get_users_with_permissions_query(db: Session):
    return (
        db.query(User)
        .options(
            joinedload(User.role).joinedload(Role.role_permissions).joinedload(RolePermission.permission),
            joinedload(User.user_permissions).joinedload(UserPermission.permission),
        )
        .order_by(User.id)
    )


def replace_user_permissions(db: Session, user_id: str, permissions_payload: List[dict]) -> User:
    _load_user_with_permissions(db, user_id)

    db.query(UserPermission).filter(UserPermission.user_id == user_id).delete()

    permission_ids = [item["permission_id"] for item in permissions_payload]
    permissions_by_id = {permission.id: permission for permission in db.query(Permission).filter(Permission.id.in_(permission_ids)).all()}

    for item in permissions_payload:
        permission = permissions_by_id.get(item["permission_id"])
        if not permission:
            continue
        db.add(UserPermission(user_id=user_id, permission_id=permission.id, allowed=bool(item.get("allowed", False))))

    db.commit()
    return _load_user_with_permissions(db, user_id)
