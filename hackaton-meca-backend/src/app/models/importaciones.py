from sqlalchemy import Column, Integer, BigInteger, String, Text, Date, DateTime, Numeric, ForeignKey, func, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class Importacion(Base):
    __tablename__ = "importaciones"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    gestion_id = Column(Integer, ForeignKey("gestiones.id", ondelete="RESTRICT"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    modo = Column(String(20), default="incremental", nullable=False)
    status = Column(String(20), default="pendiente", nullable=False, index=True)
    fecha_corte = Column(Date, nullable=True)
    total_rows = Column(Integer, default=0, nullable=False)
    processed_rows = Column(Integer, default=0, nullable=False)
    duplicate_rows = Column(Integer, default=0, nullable=False)
    error_rows = Column(Integer, default=0, nullable=False)
    archivo_debe_bob = Column(Numeric(15, 2), nullable=True)
    archivo_haber_bob = Column(Numeric(15, 2), nullable=True)
    cargado_debe_bob = Column(Numeric(15, 2), nullable=True)
    cargado_haber_bob = Column(Numeric(15, 2), nullable=True)
    log_errors = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    reverted_at = Column(DateTime(timezone=True), nullable=True)

    filas = relationship("ImportacionFila", back_populates="importacion", cascade="all, delete-orphan")
    movimientos = relationship("Movimiento", back_populates="importacion")


class ImportacionFila(Base):
    __tablename__ = "importacion_filas"

    id = Column(BigInteger, primary_key=True, index=True)
    importacion_id = Column(Integer, ForeignKey("importaciones.id", ondelete="CASCADE"), nullable=False, index=True)
    fila_excel = Column(Integer, nullable=False)
    tipo_fila = Column(String(15), nullable=False)  # 'movimiento', 'presupuesto'
    estado = Column(String(15), nullable=False, index=True)  # 'ok', 'duplicado', 'error', 'omitido'
    codigo_error = Column(String(40), nullable=True)
    mensaje_error = Column(Text, nullable=True)
    row_hash = Column(String(64), nullable=True)
    raw_json = Column(JSONB, nullable=False)

    importacion = relationship("Importacion", back_populates="filas")

    __table_args__ = (
        UniqueConstraint("importacion_id", "fila_excel", name="uq_importacion_fila"),
        Index("idx_importacion_filas_estado", "importacion_id", "estado"),
    )
