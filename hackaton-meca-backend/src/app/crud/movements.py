import hashlib
import io
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional
import openpyxl
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalogs import Area, Cuenta, Financiador, Gestion, Region, Rubro
from app.models.importaciones import Importacion, ImportacionFila
from app.models.movimientos import Movimiento
from app.schemas.movements import ImportacionLoteOut, MovimientoGastoOut


def list_movimientos(db: Session, gestion_id: Optional[int] = None) -> List[MovimientoGastoOut]:
    query = (
        select(Movimiento)
        .where(Movimiento.anulado.is_(False))
        .order_by(Movimiento.voucher_date.desc(), Movimiento.id.desc())
    )
    if gestion_id:
        query = query.where(Movimiento.gestion_id == gestion_id)

    movs = db.scalars(query).all()
    output = []
    for m in movs:
        # Resolver relaciones o valores por defecto
        reg = db.get(Region, m.region_id)
        area = db.get(Area, m.area_id)
        fin = db.get(Financiador, m.financiador_id)
        cta = db.get(Cuenta, m.cuenta_id) if m.cuenta_id else None
        rubro = db.get(Rubro, m.rubro_id)
        imp = db.get(Importacion, m.importacion_id) if m.importacion_id else None

        output.append(
            MovimientoGastoOut(
                id=m.id,
                fecha=m.voucher_date.strftime("%Y-%m-%d") if m.voucher_date else "",
                comprobante=m.documento_ref or f"EGR-{m.id:05d}",
                beneficiario=m.beneficiario or "Varios",
                concepto=m.reference or "Gasto operativo",
                moneda="BOB",
                tipoCambio=float(m.exchange_rate),
                montoBob=float(m.debit_bob),
                montoUsd=float(m.debit_usd),
                codigoCuenta=cta.code if cta else (rubro.code if rubro else ""),
                nombreCuenta=cta.name if cta else (rubro.name if rubro else ""),
                region=reg.name if reg else "Nacional",
                area=area.name if area else "General",
                financiador=fin.name if fin else "General",
                loteImportacion=imp.file_name if imp else "Registro Manual",
                auditHash=m.row_hash or "",
            )
        )
    return output


def list_batches(db: Session) -> List[ImportacionLoteOut]:
    batches = db.scalars(select(Importacion).order_by(Importacion.created_at.desc())).all()
    output = []
    estado_map = {
        "completado": "CONFIRMADO",
        "validado": "CONFIRMADO",
        "pendiente": "EN_REVISION",
        "revertido": "REVERTIDO",
    }
    for b in batches:
        output.append(
            ImportacionLoteOut(
                id=b.id,
                nombreArchivo=b.file_name,
                fechaCarga=b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "",
                usuarioCarga="Administrador General",
                totalRegistros=b.total_rows,
                totalMontoBob=float(b.archivo_debe_bob or 0),
                estado=estado_map.get(b.status, "CONFIRMADO"),
                checksumSha256=b.file_hash,
            )
        )
    return output


def revert_batch(db: Session, batch_id: int) -> bool:
    batch = db.get(Importacion, batch_id)
    if not batch:
        return False
    batch.status = "revertido"
    batch.reverted_at = datetime.now(timezone.utc)
    # Marcar movimientos asociados como anulados
    db.query(Movimiento).where(Movimiento.importacion_id == batch_id).update(
        {
            Movimiento.anulado: True,
            Movimiento.anulado_at: datetime.now(timezone.utc),
            Movimiento.anulado_motivo: f"Reversión de lote de importación #{batch_id}",
        }
    )
    db.commit()
    return True


