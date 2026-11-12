from sqlalchemy import (
    Column, Integer, BigInteger, SmallInteger, String, Text, Boolean, Date, DateTime,
    Numeric, ForeignKey, func, UniqueConstraint, Index, ForeignKeyConstraint
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class Movimiento(Base):
    __tablename__ = "movimientos"

    id = Column(BigInteger, primary_key=True, index=True)
    importacion_id = Column(Integer, ForeignKey("importaciones.id", ondelete="RESTRICT"), nullable=True, index=True)
    gestion_id = Column(Integer, ForeignKey("gestiones.id", ondelete="RESTRICT"), nullable=False, index=True)
    region_id = Column(Integer, ForeignKey("regiones.id", ondelete="RESTRICT"), nullable=False, index=True)
    area_id = Column(Integer, ForeignKey("areas.id", ondelete="RESTRICT"), nullable=False, index=True)
    financiador_id = Column(Integer, ForeignKey("financiadores.id", ondelete="RESTRICT"), nullable=False, index=True)
    rubro_id = Column(Integer, ForeignKey("rubros.id", ondelete="RESTRICT"), nullable=False, index=True)
    cuenta_id = Column(Integer, nullable=True, index=True)
    month = Column(SmallInteger, nullable=False, index=True)
    voucher_date = Column(Date, nullable=True, index=True)
    voucher_type = Column(Integer, nullable=True)
    voucher_number = Column(Integer, nullable=True)
    check_number = Column(Integer, default=0, nullable=True)
    cuenta_contable_codigo = Column(String(50), nullable=True)
    cuenta_contable_nombre = Column(String(150), nullable=True)
    reference = Column(Text, nullable=True)
    beneficiario = Column(String(200), nullable=True)
    documento_ref = Column(String(60), nullable=True)
    debit_bob = Column(Numeric(15, 2), default=0.00, nullable=False)
    credit_bob = Column(Numeric(15, 2), default=0.00, nullable=False)
    debit_usd = Column(Numeric(15, 2), default=0.00, nullable=False)
    credit_usd = Column(Numeric(15, 2), default=0.00, nullable=False)
    exchange_rate = Column(Numeric(12, 4), default=6.96, nullable=False)
    tipos_cambio_id = Column(Integer, ForeignKey("tipos_cambio.id"), nullable=True)
    neto_bob = Column(Numeric(15, 2), nullable=True)  # Generado en DB: debit_bob - credit_bob
    neto_usd = Column(Numeric(15, 2), nullable=True)  # Generado en DB: debit_usd - credit_usd
    row_hash = Column(String(64), nullable=False, index=True)
    anulado = Column(Boolean, default=False, nullable=False)
    anulado_at = Column(DateTime(timezone=True), nullable=True)
    anulado_motivo = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    importacion = relationship("Importacion", back_populates="movimientos")
    modificaciones = relationship("ModificacionGasto", back_populates="movimiento")

    __table_args__ = (
        UniqueConstraint("id", "gestion_id", name="uq_mov_id_gestion"),
        ForeignKeyConstraint(
            ["cuenta_id", "rubro_id"],
            ["cuentas.id", "cuentas.rubro_id"],
            name="fk_mov_cuenta_rubro",
            ondelete="RESTRICT",
        ),
        Index("idx_movimientos_query", "gestion_id", "region_id", "area_id", "financiador_id", "rubro_id", "cuenta_id"),
        Index("idx_movimientos_month", "gestion_id", "month"),
        Index("idx_movimientos_fecha", "gestion_id", "voucher_date"),
    )
