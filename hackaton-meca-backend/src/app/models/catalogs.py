from sqlalchemy import (
    CHAR,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Region(Base):
    __tablename__ = "regiones"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Area(Base):
    __tablename__ = "areas"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Rubro(Base):
    __tablename__ = "rubros"

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    cuentas = relationship("Cuenta", back_populates="rubro")


class Cuenta(Base):
    __tablename__ = "cuentas"

    id = Column(Integer, primary_key=True)
    rubro_id = Column(
        Integer,
        ForeignKey("rubros.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code = Column(String(50), nullable=False)
    name = Column(String(150), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    rubro = relationship("Rubro", back_populates="cuentas")

    __table_args__ = (
        UniqueConstraint("rubro_id", "code", name="uq_cuenta_rubro_code"),
        UniqueConstraint("id", "rubro_id", name="uq_cuenta_id_rubro"),
    )


class FinanciadorGrupo(Base):
    __tablename__ = "financiador_grupos"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    financiadores = relationship("Financiador", back_populates="grupo")


class Financiador(Base):
    __tablename__ = "financiadores"

    id = Column(Integer, primary_key=True)
    grupo_id = Column(
        Integer,
        ForeignKey("financiador_grupos.id", ondelete="SET NULL"),
        nullable=True,
    )
    code = Column(String(50), nullable=True)
    name = Column(String(120), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    moneda = Column(
        CHAR(3),
        server_default=text("'BOB'"),
        nullable=False,
    )
    vigencia_inicio = Column(Date, nullable=True)
    vigencia_fin = Column(Date, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    grupo = relationship("FinanciadorGrupo", back_populates="financiadores")

    __table_args__ = (
        CheckConstraint(
            "moneda IN ('BOB', 'USD')",
            name="ck_financiador_moneda",
        ),
        CheckConstraint(
            "vigencia_fin IS NULL OR vigencia_inicio IS NULL "
            "OR vigencia_fin >= vigencia_inicio",
            name="ck_financiador_vigencia",
        ),
    )


class Gestion(Base):
    __tablename__ = "gestiones"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, unique=True, nullable=False)
    is_closed = Column(Boolean, server_default=text("false"), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    description = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "year BETWEEN 2000 AND 2100",
            name="ck_gestion_year",
        ),
    )


class TipoCambio(Base):
    __tablename__ = "tipos_cambio"

    id = Column(Integer, primary_key=True)
    fecha = Column(Date, nullable=False)
    tipo = Column(
        String(15),
        server_default=text("'oficial'"),
        nullable=False,
    )
    rate = Column(Numeric(12, 4), nullable=False)

    __table_args__ = (
        CheckConstraint("rate > 0", name="ck_tipo_cambio_rate"),
        UniqueConstraint("fecha", "tipo", name="uq_tipo_cambio"),
    )