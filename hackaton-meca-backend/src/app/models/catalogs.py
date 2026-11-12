from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, Numeric, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class Region(Base):
    __tablename__ = "regiones"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Area(Base):
    __tablename__ = "areas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Rubro(Base):
    __tablename__ = "rubros"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cuentas = relationship("Cuenta", back_populates="rubro")


class Cuenta(Base):
    __tablename__ = "cuentas"

    id = Column(Integer, primary_key=True, index=True)
    rubro_id = Column(Integer, ForeignKey("rubros.id", ondelete="RESTRICT"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(150), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    rubro = relationship("Rubro", back_populates="cuentas")

    __table_args__ = (
        UniqueConstraint("rubro_id", "code", name="uq_cuenta_rubro_code"),
        UniqueConstraint("id", "rubro_id", name="uq_cuenta_id_rubro"),
    )


class FinanciadorGrupo(Base):
    __tablename__ = "financiador_grupos"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    financiadores = relationship("Financiador", back_populates="grupo")


class Financiador(Base):
    __tablename__ = "financiadores"

    id = Column(Integer, primary_key=True, index=True)
    grupo_id = Column(Integer, ForeignKey("financiador_grupos.id", ondelete="SET NULL"), nullable=True, index=True)
    code = Column(String(50), nullable=True)
    name = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    moneda = Column(String(3), default="BOB", nullable=False)  # 'BOB', 'USD'
    vigencia_inicio = Column(Date, nullable=True)
    vigencia_fin = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    grupo = relationship("FinanciadorGrupo", back_populates="financiadores")


class Gestion(Base):
    __tablename__ = "gestiones"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, unique=True, nullable=False, index=True)
    is_closed = Column(Boolean, default=False, nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    description = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TipoCambio(Base):
    __tablename__ = "tipos_cambio"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    tipo = Column(String(15), default="oficial", nullable=False)
    rate = Column(Numeric(12, 4), nullable=False)

    __table_args__ = (
        UniqueConstraint("fecha", "tipo", name="uq_tipo_cambio"),
    )
