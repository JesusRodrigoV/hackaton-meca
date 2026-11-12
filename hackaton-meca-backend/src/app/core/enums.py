from enum import Enum


class UserRole(str, Enum):
    ADMINISTRADOR = "administrador"
    OSI = "osi"
    VETERINARIO = "veterinario"
    CUIDADOR = "cuidador"
    VISITANTE = "visitante"


class PermissionCode(str, Enum):
    MANAGE_USERS = "manage_users"
    MANAGE_PERMISSIONS = "manage_permissions"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    VIEW_ADMIN_DASHBOARD = "view_admin_dashboard"
    MANAGE_ANIMALS = "manage_animals"
    MANAGE_ANIMAL_CATALOG = "manage_animal_catalog"
    MANAGE_VETERINARY_MODULE = "manage_veterinary_module"
    MANAGE_TASKS = "manage_tasks"
    VIEW_INVENTORY = "view_inventory"
    MANAGE_INVENTORY = "manage_inventory"
    MANAGE_SURVEYS = "manage_surveys"
    ACCESS_ANIMALS_MANAGEMENT = "access_animals_management"
    ANIMALS_LIST_SPECIES = "animals_list_species"
    ANIMALS_CREATE_SPECIES = "animals_create_species"
    ANIMALS_LIST_HABITATS = "animals_list_habitats"
    ANIMALS_CREATE_HABITATS = "animals_create_habitats"
    ANIMALS_LIST_ANIMALS = "animals_list_animals"
    ANIMALS_CREATE_ANIMALS = "animals_create_animals"
    ACCESS_TASKS_MANAGEMENT = "access_tasks_management"
    TASKS_OPERATIONS_BOARD = "tasks_operations_board"
    TASKS_ROUTINES_PLANNER = "tasks_routines_planner"
    TASKS_TYPES_CONFIG = "tasks_types_config"
    ACCESS_INVENTORY_MANAGEMENT = "access_inventory_management"
    INVENTORY_CREATE_PRODUCT = "inventory_create_product"
    INVENTORY_LIST_PRODUCTS = "inventory_list_products"
    INVENTORY_CREATE_SUPPLIER = "inventory_create_supplier"
    INVENTORY_LIST_SUPPLIERS = "inventory_list_suppliers"
    INVENTORY_LIST_TYPES = "inventory_list_types"
    INVENTORY_LIST_UNITS = "inventory_list_units"
    INVENTORY_MOVEMENTS_HISTORY = "inventory_movements_history"
    ACCESS_USERS_MANAGEMENT = "access_users_management"
    USERS_CREATE = "users_create"
    USERS_LIST = "users_list"
    ACCESS_SURVEYS_MANAGEMENT = "access_surveys_management"
    SURVEYS_LIST = "surveys_list"
    SURVEYS_CREATE = "surveys_create"
    ACCESS_AUDIT_ASSISTANT = "access_audit_assistant"
    AUDIT_APPLICATION_LOGS = "audit_application_logs"
    AUDIT_SECURITY_LOGS = "audit_security_logs"
    AUDIT_USER_LOGS = "audit_user_logs"
    RISK_MATRIX_ACCESS = "risk_matrix_access"
    CAREGIVER_MY_TASKS = "caregiver_my_tasks"
    MEDICAL_MY_TASKS = "medical_my_tasks"
    MEDICAL_DIETS = "medical_diets"
    MEDICAL_CLINICAL_RECORDS = "medical_clinical_records"


class AnimalState(str, Enum):
    SALUDABLE = "Saludable"
    EN_TRATAMIENTO = "En tratamiento"
    EN_CUARENTENA = "En cuarentena"
    TRASLADADO = "Trasladado"
    FALLECIDO = "Fallecido"


class AuditEvent(str, Enum):
    LOGIN_SUCCESS = "login_exitoso"
    LOGIN_FAILURE = "login_fallido"
    V2P_SUCCESS = "login_2fa_exitoso"
    PERMISSION_UPDATE = "permission_update"
    ROLE_CREATED = "role_created"
    ROLE_UPDATED = "role_updated"
    ROLE_DELETED = "role_deleted"
    ROLE_PERMISSIONS_UPDATED = "role_permissions_updated"


class AuditLogType(str, Enum):
    APPLICATION = "application"
    SECURITY = "security"
