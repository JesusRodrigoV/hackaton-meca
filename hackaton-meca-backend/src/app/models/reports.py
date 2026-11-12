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
    SmallInteger,
    String,
    Text,
    Boolean,
    desc,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class ReporteDefinicion(Base):
    __tablename__ = "reportes_definiciones"

    id = Column(Integer, primary_key=True)
    code = Column(String(40), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    descripcion = Column(Text, nullable=True)
    tipo = Column(String(15), nullable=False)
    dimensiones = Column(
        JSONB,
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )
    orden = Column(SmallInteger, server_default=text("0"), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "tipo IN ('agregado', 'detalle', 'resumen')",
            name="ck_reporte_definicion_tipo",
        ),
    )


class ReporteProgramado(Base):
    __tablename__ = "reportes_programados"

    id = Column(Integer, primary_key=True)
    reporte_id = Column(
        Integer,
        ForeignKey("reportes_definiciones.id", ondelete="CASCADE"),
        nullable=True,
    )
    name = Column(String(120), nullable=False)
    cron_expr = Column(String(50), nullable=False)
    formato = Column(
        String(10),
        server_default=text("'xlsx'"),
        nullable=False,
    )
    parametros_json = Column(
        JSONB,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
    destinatarios = Column(
        JSONB,
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )
    activo = Column(Boolean, server_default=text("true"), nullable=False)
    creado_por = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    ultima_ejecucion = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "formato IN ('xlsx', 'pdf', 'ambos')",
            name="ck_reporte_programado_formato",
        ),
    )


class ReporteGenerado(Base):
    __tablename__ = "reportes_generados"

    id = Column(BigInteger, primary_key=True)
    reporte_id = Column(
        Integer,
        ForeignKey("reportes_definiciones.id", ondelete="SET NULL"),
        nullable=True,
    )
    programacion_id = Column(
        Integer,
        ForeignKey("reportes_programados.id", ondelete="SET NULL"),
        nullable=True,
    )
    gestion_id = Column(
        Integer,
        ForeignKey("gestiones.id", ondelete="RESTRICT"),
        nullable=False,
    )
    importacion_id = Column(
        Integer,
        ForeignKey("importaciones.id", ondelete="SET NULL"),
        nullable=True,
    )
    fecha_corte = Column(Date, nullable=False)
    formato = Column(String(10), nullable=False)
    origen = Column(
        String(20),
        server_default=text("'manual'"),
        nullable=False,
    )
    parametros_json = Column(
        JSONB,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
    file_path = Column(Text, nullable=False)
    file_sha256 = Column(CHAR(64), nullable=False)
    file_size = Column(BigInteger, nullable=True)
    generado_por = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    generado_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "formato IN ('xlsx', 'pdf')",
            name="ck_reporte_generado_formato",
        ),
        CheckConstraint(
            "origen IN ('manual', 'programado', 'post_importacion')",
            name="ck_reporte_generado_origen",
        ),
        Index(
            "idx_reportes_generados",
            "gestion_id",
            "reporte_id",
            desc(generado_at),
        ),
    )