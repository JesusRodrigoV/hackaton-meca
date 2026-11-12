from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.catalogs import Area, Cuenta, Financiador, Gestion, Region, Rubro
from app.models.presupuestos import ModificacionGasto, Presupuesto, PresupuestoModificacion
from app.schemas.presupuestos import ModificacionCreate, PresupuestoCreate, PresupuestoTechoOut


def get_techos_presupuestarios(db: Session, gestion_id: Optional[int] = None) -> List[PresupuestoTechoOut]:
    sql = text("""
        SELECT 
            row_number() OVER () AS id,
            COALESCE(c.code, ru.code) AS codigo_cuenta,
            COALESCE(c.name, ru.name) AS nombre_cuenta,
            ru.name AS rubro,
            r.name AS region,
            a.name AS area,
            f.name AS financiador,
            COALESCE(v.presupuesto_inicial_bob, 0) AS monto_inicial_bob,
            COALESCE(v.modificaciones_bob, 0) AS modificaciones_bob,
            COALESCE(v.presupuesto_vigente_bob, 0) AS monto_vigente_bob,
            COALESCE(v.ejecutado_bob, 0) AS monto_ejecutado_bob,
            COALESCE(v.saldo_bob, 0) AS saldo_disponible_bob,
            COALESCE(v.pct_ejecucion, 0) AS porcentaje_ejecucion,
            CASE 
                WHEN v.alerta = 'EJECUCION_SIN_PRESUPUESTO' THEN 'EJEC_SIN_PRESUP'
                ELSE v.alerta
            END AS estado
        FROM v_ejecucion_vs_presupuesto v
        JOIN regiones r ON r.id = v.region_id
        JOIN areas a ON a.id = v.area_id
        JOIN financiadores f ON f.id = v.financiador_id
        JOIN rubros ru ON ru.id = v.rubro_id
        LEFT JOIN cuentas c ON c.id = v.cuenta_id
        ORDER BY r.name, ru.code, c.code NULLS FIRST;
    """)

    results = db.execute(sql).mappings().all()
    output = []
    for r in results:
        output.append(
            PresupuestoTechoOut(
                id=r["id"],
                codigoCuenta=r["codigo_cuenta"],
                nombreCuenta=r["nombre_cuenta"],
                rubro=r["rubro"],
                region=r["region"],
                area=r["area"],
                financiador=r["financiador"],
                montoInicialBob=float(r["monto_inicial_bob"]),
                modificacionesBob=float(r["modificaciones_bob"]),
                montoVigenteBob=float(r["monto_vigente_bob"]),
                montoEjecutadoBob=float(r["monto_ejecutado_bob"]),
                saldoDisponibleBob=float(r["saldo_disponible_bob"]),
                porcentajeEjecucion=float(r["porcentaje_ejecucion"]),
                estado=r["estado"],
            )
        )
    return output


def create_presupuesto(db: Session, item: PresupuestoCreate) -> Presupuesto:
    p = Presupuesto(
        gestion_id=item.gestion_id,
        region_id=item.region_id,
        area_id=item.area_id,
        financiador_id=item.financiador_id,
        rubro_id=item.rubro_id,
        cuenta_id=item.cuenta_id,
        month=item.month,
        monto_original=Decimal(str(item.monto_bob)),
        amount_bob=Decimal(str(item.monto_bob)),
        amount_usd=round(Decimal(str(item.monto_bob)) / Decimal("6.96"), 2),
        linea=item.linea,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def list_modificaciones(db: Session):
    return db.scalars(
        select(PresupuestoModificacion).order_by(PresupuestoModificacion.created_at.desc())
    ).all()


def create_modificacion(
    db: Session,
    payload: ModificacionCreate,
    user_id: int,
    user_email: str,
):
    gestion = db.execute(select(Gestion).where(Gestion.year == 2026)).scalar_one_or_none()
    gestion_id = gestion.id if gestion else 1

    # Buscar presupuesto de origen por financiador
    fin_orig = db.execute(
        select(Financiador).where(Financiador.name.ilike(f"%{payload.financiadorOrigen}%"))
    ).scalar_one_or_none()

    fin_dest = db.execute(
        select(Financiador).where(Financiador.name.ilike(f"%{payload.financiadorDestino}%"))
    ).scalar_one_or_none()

    orig_pres = None
    dest_pres = None
    if fin_orig:
        orig_pres = db.execute(
            select(Presupuesto).where(Presupuesto.financiador_id == fin_orig.id)
        ).scalars().first()

    if fin_dest:
        dest_pres = db.execute(
            select(Presupuesto).where(Presupuesto.financiador_id == fin_dest.id)
        ).scalars().first()

    mod = PresupuestoModificacion(
        gestion_id=gestion_id,
        tipo="traspaso" if (orig_pres and dest_pres) else "ampliacion",
        origen_presupuesto_id=orig_pres.id if orig_pres else None,
        destino_presupuesto_id=dest_pres.id if dest_pres else (orig_pres.id if orig_pres else None),
        amount_bob=Decimal(str(payload.montoBob)),
        reason=f"[{payload.partida}] {payload.motivo} (De {payload.financiadorOrigen} a {payload.financiadorDestino})",
        estado="borrador",
        solicitado_por=user_id,
    )
    db.add(mod)
    db.commit()
    db.refresh(mod)
    return mod


def approve_modificacion(db: Session, mod_id: int, user_id: int, aprobador_name: str):
    mod = db.execute(
        select(PresupuestoModificacion).where(PresupuestoModificacion.id == mod_id)
    ).scalar_one_or_none()
    if not mod:
        return None
    mod.estado = "aprobado"
    mod.aprobado_por = user_id
    mod.aprobado_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(mod)
    return mod


def reject_modificacion(db: Session, mod_id: int, user_id: int):
    mod = db.execute(
        select(PresupuestoModificacion).where(PresupuestoModificacion.id == mod_id)
    ).scalar_one_or_none()
    if not mod:
        return None
    mod.estado = "rechazado"
    db.commit()
    db.refresh(mod)
    return mod
