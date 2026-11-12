from enum import Enum


class RoleName(str, Enum):
    ADMINISTRADOR = "Administrador"
    DIRECTIVO = "Directivo"
    CONTADOR = "Contador"
    TECNICO = "Tecnico"
    AUDITOR = "Auditor"


class PermissionCode(str, Enum):
    DASHBOARD_VER = "dashboard.ver"
    REPORTES_VER = "reportes.ver"
    REPORTES_EXPORTAR = "reportes.exportar"
    REPORTES_PROGRAMAR = "reportes.programar"
    IMPORTACIONES_VER = "importaciones.ver"
    IMPORTACIONES_CREAR = "importaciones.crear"
    IMPORTACIONES_CONFIRMAR = "importaciones.confirmar"
    IMPORTACIONES_REVERTIR = "importaciones.revertir"
    PRESUPUESTOS_VER = "presupuestos.ver"
    PRESUPUESTOS_EDITAR = "presupuestos.editar"
    MODIFICACIONES_SOLICITAR = "modificaciones.solicitar"
    MODIFICACIONES_APROBAR = "modificaciones.aprobar"
    CATALOGOS_EDITAR = "catalogos.editar"
    GESTIONES_CERRAR = "gestiones.cerrar"
    USUARIOS_ADMIN = "usuarios.admin"
    ROLES_ADMIN = "roles.admin"
    AUDITORIA_VER = "auditoria.ver"


class AuditAction(str, Enum):
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGIN_2FA_REQUIRED = "auth.login.2fa.required"
    LOGIN_CHANGE_PASSWORD_REQUIRED = "auth.login.change_password_required"
    LOGIN_2FA_SUCCESS = "auth.login.2fa.success"
    LOGIN_2FA_FAILURE = "auth.login.2fa.failure"
    LOGOUT = "auth.logout"
    LOGOUT_ALL = "auth.logout_all"
    TOKEN_REFRESH = "auth.token.refresh"
    PASSWORD_CHANGE = "auth.password.change"
    PASSWORD_RESET_REQUEST = "auth.password.reset.request"
    PASSWORD_RESET = "auth.password.reset"
    TOTP_SETUP = "auth.2fa.setup"
    TOTP_ENABLE = "auth.2fa.enable"
    TOTP_DISABLE = "auth.2fa.disable"
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DEACTIVATE = "user.deactivate"
    USER_SCOPES_UPDATE = "user.scopes.update"
    ROLE_CREATE = "role.create"
    ROLE_UPDATE = "role.update"
    ROLE_DELETE = "role.delete"
    ROLE_PERMISSIONS_UPDATE = "role.permissions.update"
    PERMISSION_CREATE = "permission.create"
    PERMISSION_UPDATE = "permission.update"
    PERMISSION_DELETE = "permission.delete"


class AuditEntity(str, Enum):
    AUTH = "auth"
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    SYSTEM = "system"


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    PRE_2FA = "pre_2fa"
    CHANGE_PASSWORD = "change_password"