def import_excel_file(
    db: Session,
    file_bytes: bytes,
    filename: str,
    user_id: int,
) -> dict:
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Verificar si el lote ya fue importado
    existing = db.execute(
        select(Importacion).where(
            Importacion.file_hash == file_hash,
            Importacion.status != "revertido",
        )
    ).scalar_one_or_none()
    if existing:
        return {
            "batch_id": existing.id,
            "count": existing.total_rows,
            "message": "Archivo previamente procesado",
        }

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    ws = wb.active

    gestion = db.execute(select(Gestion).where(Gestion.year == 2026)).scalar_one_or_none()
    gestion_id = gestion.id if gestion else 1

    # Crear registro de importación
    imp = Importacion(
        user_id=user_id,
        gestion_id=gestion_id,
        file_name=filename,
        file_hash=file_hash,
        modo="incremental",
        status="completado",
        total_rows=0,
        archivo_debe_bob=Decimal("0.00"),
    )
    db.add(imp)
    db.flush()

    # Pre-cargar catálogos para búsqueda rápida
    regiones = {r.name.lower(): r for r in db.scalars(select(Region)).all()}
    areas = {a.name.lower(): a for a in db.scalars(select(Area)).all()}
    financiadores = {f.name.lower(): f for f in db.scalars(select(Financiador)).all()}
    cuentas = {c.code: c for c in db.scalars(select(Cuenta)).all()}
    rubros = {r.code: r for r in db.scalars(select(Rubro)).all()}

    # Fallback default IDs
    default_reg = next(iter(regiones.values()))
    default_area = next(iter(areas.values()))
    default_fin = next(iter(financiadores.values()))
    default_rubro = next(iter(rubros.values()))

    processed = 0
    total_monto = Decimal("0.00")

    # Iterar filas (asumiendo cabecera en fila 1)
    # Columnas esperadas: Fecha, Comprobante, Beneficiario, Concepto, Código Cuenta, Región, Área, Financiador, Monto BOB
    rows = list(ws.iter_rows(values_only=True))
    data_rows = rows[1:] if len(rows) > 1 else []

    for idx, row in enumerate(data_rows, start=2):
        if not row or all(v is None for v in row):
            continue

        fecha_val = row[0]
        comp_val = str(row[1]) if len(row) > 1 and row[1] else f"IMP-F{idx}"
        benef_val = str(row[2]) if len(row) > 2 and row[2] else "Varios"
        conc_val = str(row[3]) if len(row) > 3 and row[3] else "Gasto importado"
        cta_code = str(row[4]).strip() if len(row) > 4 and row[4] else "5.1.01"

        reg_name = str(row[5]).strip().lower() if len(row) > 5 and row[5] else ""
        area_name = str(row[6]).strip().lower() if len(row) > 6 and row[6] else ""
        fin_name = str(row[7]).strip().lower() if len(row) > 7 and row[7] else ""

        try:
            monto_val = Decimal(str(row[8])) if len(row) > 8 and row[8] is not None else Decimal("100.00")
        except Exception:
            monto_val = Decimal("100.00")

        # Parsing fecha
        if isinstance(fecha_val, (date, datetime)):
            v_date = fecha_val.date() if isinstance(fecha_val, datetime) else fecha_val
        else:
            v_date = date(2026, 3, 1)

        reg_obj = regiones.get(reg_name, default_reg)
        area_obj = areas.get(area_name, default_area)
        fin_obj = financiadores.get(fin_name, default_fin)
        cta_obj = cuentas.get(cta_code)
        rubro_obj = cta_obj.rubro if cta_obj else default_rubro

        row_hash = hashlib.sha256(f"{imp.id}_{idx}_{comp_val}_{monto_val}".encode()).hexdigest()

        # Registrar fila en staging
        fila = ImportacionFila(
            importacion_id=imp.id,
            fila_excel=idx,
            tipo_fila="movimiento",
            estado="ok",
            row_hash=row_hash,
            raw_json={"row": [str(c) for c in row]},
        )
        db.add(fila)

        # Crear movimiento confirmado
        mov = Movimiento(
            importacion_id=imp.id,
            gestion_id=gestion_id,
            region_id=reg_obj.id,
            area_id=area_obj.id,
            financiador_id=fin_obj.id,
            rubro_id=rubro_obj.id,
            cuenta_id=cta_obj.id if cta_obj else None,
            month=v_date.month,
            voucher_date=v_date,
            documento_ref=comp_val,
            beneficiario=benef_val,
            reference=conc_val,
            debit_bob=monto_val,
            credit_bob=Decimal("0.00"),
            exchange_rate=Decimal("6.96"),
            debit_usd=round(monto_val / Decimal("6.96"), 2),
            credit_usd=Decimal("0.00"),
            row_hash=row_hash,
        )
        db.add(mov)

        processed += 1
        total_monto += monto_val

    imp.total_rows = processed
    imp.processed_rows = processed
    imp.archivo_debe_bob = total_monto
    imp.cargado_debe_bob = total_monto
    imp.confirmed_at = datetime.now(timezone.utc)
    db.commit()

    return {"batch_id": imp.id, "count": processed, "total_bob": float(total_monto)}
