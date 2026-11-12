from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Movimiento(Base):
    __tablename__ = "movimientos"

    id = Column(BigInteger, primary_key=True)
    importacion_id = Column(
        Integer,
        ForeignKey("importaciones.id", ondelete="RESTRICT"),
        nullable=True,
    )
    gestion_id = Column(
        Integer,
        ForeignKey("gestiones.id", ondelete="RESTRICT"),
        nullable=False,
    )
    region_id = Column(
        Integer,
        ForeignKey("regiones.id", ondelete="RESTRICT"),
        nullable=False,
    )
    area_id = Column(
        Integer,
        ForeignKey("areas.id", ondelete="RESTRICT"),
        nullable=False,
    )
    financiador_id = Column(
        Integer,
        ForeignKey("financiadores.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rubro_id = Column(
        Integer,
        ForeignKey("rubros.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cuenta_id = Column(Integer, nullable=True)
    month = Column(SmallInteger, nullable=False)
    voucher_date = Column(Date, nullable=True)
    voucher_type = Column(Integer, nullable=True)
    voucher_number = Column(Integer, nullable=True)
    check_number = Column(Integer, server_default=text("0"), nullable=True)
    cuenta_contable_codigo = Column(String(50), nullable=True)
    cuenta_contable_nombre = Column(String(150), nullable=True)
    reference = Column(Text, nullable=True)
    beneficiario = Column(String(200), nullable=True)
    documento_ref = Column(String(60), nullable=True)
    debit_bob = Column(
        Numeric(15, 2),
        server_default=text("0.00"),
        nullable=False,
    )
    credit_bob = Column(
        Numeric(15, 2),
        server_default=text("0.00"),
        nullable=False,
    )
    debit_usd = Column(
        Numeric(15, 2),
        server_default=text("0.00"),
        nullable=False,
    )
    credit_usd = Column(
        Numeric(15, 2),
        server_default=text("0.00"),
        nullable=False,
    )
    exchange_rate = Column(
        Numeric(12, 4),
        server_default=text("6.96"),
        nullable=False,
    )
    tipos_cambio_id = Column(
        Integer,
        ForeignKey("tipos_cambio.id"),
        nullable=True,
    )
    neto_bob = Column(
        Numeric(15, 2),
        Computed("debit_bob - credit_bob", persisted=True),
    )
    neto_usd = Column(
        Numeric(15, 2),
        Computed("debit_usd - credit_usd", persisted=True),
    )
    row_hash = Column(CHAR(64), nullable=False)
    anulado = Column(Boolean, server_default=text("false"), nullable=False)
    anulado_at = Column(DateTime(timezone=True), nullable=True)
    anulado_motivo = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    importacion = relationship("Importacion", back_populates="movimientos")
    modificaciones = relationship("ModificacionGasto", back_populates="movimiento")

    __table_args__ = (
        CheckConstraint(
            "month BETWEEN 1 AND 12",
            name="ck_movimiento_month",
        ),
        CheckConstraint("debit_bob >= 0", name="ck_movimiento_debit_bob"),
        CheckConstraint("credit_bob >= 0", name="ck_movimiento_credit_bob"),
        CheckConstraint("debit_usd >= 0", name="ck_movimiento_debit_usd"),
        CheckConstraint("credit_usd >= 0", name="ck_movimiento_credit_usd"),
        CheckConstraint(
            "exchange_rate > 0",
            name="ck_movimiento_exchange_rate",
        ),
        UniqueConstraint("id", "gestion_id", name="uq_mov_id_gestion"),
        ForeignKeyConstraint(
            ["cuenta_id", "rubro_id"],
            ["cuentas.id", "cuentas.rubro_id"],
            name="fk_mov_cuenta_rubro",
            ondelete="RESTRICT",
        ),
        Index(
            "uq_movimientos_row_hash",
            "row_hash",
            unique=True,
            postgresql_where=text("NOT anulado"),
        ),
        Index(
            "idx_movimientos_query",
            "gestion_id",
            "region_id",
            "area_id",
            "financiador_id",
            "rubro_id",
            "cuenta_id",
        ),
        Index("idx_movimientos_month", "gestion_id", "month"),
        Index("idx_movimientos_fecha", "gestion_id", "voucher_date"),
        Index("idx_movimientos_importacion", "importacion_id"),
    )