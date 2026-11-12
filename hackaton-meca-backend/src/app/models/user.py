from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.db.base import Base
#Prueba
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.role import Role
from sqlalchemy.sql import select
from app.core.enums import UserRole
#prueba 2
from sqlalchemy.orm import validates
import re
#SQLaclchemy as ORM

class User(Base):
    __tablename__ = "users"

    id = Column(String(120), primary_key=True, index=True)
    #unique=True
    email = Column(String(200), unique=True, index=True, nullable=True)
    username = Column(String(120), unique=True, nullable=False)
    phone_number = Column(String(25), unique=True, index=True, nullable=True)
    phone_verified = Column(Boolean, default=False, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    verification_code = Column(String(10), nullable=True)
    sms_otp_code = Column(String(10), nullable=True)
    sms_otp_purpose = Column(String(32), nullable=True)
    sms_otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    photo_url = Column(String(2048), nullable=True) #estandar

    #2fa
    is_totp_enabled = Column(Boolean, default=False, nullable=False)
    totp_secret = Column(String(255), nullable=True)
    #redis
    locked_until = Column(DateTime(timezone=True), nullable=True)
    must_change_password = Column(Boolean, default=True, nullable=False)
    password_changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    role = relationship("Role", back_populates="users")
    user_permissions = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan")
    encuestas_creadas = relationship("Encuesta", back_populates="usuario_creador")
    participaciones_encuestas = relationship("ParticipacionEncuesta", back_populates="usuario")
    trivias_creadas = relationship("Trivia", back_populates="usuario")
    participaciones_trivia = relationship("ParticipacionTrivia", back_populates="usuario")   
    favorited_by_users = relationship("AnimalFavorito", back_populates="usuario", cascade="all, delete-orphan")
    
    #codigos usuario
    backup_codes = relationship("TwoFactorCodes", back_populates="user", cascade="all, delete-orphan")
    #inventario
    entradas_inventario = relationship("EntradaInventario", back_populates="usuario")
    salidas_inventario = relationship("Salida", back_populates="usuario")
    #tareas
    tareas_asignadas = relationship("Tarea", back_populates="usuario_asignado", foreign_keys="[Tarea.usuario_asignado_id]")
    tareas_recurrentes_asignadas = relationship("TareaRecurrente", back_populates="usuario_asignado", foreign_keys="[TareaRecurrente.usuario_asignado_id]")
    registros_alimentacion = relationship("RegistroAlimentacion", back_populates="usuario")
    #veterinario
    historiales_creados = relationship("HistorialMedico", back_populates="veterinario")
    recetas_asignadas = relationship("RecetaMedica", back_populates="usuario_asignado")
    onboarding_tours = relationship("OnboardingTourProgress", back_populates="user", cascade="all, delete-orphan")
    #Pruebas
    #propeidades hibridas
    @hybrid_property
    def is_admin(self):

        return self.role.name == UserRole.ADMINISTRADOR.value

    @is_admin.expression
    def is_admin(cls):
        # subconsulta que revisa el nombre del rol
        return (
            select([Role.name])
            .where(Role.id == cls.role_id)
            .as_scalar()
        ) == UserRole.ADMINISTRADOR.value
    
    #validacion
    @validates('email')
    def validate_and_normalize_email(self, key, email_address):
        if not email_address:
            return None
              
        normalized_email = email_address.lower().strip()

        if '@' not in normalized_email or '.' not in normalized_email.split('@')[-1]:
             raise ValueError(f"Email no valido: '{email_address}'")
        return normalized_email

    @validates('username')
    def validate_and_normalize_username(self, key, username):
        if not username:
            raise ValueError("El nombre de usuario no puede estar vacio")

        normalized_username = username.strip().lower()
        if not re.match(r"^[a-z0-9]+\.(admin|cuidador|vet|visitante|osi)\.[a-z0-9]+$", normalized_username):
             raise ValueError("El ID de usuario debe usar el formato nombre.rol.apellido")

        return normalized_username
