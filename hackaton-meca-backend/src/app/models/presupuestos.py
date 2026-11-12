from sqlalchemy import (
    Column, Integer, BigInteger, SmallInteger, String, Text, DateTime,
    Numeric, ForeignKey, func, UniqueConstraint, Index, ForeignKeyConstraint
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id = Column(BigInteger, primary_key=True, index=True)
    gestion_id = Column(Integer, ForeignKey("gestiones.id", ondelete="RESTRICT"), nullable=False, index=True)
    region_id = Column(Integer, ForeignKey("regiones.id", ondelete="RESTRICT"), nullable=False, index=True)
    area_id = Column(Integer, ForeignKey("areas.id", ondelete="RESTRICT"), nullable=False, index=True)
    financiador_id = Column(Integer, ForeignKey("financiadores.id", ondelete="RESTRICT"), nullable=False, index=True)
    rubro_id = Column(Integer, ForeignKey("rubros.id", ondelete="RESTRICT"), nullable=False, index=True)
    cuenta_id = Column(Integer, nullable=True, index=True)
    month = Column(SmallInteger, nullable=True)  # NULL = anual
    linea = Column(String(150), nullable=True)
    moneda = Column(String(3), default="BOB", nullable=False)
    monto_original = Column(Numeric(15, 2), nullable=False)
    amount_bob = Column(Numeric(15, 2), default=0.00, nullable=False)
    amount_usd = Column(Numeric(15, 2), default=0.00, nullable=True)
    tipos_cambio_id = Column(Integer, ForeignKey("tipos_cambio.id"), nullable=True)
    importacion_id = Column(Integer, ForeignKey("importaciones.id", ondelete="RESTRICT"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("id", "gestion_id", name="uq_pres_id_gestion"),
        ForeignKeyConstraint(
            ["cuenta_id", "rubro_id"],
            ["cuentas.id", "cuentas.rubro_id"],
            name="fk_pres_cuenta_rubro",
            ondelete="RESTRICT",
        ),
        Index("idx_presupuestos_query", "gestion_id", "region_id", "area_id", "financiador_id", "rubro_id", "cuenta_id"),
    )


class PresupuestoModificacion(Base):
    __tablename__ = "presupuesto_modificaciones"

    id = Column(BigInteger, primary_key=True, index=True)
    gestion_id = Column(Integer, ForeignKey("gestiones.id", ondelete="RESTRICT"), nullable=False, index=True)
    tipo = Column(String(20), nullable=False)  # 'ampliacion', 'reduccion', 'traspaso'
    origen_presupuesto_id = Column(BigInteger, ForeignKey("presupuestos.id", ondelete="RESTRICT"), nullable=True)
    destino_presupuesto_id = Column(BigInteger, ForeignKey("presupuestos.id", ondelete="RESTRICT"), nullable=True)
    amount_bob = Column(Numeric(15, 2), nullable=False)
    reason = Column(Text, nullable=False)
    estado = Column(String(15), default="borrador", nullable=False, index=True)  # 'borrador', 'aprobado', 'rechazado'
    solicitado_por = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    aprobado_por = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    aprobado_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    origen_presupuesto = relationship("Presupuesto", foreign_keys=[origen_presupuesto_id])
    destino_presupuesto = relationship("Presupuesto", foreign_keys=[destino_presupuesto_id])

    __table_args__ = (
        Index("idx_pm_gestion_estado", "gestion_id", "estado"),
    )


class ModificacionGasto(Base):
    __tablename__ = "modificaciones"

    id = Column(BigInteger, primary_key=True, index=True)
    gestion_id = Column(Integer, nullable=False, index=True)
    movimiento_id = Column(BigInteger, nullable=False, index=True)
    financiador_origen_id = Column(Integer, ForeignKey("financiadores.id", ondelete="RESTRICT"), nullable=False)
    financiador_destino_id = Column(Integer, ForeignKey("financiadores.id", ondelete="RESTRICT"), nullable=False)
    amount_bob = Column(Numeric(15, 2), nullable=False)
    reason = Column(Text, nullable=False)
    estado = Column(String(15), default="borrador", nullable=False, index=True)  # 'borrador', 'aprobado', 'rechazado'
    solicitado_por = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    aprobado_por = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    aprobado_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    movimiento = relationship("Movimiento", back_populates="modificaciones")
    financiador_origen = relationship("Financiador", foreign_keys=[financiador_origen_id])
    financiador_destino = relationship("Financiador", foreign_keys=[financiador_destino_id])

    __table_args__ = (
        ForeignKeyConstraint(
            ["movimiento_id", "gestion_id"],
            ["movimientos.id", "movimientos.gestion_id"],
            name="fk_mod_movimiento",
            ondelete="RESTRICT",
        ),
        Index("idx_modificaciones_mov", "movimiento_id", "estado"),
    )
