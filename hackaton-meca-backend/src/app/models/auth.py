from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class RefreshToken(Base):
    """Token de refresco persistido para permitir revocación real."""

    __tablename__ = "refresh_tokens"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    jti = Column(String(128), unique=True, nullable=False)
    revoked = Column(Boolean, server_default=text("false"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    device_info = Column(String(300), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("idx_refresh_tokens_user", "user_id", "revoked"),
    )


class PasswordResetToken(Base):
    """Token de recuperación de contraseña; se guarda hasheado."""

    __tablename__ = "password_reset_tokens"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash = Column(String(64), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="password_reset_tokens")

    __table_args__ = (
        Index("idx_password_reset_tokens_user", "user_id"),
    )


class TwoFactorBackupCode(Base):
    """Códigos de respaldo de un solo uso para 2FA TOTP."""

    __tablename__ = "two_factor_backup_codes"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    code_hash = Column(String(255), nullable=False)
    is_used = Column(Boolean, server_default=text("false"), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="backup_codes")

    __table_args__ = (
        Index("idx_2fa_backup_user", "user_id", "is_used"),
    )