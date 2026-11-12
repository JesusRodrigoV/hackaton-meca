from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class Importacion(Base):
    __tablename__ = "importaciones"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    gestion_id = Column(
        Integer,
        ForeignKey("gestiones.id", ondelete="RESTRICT"),
        nullable=False,
    )
    file_name = Column(String(255), nullable=False)
    file_hash = Column(CHAR(64), nullable=False)
    modo = Column(String(20), server_default=text("'incremental'"), nullable=False)
    status = Column(String(20), server_default=text("'pendiente'"), nullable=False)
    fecha_corte = Column(Date, nullable=True)
    total_rows = Column(Integer, server_default=text("0"), nullable=False)
    processed_rows = Column(Integer, server_default=text("0"), nullable=False)
    duplicate_rows = Column(Integer, server_default=text("0"), nullable=False)
    error_rows = Column(Integer, server_default=text("0"), nullable=False)
    archivo_debe_bob = Column(Numeric(15, 2), nullable=True)
    archivo_haber_bob = Column(Numeric(15, 2), nullable=True)
    cargado_debe_bob = Column(Numeric(15, 2), nullable=True)
    cargado_haber_bob = Column(Numeric(15, 2), nullable=True)
    log_errors = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    reverted_at = Column(DateTime(timezone=True), nullable=True)

    filas = relationship(
        "ImportacionFila",
        back_populates="importacion",
        cascade="all, delete-orphan",
    )
    movimientos = relationship("Movimiento", back_populates="importacion")

    __table_args__ = (
        CheckConstraint(
            "modo IN ('incremental', 'reemplazo_periodo')",
            name="ck_importacion_modo",
        ),
        CheckConstraint(
            "status IN ('pendiente', 'validado', 'completado', 'revertido', 'fallido')",
            name="ck_importacion_status",
        ),
        Index(
            "uq_importaciones_hash",
            "gestion_id",
            "file_hash",
            unique=True,
            postgresql_where=text("status NOT IN ('revertido', 'fallido')"),
        ),
    )


class ImportacionFila(Base):
    __tablename__ = "importacion_filas"

    id = Column(BigInteger, primary_key=True)
    importacion_id = Column(
        Integer,
        ForeignKey("importaciones.id", ondelete="CASCADE"),
        nullable=False,
    )
    fila_excel = Column(Integer, nullable=False)
    tipo_fila = Column(String(15), nullable=False)
    estado = Column(String(15), nullable=False)
    codigo_error = Column(String(40), nullable=True)
    mensaje_error = Column(Text, nullable=True)
    row_hash = Column(CHAR(64), nullable=True)
    raw_json = Column(JSONB, nullable=False)

    importacion = relationship("Importacion", back_populates="filas")

    __table_args__ = (
        CheckConstraint(
            "tipo_fila IN ('movimiento', 'presupuesto')",
            name="ck_importacion_fila_tipo",
        ),
        CheckConstraint(
            "estado IN ('ok', 'duplicado', 'error', 'omitido')",
            name="ck_importacion_fila_estado",
        ),
        UniqueConstraint(
            "importacion_id",
            "fila_excel",
            name="uq_importacion_fila",
        ),
        Index("idx_importacion_filas_estado", "importacion_id", "estado"),
    )