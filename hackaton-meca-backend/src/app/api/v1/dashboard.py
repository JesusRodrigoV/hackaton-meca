from decimal import Decimal
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, require_permission
from app.db.session import get_db
from app.models.catalogs import Financiador, Region
from app.models.movimientos import Movimiento
from app.models.security import User

router = APIRouter()


@router.get(
    "/kpis",
    dependencies=[Depends(require_permission("dashboard.ver"))],
)
def get_kpis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sql = text("""
        SELECT 
            COALESCE(SUM(presupuesto_vigente_bob), 0) AS total_vigente,
            COALESCE(SUM(ejecutado_bob), 0) AS total_ejecutado,
            COALESCE(SUM(saldo_bob), 0) AS total_saldo,
            COUNT(CASE WHEN alerta = 'SOBREEJECUCION' THEN 1 END) AS count_sobreejec,
            COUNT(CASE WHEN alerta = 'EJECUCION_SIN_PRESUPUESTO' THEN 1 END) AS count_alerta,
            COUNT(CASE WHEN alerta = 'SIN_EJECUCION' THEN 1 END) AS count_sin_ejec
        FROM v_ejecucion_vs_presupuesto;
    """)
    row = db.execute(sql).mappings().one()

    tot_vigente = float(row["total_vigente"])
    tot_ejec = float(row["total_ejecutado"])
    tot_saldo = float(row["total_saldo"])
    pct = round((tot_ejec / tot_vigente * 100), 2) if tot_vigente > 0 else 0.0

    total_movs = db.scalar(
        select(func.count(Movimiento.id)).where(Movimiento.anulado.is_(False))
    ) or 0

    return {
        "presupuestoVigenteBob": tot_vigente,
        "ejecutadoBob": tot_ejec,
        "saldoDisponibleBob": tot_saldo,
        "porcentajeEjecucion": pct,
        "totalMovimientos": total_movs,
        "cuentasSobreejecutadas": row["count_sobreejec"],
        "cuentasEnAlerta": row["count_alerta"],
        "cuentasSinEjecucion": row["count_sin_ejec"],
    }


@router.get(
    "/charts/by-financier",
    dependencies=[Depends(require_permission("dashboard.ver"))],
)
def get_chart_financier(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sql = text("""
        SELECT 
            f.name AS financiador,
            COALESCE(SUM(v.presupuesto_vigente_bob), 0) AS vigente,
            COALESCE(SUM(v.ejecutado_bob), 0) AS ejecutado
        FROM v_ejecucion_vs_presupuesto v
        JOIN financiadores f ON f.id = v.financiador_id
        GROUP BY f.name
        ORDER BY f.name;
    """)
    rows = db.execute(sql).mappings().all()
    labels = [r["financiador"] for r in rows]
    vigente = [float(r["vigente"]) for r in rows]
    ejecutado = [float(r["ejecutado"]) for r in rows]

    return {
        "labels": labels,
        "datasets": [
            {"label": "Presupuesto Vigente (Bs)", "data": vigente},
            {"label": "Ejecutado (Bs)", "data": ejecutado},
        ],
    }


@router.get(
    "/charts/by-region",
    dependencies=[Depends(require_permission("dashboard.ver"))],
)
def get_chart_region(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sql = text("""
        SELECT 
            r.name AS region,
            COALESCE(SUM(v.ejecutado_bob), 0) AS ejecutado
        FROM v_ejecucion_vs_presupuesto v
        JOIN regiones r ON r.id = v.region_id
        GROUP BY r.name
        ORDER BY r.name;
    """)
    rows = db.execute(sql).mappings().all()
    labels = [r["region"] for r in rows]
    data = [float(r["ejecutado"]) for r in rows]

    return {
        "labels": labels,
        "datasets": [
            {"label": "Ejecución por Región (Bs)", "data": data},
        ],
    }
