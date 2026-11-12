from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id = Column(
        Integer,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id = Column(
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True)
    code = Column(String(100), unique=True, nullable=False)
    module = Column(String(50), nullable=False)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, server_default=text("true"), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    roles = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, server_default=text("false"), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    users = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
    )
    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(150), nullable=False)
    full_name = Column(String(150), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, server_default=text("true"), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    failed_attempts = Column(
        SmallInteger,
        server_default=text("0"),
        nullable=False,
    )
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Excepciones de autenticación acordadas para el MVP.
    totp_secret = Column(Text, nullable=True)
    is_totp_enabled = Column(
        Boolean,
        server_default=text("false"),
        nullable=False,
    )
    totp_enabled_at = Column(DateTime(timezone=True), nullable=True)
    must_change_password = Column(
        Boolean,
        server_default=text("false"),
        nullable=False,
    )
    password_changed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    roles = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
    )
    data_scopes = relationship(
        "UserDataScope",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs = relationship("AuditLog", back_populates="user")
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    backup_codes = relationship(
        "TwoFactorBackupCode",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # SQL v2 protege el correo con un único funcional, no con un UNIQUE simple.
        Index("uq_users_email", func.lower(email), unique=True),
    )

    


class UserDataScope(Base):
    __tablename__ = "user_data_scopes"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    dimension_type = Column(String(30), nullable=False)
    dimension_id = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="data_scopes")

    __table_args__ = (
        CheckConstraint(
            "dimension_type IN ('region', 'area', 'financiador')",
            name="ck_user_scope_dimension",
        ),
        UniqueConstraint(
            "user_id",
            "dimension_type",
            "dimension_id",
            name="uq_user_scope",
        ),
        Index("idx_user_data_scopes", "user_id", "dimension_type"),
    )