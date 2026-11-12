from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    Column,
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


class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id = Column(BigInteger, primary_key=True)
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
    month = Column(SmallInteger, nullable=True)
    linea = Column(String(150), nullable=True)
    moneda = Column(
        CHAR(3),
        server_default=text("'BOB'"),
        nullable=False,
    )
    monto_original = Column(Numeric(15, 2), nullable=False)
    amount_bob = Column(
        Numeric(15, 2),
        server_default=text("0.00"),
        nullable=False,
    )
    amount_usd = Column(
        Numeric(15, 2),
        server_default=text("0.00"),
        nullable=True,
    )
    tipos_cambio_id = Column(
        Integer,
        ForeignKey("tipos_cambio.id"),
        nullable=True,
    )
    importacion_id = Column(
        Integer,
        ForeignKey("importaciones.id", ondelete="RESTRICT"),
        nullable=True,
    )
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

    __table_args__ = (
        CheckConstraint(
            "month IS NULL OR month BETWEEN 1 AND 12",
            name="ck_presupuesto_month",
        ),
        CheckConstraint(
            "moneda IN ('BOB', 'USD')",
            name="ck_presupuesto_moneda",
        ),
        CheckConstraint(
            "moneda <> 'BOB' OR monto_original = amount_bob",
            name="ck_pres_monto_bob",
        ),
        UniqueConstraint("id", "gestion_id", name="uq_pres_id_gestion"),
        ForeignKeyConstraint(
            ["cuenta_id", "rubro_id"],
            ["cuentas.id", "cuentas.rubro_id"],
            name="fk_pres_cuenta_rubro",
            ondelete="RESTRICT",
        ),
        Index(
            "uq_presupuestos_linea",
            "gestion_id",
            "region_id",
            "area_id",
            "financiador_id",
            "rubro_id",
            text("COALESCE(cuenta_id, 0)"),
            text("COALESCE(month, 0)"),
            text("COALESCE(linea, '')"),
            unique=True,
        ),
        Index(
            "idx_presupuestos_query",
            "gestion_id",
            "region_id",
            "area_id",
            "financiador_id",
            "rubro_id",
            "cuenta_id",
        ),
    )


class PresupuestoModificacion(Base):
    __tablename__ = "presupuesto_modificaciones"

    id = Column(BigInteger, primary_key=True)
    gestion_id = Column(
        Integer,
        ForeignKey("gestiones.id", ondelete="RESTRICT"),
        nullable=False,
    )
    tipo = Column(String(20), nullable=False)
    origen_presupuesto_id = Column(
        BigInteger,
        ForeignKey("presupuestos.id", ondelete="RESTRICT"),
        nullable=True,
    )
    destino_presupuesto_id = Column(
        BigInteger,
        ForeignKey("presupuestos.id", ondelete="RESTRICT"),
        nullable=True,
    )
    amount_bob = Column(Numeric(15, 2), nullable=False)
    reason = Column(Text, nullable=False)
    estado = Column(
        String(15),
        server_default=text("'borrador'"),
        nullable=False,
    )
    solicitado_por = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    aprobado_por = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    aprobado_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    origen_presupuesto = relationship(
        "Presupuesto",
        foreign_keys=[origen_presupuesto_id],
    )
    destino_presupuesto = relationship(
        "Presupuesto",
        foreign_keys=[destino_presupuesto_id],
    )

    __table_args__ = (
        CheckConstraint(
            "tipo IN ('ampliacion', 'reduccion', 'traspaso')",
            name="ck_pm_tipo",
        ),
        CheckConstraint("amount_bob > 0", name="ck_pm_amount"),
        CheckConstraint(
            "estado IN ('borrador', 'aprobado', 'rechazado')",
            name="ck_pm_estado",
        ),
        CheckConstraint(
            "(tipo = 'ampliacion' AND destino_presupuesto_id IS NOT NULL "
            "AND origen_presupuesto_id IS NULL) "
            "OR (tipo = 'reduccion' AND origen_presupuesto_id IS NOT NULL "
            "AND destino_presupuesto_id IS NULL) "
            "OR (tipo = 'traspaso' AND origen_presupuesto_id IS NOT NULL "
            "AND destino_presupuesto_id IS NOT NULL "
            "AND origen_presupuesto_id <> destino_presupuesto_id)",
            name="ck_pm_direccion",
        ),
        CheckConstraint(
            "estado <> 'aprobado' OR "
            "(aprobado_por IS NOT NULL AND aprobado_at IS NOT NULL)",
            name="ck_pm_aprobacion",
        ),
        Index("idx_pm_gestion_estado", "gestion_id", "estado"),
    )


class ModificacionGasto(Base):
    __tablename__ = "modificaciones"

    id = Column(BigInteger, primary_key=True)
    gestion_id = Column(Integer, nullable=False)
    movimiento_id = Column(BigInteger, nullable=False)
    financiador_origen_id = Column(
        Integer,
        ForeignKey("financiadores.id", ondelete="RESTRICT"),
        nullable=False,
    )
    financiador_destino_id = Column(
        Integer,
        ForeignKey("financiadores.id", ondelete="RESTRICT"),
        nullable=False,
    )
    amount_bob = Column(Numeric(15, 2), nullable=False)
    reason = Column(Text, nullable=False)
    estado = Column(
        String(15),
        server_default=text("'borrador'"),
        nullable=False,
    )
    solicitado_por = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    aprobado_por = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    aprobado_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    movimiento = relationship("Movimiento", back_populates="modificaciones")
    financiador_origen = relationship(
        "Financiador",
        foreign_keys=[financiador_origen_id],
    )
    financiador_destino = relationship(
        "Financiador",
        foreign_keys=[financiador_destino_id],
    )

    __table_args__ = (
        CheckConstraint("amount_bob > 0", name="ck_mod_amount"),
        CheckConstraint(
            "estado IN ('borrador', 'aprobado', 'rechazado')",
            name="ck_mod_estado",
        ),
        CheckConstraint(
            "financiador_origen_id <> financiador_destino_id",
            name="ck_mod_financiadores",
        ),
        CheckConstraint(
            "estado <> 'aprobado' OR "
            "(aprobado_por IS NOT NULL AND aprobado_at IS NOT NULL)",
            name="ck_mod_aprobacion",
        ),
        ForeignKeyConstraint(
            ["movimiento_id", "gestion_id"],
            ["movimientos.id", "movimientos.gestion_id"],
            name="fk_mod_movimiento",
            ondelete="RESTRICT",
        ),
        Index("idx_modificaciones_mov", "movimiento_id", "estado"),
    )