import logging
from datetime import datetime, timedelta, timezone
import secrets
from sqlalchemy.orm import Session, Query, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from starlette import status
from typing import List, Optional
import secrets
import string
import re
import unicodedata

logger = logging.getLogger(__name__)

from app.models.user import User
from app.models.role import Role
from app.models.password_history import PasswordHistory
from app.schemas.user import (
    UserCreate,
    AdminUserCreate,
    AdminUserUpdate,
    UserUpdateProfile,
)
from app.core.security import get_password_hash, verify_password
from app.core.password_policy import validate_password_strength_func
from app.core.enums import UserRole
from app.core.config import settings

def _get_visitante_role_id(db: Session) -> int:

    role = db.query(Role).filter(Role.name == UserRole.VISITANTE.value).first()
    if not role:
        raise RuntimeError(
            f"Rol por defecto '{UserRole.VISITANTE.value}' no encontrado en la base de datos"
        )
    return role.id


def normalize_user_id(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = re.sub(r"[^a-z0-9]+", ".", ascii_value).strip(".")
    ascii_value = re.sub(r"\.+", ".", ascii_value)
    parts = ascii_value.split(".")
    if len(parts) == 3:
        role_aliases = {
            "administrador": "admin",
            "administrator": "admin",
            "admin": "admin",
            "cuidador": "cuidador",
            "caregiver": "cuidador",
            "veterinario": "vet",
            "veterinaria": "vet",
            "veterinary": "vet",
            "vet": "vet",
            "visitante": "visitante",
            "visitor": "visitante",
            "osi": "osi",
        }
        parts[1] = role_aliases.get(parts[1], parts[1])
        ascii_value = ".".join(parts)
    return ascii_value


def get_user(db: Session, user_id: str) -> Optional[User]:
    """
    Obtiene un usuario por su ID
    """
    return (
        db.query(User).options(joinedload(User.role)).filter(User.id == user_id).first()
    )


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Busca un usuario por su email, aplicando la misma normalizacion
    """
    normalized_email = email.strip().lower()
    return (
        db.query(User)
        .options(joinedload(User.role))
        .filter(User.email == normalized_email)
        .first()
    )


def get_user_by_phone(db: Session, phone_number: str) -> User | None:
    return (
        db.query(User)
        .options(joinedload(User.role))
        .filter(User.phone_number == phone_number.strip())
        .first()
    )


def get_user_by_identifier(db: Session, identifier: str) -> User | None:
    normalized_identifier = identifier.strip().lower()
    query = db.query(User).options(joinedload(User.role))
    if normalized_identifier.startswith("+"):
        return query.filter(User.phone_number == normalized_identifier).first()
    return query.filter(
        (User.id == normalized_identifier)
        | (User.username == normalized_identifier)
        | (User.phone_number == normalized_identifier)
        | (User.email == normalized_identifier)
    ).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    """
    Busca un usuario por su nombre de usuario.
    """
    return (
        db.query(User)
        .options(joinedload(User.role))
        .filter(User.username == username)
        .first()
    )


def get_users_query(
    db: Session,
    role_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "id",
    sort_type: Optional[str] = "desc",
) -> Query:
    query = db.query(User).options(joinedload(User.role))

    if role_id is not None:
        query = query.filter(User.role_id == role_id)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    # Ordenamiento seguro (evitar inyección SQL)
    valid_sort_fields = {
        "id": User.id,
        "email": User.email,
        "username": User.username,
        "created_at": User.created_at,
        "is_active": User.is_active,
    }

    sort_field = valid_sort_fields.get(sort_by, User.id)
    if (sort_type or "desc").lower() == "asc":
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())

    return query

def create_public_user(db: Session, user_in: UserCreate) -> User:
    hashed_password = get_password_hash(user_in.password)
    role_id = _get_visitante_role_id(db)
    
    # Generar código de 6 dígitos
    user_id = normalize_user_id(user_in.username)

    user = User(
        id=user_id,
        email=user_in.email,
        username=user_id,
        phone_number=user_in.phone_number,
        hashed_password=hashed_password,
        is_active=False,
        email_verified=False,
        phone_verified=False,
        role_id=role_id,
        must_change_password=False,
        password_changed_at=datetime.now(timezone.utc),
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.exception("Error de integridad creando usuario")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email o nombre de usuario ya existen",
        )
    db.refresh(user)
    return user


def create_user_by_admin(db: Session, user_in: AdminUserCreate) -> User:
    hashed_password = get_password_hash(user_in.password)
    user_id = normalize_user_id(user_in.username)

    user = User(
        id=user_id,
        email=user_in.email,
        username=user_id,
        phone_number=user_in.phone_number,
        hashed_password=hashed_password,
        is_active=user_in.is_active,
        email_verified=True,
        phone_verified=True,
        role_id=user_in.role_id,
        must_change_password=True,
        password_changed_at=datetime.now(timezone.utc),
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.exception("Error de integridad creando usuario por admin")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email o nombre de usuario ya existen",
        )
    db.refresh(user)
    return user


def update_user_by_admin(
    db: Session, db_user_to_update: User, user_in: AdminUserUpdate
) -> User:
    update_data = user_in.model_dump(exclude_unset=True)
    if "username" in update_data and update_data["username"]:
        update_data["username"] = normalize_user_id(update_data["username"])
    for field, value in update_data.items():
        setattr(db_user_to_update, field, value)

    db.add(db_user_to_update)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.exception("Conflicto de integridad actualizando usuario por admin")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Conflicto de datos"
        )
    db.refresh(db_user_to_update)
    return db_user_to_update


def delete_user_by_admin(db: Session, user_id_to_delete: str) -> Optional[User]:
    db_user = db.query(User).filter(User.id == user_id_to_delete).first()
    if not db_user:
        return None

    db.delete(db_user)
    db.commit()
    return db_user


def update_own_profile(
    db: Session, db_user_to_update: User, user_in: UserUpdateProfile
) -> User:
    update_data = user_in.model_dump(exclude_unset=True)

    password_raw = update_data.pop("password", None)
    if password_raw is not None:
        validate_password_strength_func(password_raw)
        if is_password_in_history(db, db_user_to_update, password_raw):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes reutilizar una contraseña que ya has usado anteriormente",
            )
        _save_password_to_history(db, db_user_to_update, db_user_to_update.hashed_password)
        _enforce_password_history_limit(db, db_user_to_update)
        db_user_to_update.hashed_password = get_password_hash(password_raw)
        db_user_to_update.password_changed_at = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(db_user_to_update, field, value)

    db.add(db_user_to_update)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.exception("Conflicto de integridad actualizando perfil propio")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Conflicto de datos"
        )
    db.refresh(db_user_to_update)
    return db_user_to_update


def update_password(db: Session, db_user: User, new_password: str) -> User:
    # Guardar en histórico antes de actualizar
    _save_password_to_history(db, db_user, db_user.hashed_password)

    # Verificar límite de histórico según rol
    _enforce_password_history_limit(db, db_user)

    db_user.hashed_password = get_password_hash(new_password)
    db_user.password_changed_at = datetime.now(timezone.utc)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_user_email(db: Session, email: str, code: str) -> bool:
    """
    Verifica el código y activa al usuario.
    """
    user = get_user_by_email(db, email=email)
    if not user:
        return False

    if user.verification_code == code:
        user.email_verified = True
        user.is_active = True
        user.verification_code = None  # Limpiar código tras éxito
        db.add(user)
        db.commit()
        return True

    return False


def request_phone_update(db: Session, user: User, new_phone: str) -> str:
    """
    Actualiza temporalmente el número de teléfono y genera un código de verificación.
    """
    user.phone_number = new_phone
    user.phone_verified = False
    
    # Generar y retornar el nuevo código
    code = create_sms_otp(db, user, "verify_phone")
    db.commit()
    db.refresh(user)
    return code


def create_sms_otp(db: Session, user: User, purpose: str) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    user.sms_otp_code = code
    user.sms_otp_purpose = purpose
    user.sms_otp_expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.SMS_OTP_EXPIRE_MINUTES
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return code


def verify_sms_otp(db: Session, user: User, code: str, purpose: str) -> bool:
    now = datetime.now(timezone.utc)
    expires_at = user.sms_otp_expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    is_valid = (
        user.sms_otp_code == code
        and user.sms_otp_purpose == purpose
        and expires_at is not None
        and expires_at >= now
    )
    if not is_valid:
        return False

    user.sms_otp_code = None
    user.sms_otp_purpose = None
    user.sms_otp_expires_at = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return True


def mark_phone_verified(db: Session, phone_number: str) -> bool:
    user = get_user_by_phone(db, phone_number=phone_number)
    if not user:
        return False

    user.phone_verified = True
    user.email_verified = True
    user.is_active = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return True


def resend_verification_code(db: Session, email: str) -> Optional[User]:
    """
    Genera un nuevo código de verificación para un usuario no verificado.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    user = get_user_by_email(db, email=email)
    if not user:
        logger.warning(f"Intento de reenvío para email no encontrado: {email}")
        return None
        
    if user.email_verified:
        logger.info(f"Intento de reenvío para email ya verificado: {email}")
        return None

    # Generar nuevo código de 6 dígitos
    new_code = ''.join(secrets.choice(string.digits) for _ in range(6))
    user.verification_code = new_code
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"NUEVO CODIGO GENERADO para {email}: {new_code}")
    return user

