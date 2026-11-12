"""Script to seed complete RBAC roles, permissions, and demo users for MECA."""

import logging
from sqlalchemy import select
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.catalogs import Financiador, Region
from app.models.security import Permission, Role, RolePermission, User, UserDataScope, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALL_PERMISSIONS = [
    ("dashboard.ver", "dashboard", "Ver Dashboard", "Visualización del dashboard ejecutivo y métricas"),
    ("reportes.ver", "reportes", "Ver Reportes", "Acceso a consultas de reportes financieros"),
    ("reportes.exportar", "reportes", "Exportar Reportes", "Descarga de reportes en Excel y PDF"),
    ("reportes.programar", "reportes", "Programar Reportes", "Configuración de envíos periódicos de reportes"),
    ("importaciones.ver", "importaciones", "Ver Importaciones", "Consulta de historial de lotes importados"),
    ("importaciones.crear", "importaciones", "Cargar Archivo", "Carga y validación previa de archivos contables"),
    ("importaciones.confirmar", "importaciones", "Confirmar Lote", "Impacto definitivo del lote en ejecución"),
    ("importaciones.revertir", "importaciones", "Revertir Lote", "Eliminación segura y reversión de lote"),
    ("presupuestos.ver", "presupuestos", "Ver Presupuestos", "Consulta de techos presupuestarios"),
    ("presupuestos.editar", "presupuestos", "Editar Presupuestos", "Formulación y ajuste de techos presupuestarios"),
    ("modificaciones.solicitar", "presupuestos", "Solicitar Modificación", "Creación de solicitudes de traspaso intra/inter"),
    ("modificaciones.aprobar", "presupuestos", "Aprobar Modificación", "Resolución y aprobación de traspasos"),
    ("catalogos.editar", "catalogos", "Gestionar Catálogos", "Edición de cuentas, financiadores y centros de costo"),
    ("gestiones.cerrar", "catalogos", "Cierre de Gestión", "Operación de cierre fiscal y bloqueo de movimientos"),
    ("usuarios.admin", "seguridad", "Administrar Usuarios", "Creación, edición y asignación de alcances a usuarios"),
    ("roles.admin", "seguridad", "Administrar Roles", "Gestión de la matriz de roles y permisos"),
    ("auditoria.ver", "auditoria", "Ver Auditoría", "Inspección de logs inmutables y cadena criptográfica"),
]

ROLES_PERMISSIONS = {
    "Administrador": [code for code, _, _, _ in ALL_PERMISSIONS],
    "Finanzas": [
        "dashboard.ver", "reportes.ver", "reportes.exportar",
        "importaciones.ver", "importaciones.crear", "importaciones.confirmar", "importaciones.revertir",
        "presupuestos.ver", "presupuestos.editar", "modificaciones.solicitar", "catalogos.editar"
    ],
    "Coordinador": [
        "dashboard.ver", "reportes.ver", "reportes.exportar",
        "presupuestos.ver", "modificaciones.solicitar"
    ],
    "Auditor": [
        "dashboard.ver", "reportes.ver", "reportes.exportar",
        "importaciones.ver", "presupuestos.ver", "auditoria.ver"
    ],
}


def seed():
    db = SessionLocal()
    try:
        # 1. Permisos
        perm_map = {}
        for code, module, name, desc in ALL_PERMISSIONS:
            p = db.execute(select(Permission).where(Permission.code == code)).scalar_one_or_none()
            if not p:
                p = Permission(code=code, module=module, name=name, description=desc, is_active=True)
                db.add(p)
                db.commit()
                db.refresh(p)
            perm_map[code] = p

        # 2. Roles
        role_map = {}
        for role_name, perms in ROLES_PERMISSIONS.items():
            r = db.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
            if not r:
                r = Role(name=role_name, description=f"Rol institucional {role_name}", is_system=True)
                db.add(r)
                db.commit()
                db.refresh(r)
            role_map[role_name] = r

            # Vincular permisos al rol
            for p_code in perms:
                perm_obj = perm_map.get(p_code)
                if perm_obj:
                    link = db.execute(
                        select(RolePermission).where(
                            RolePermission.role_id == r.id,
                            RolePermission.permission_id == perm_obj.id,
                        )
                    ).scalar_one_or_none()
                    if not link:
                        db.add(RolePermission(role_id=r.id, permission_id=perm_obj.id))
            db.commit()

        # 3. Usuarios Institucionales
        pwd_hash = get_password_hash("AdminExB2026!")

        users_data = [
            ("admin@ensenaporbolivia.org", "Ana Morales (Director General)", "Administrador", "global", None),
            ("finanzas@ensenaporbolivia.org", "Carlos Rojas (Técnico Finanzas)", "Finanzas", "global", None),
            ("coord.scz@ensenaporbolivia.org", "Mariana Paz (Coord. Santa Cruz)", "Coordinador", "region", "SCZ"),
            ("santacruz@ensenaporbolivia.org", "Mariana Paz (Coord. Santa Cruz)", "Coordinador", "region", "SCZ"),
            ("auditor.catalyst@fundacion.org", "Roberto Silva (Auditor CATALYST)", "Auditor", "financiador", "CATALYST 18"),
            ("auditor@catalyst.org", "Roberto Silva (Auditor CATALYST)", "Auditor", "financiador", "CATALYST 18"),
        ]

        scz_region = db.execute(select(Region).where(Region.code == "SCZ")).scalar_one_or_none()
        catalyst_fin = db.execute(select(Financiador).where(Financiador.code == "CATALYST 18")).scalar_one_or_none()

        for email, full_name, r_name, scope_type, scope_target in users_data:
            u = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not u:
                u = User(
                    email=email,
                    full_name=full_name,
                    password_hash=pwd_hash,
                    is_active=True,
                    must_change_password=False,
                )
                db.add(u)
                db.commit()
                db.refresh(u)
            else:
                u.full_name = full_name
                u.password_hash = pwd_hash
                u.is_active = True
                u.must_change_password = False
                db.commit()

            # Asignar rol
            target_role = role_map[r_name]
            ur = db.execute(
                select(UserRole).where(UserRole.user_id == u.id, UserRole.role_id == target_role.id)
            ).scalar_one_or_none()
            if not ur:
                db.add(UserRole(user_id=u.id, role_id=target_role.id))
                db.commit()

            # Asignar scope de datos
            if scope_type == "region" and scz_region:
                existing_scope = db.execute(
                    select(UserDataScope).where(
                        UserDataScope.user_id == u.id,
                        UserDataScope.dimension_type == "region",
                        UserDataScope.dimension_id == scz_region.id,
                    )
                ).scalar_one_or_none()
                if not existing_scope:
                    db.add(UserDataScope(user_id=u.id, dimension_type="region", dimension_id=scz_region.id))
                    db.commit()

            elif scope_type == "financiador" and catalyst_fin:
                existing_scope = db.execute(
                    select(UserDataScope).where(
                        UserDataScope.user_id == u.id,
                        UserDataScope.dimension_type == "financiador",
                        UserDataScope.dimension_id == catalyst_fin.id,
                    )
                ).scalar_one_or_none()
                if not existing_scope:
                    db.add(UserDataScope(user_id=u.id, dimension_type="financiador", dimension_id=catalyst_fin.id))
                    db.commit()

        logger.info("Usuarios RBAC y alcances institucionales sembrados exitosamente.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
