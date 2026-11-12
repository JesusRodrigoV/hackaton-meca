from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, Text, Boolean, Date, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base


class ReporteDefinicion(Base):
    __tablename__ = "reportes_definiciones"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(40), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    descripcion = Column(Text, nullable=True)
    tipo = Column(String(15), nullable=False)  # 'agregado', 'detalle', 'resumen'
    dimensiones = Column(JSONB, default=list, nullable=False)
    orden = Column(SmallInteger, default=0, nullable=False)


class ReporteProgramado(Base):
    __tablename__ = "reportes_programados"

    id = Column(Integer, primary_key=True, index=True)
    reporte_id = Column(Integer, ForeignKey("reportes_definiciones.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(120), nullable=False)
    cron_expr = Column(String(50), nullable=False)
    formato = Column(String(10), default="xlsx", nullable=False)  # 'xlsx', 'pdf', 'ambos'
    parametros_json = Column(JSONB, default=dict, nullable=False)
    destinatarios = Column(JSONB, default=list, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    creado_por = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    ultima_ejecucion = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ReporteGenerado(Base):
    __tablename__ = "reportes_generados"

    id = Column(BigInteger, primary_key=True, index=True)
    reporte_id = Column(Integer, ForeignKey("reportes_definiciones.id", ondelete="SET NULL"), nullable=True)
    programacion_id = Column(Integer, ForeignKey("reportes_programados.id", ondelete="SET NULL"), nullable=True)
    gestion_id = Column(Integer, ForeignKey("gestiones.id", ondelete="RESTRICT"), nullable=False, index=True)
    importacion_id = Column(Integer, ForeignKey("importaciones.id", ondelete="SET NULL"), nullable=True)
    fecha_corte = Column(Date, nullable=False)
    formato = Column(String(10), nullable=False)  # 'xlsx', 'pdf'
    origen = Column(String(20), default="manual", nullable=False)  # 'manual', 'programado', 'post_importacion'
    parametros_json = Column(JSONB, default=dict, nullable=False)
    file_path = Column(Text, nullable=False)
    file_sha256 = Column(String(64), nullable=False)
    file_size = Column(BigInteger, nullable=True)
    generado_por = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    generado_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_reportes_generados", "gestion_id", "reporte_id", "generado_at"),
    )