def _save_password_to_history(db: Session, user: User, password_hash: str) -> None:
    """Guarda el hash de la contraseña actual en el histórico."""
    history_entry = PasswordHistory(user_id=user.id, password_hash=password_hash)
    db.add(history_entry)
    db.commit()


def _enforce_password_history_limit(db: Session, user: User) -> None:
    """Elimina entradas antiguas del histórico si se excede el límite del rol."""
    if not user.role:
        return

    role_name = user.role.name
    limit = _get_password_history_limit(role_name)

    if limit <= 0:
        return

    # Obtener registros ordenados por fecha (más reciente primero)
    history_records = (
        db.query(PasswordHistory)
        .filter(PasswordHistory.user_id == user.id)
        .order_by(PasswordHistory.created_at.desc())
        .all()
    )

    # Si excedemos el límite, eliminar los más antiguos
    if len(history_records) > limit:
        records_to_delete = history_records[limit:]
        for record in records_to_delete:
            db.delete(record)
        db.commit()


def _get_password_history_limit(role_name: str) -> int:
    role_limits = {
        "administrador": settings.PASSWORD_HISTORY_ADMIN_MAX,
        "osi": settings.PASSWORD_HISTORY_ESPECIALISTA_MAX,
        "veterinario": settings.PASSWORD_HISTORY_ESPECIALISTA_MAX,
        "cuidador": settings.PASSWORD_HISTORY_ESPECIALISTA_MAX,
        "visitante": settings.PASSWORD_HISTORY_PACIENTE_MAX,
    }
    return role_limits.get(role_name, settings.PASSWORD_HISTORY_USUARIO_BASICO_MAX)


def _get_password_validity_days(role_name: str) -> int:
    role_validity = {
        "administrador": settings.PASSWORD_VALIDITY_ADMIN_DAYS,
        "osi": settings.PASSWORD_VALIDITY_ESPECIALISTA_DAYS,
        "veterinario": settings.PASSWORD_VALIDITY_ESPECIALISTA_DAYS,
        "cuidador": settings.PASSWORD_VALIDITY_ESPECIALISTA_DAYS,
        "visitante": settings.PASSWORD_VALIDITY_PACIENTE_DAYS,
    }
    return role_validity.get(role_name, settings.PASSWORD_VALIDITY_USUARIO_BASICO_DAYS)


def is_password_expired(user: User) -> bool:
    if user.password_changed_at is None:
        return False
    validity_days = _get_password_validity_days(user.role.name if user.role else "visitante")
    from datetime import timedelta
    expiry = user.password_changed_at + timedelta(days=validity_days)
    return expiry < datetime.now(timezone.utc)


def is_password_in_history(db: Session, user: User, new_password: str) -> bool:
    """Verifica si la nueva contraseña es la actual o ya estuvo en el histórico del rol."""
    if verify_password(new_password, user.hashed_password):
        return True

    role_name = user.role.name if user.role else "visitante"
    limit = _get_password_history_limit(role_name)

    history_records = (
        db.query(PasswordHistory)
        .filter(PasswordHistory.user_id == user.id)
        .order_by(PasswordHistory.created_at.desc())
        .limit(limit)
        .all()
    )

    for record in history_records:
        if verify_password(new_password, record.password_hash):
            return True
    return False


def get_password_history(db: Session, user_id: str, limit: int = 10) -> list:
    """Obtiene el histórico de contraseñas de un usuario."""
    return (
        db.query(PasswordHistory)
        .filter(PasswordHistory.user_id == user_id)
        .order_by(PasswordHistory.created_at.desc())
        .limit(limit)
        .all()
    )
