from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, require_permission
from app.db.session import get_db
from app.models.security import User
from app.services.report_export import (
    build_report_dataset,
    render_excel_bytes,
    render_pdf_bytes,
)

router = APIRouter()


@router.get(
    "/donor-execution",
    dependencies=[Depends(require_permission("reportes.ver"))],
)
@router.get(
    "/by-financier",
    dependencies=[Depends(require_permission("reportes.ver"))],
)
def get_donor_execution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sql = text("""
        SELECT 
            f.name AS financiador,
            COALESCE(SUM(v.presupuesto_inicial_bob), 0) AS inicial,
            COALESCE(SUM(v.modificaciones_bob), 0) AS modificaciones,
            COALESCE(SUM(v.presupuesto_vigente_bob), 0) AS vigente,
            COALESCE(SUM(v.ejecutado_bob), 0) AS ejecutado,
            COALESCE(SUM(v.saldo_bob), 0) AS saldo,
            CASE 
                WHEN COALESCE(SUM(v.presupuesto_vigente_bob), 0) > 0 
                THEN ROUND((COALESCE(SUM(v.ejecutado_bob), 0) / SUM(v.presupuesto_vigente_bob) * 100), 2)
                ELSE 0 
            END AS porcentaje
        FROM v_ejecucion_vs_presupuesto v
        JOIN financiadores f ON f.id = v.financiador_id
        GROUP BY f.name
        ORDER BY f.name;
    """)
    rows = db.execute(sql).mappings().all()
    return [
        {
            "financiador": r["financiador"],
            "inicialBob": float(r["inicial"]),
            "modificacionesBob": float(r["modificaciones"]),
            "vigenteBob": float(r["vigente"]),
            "ejecutadoBob": float(r["ejecutado"]),
            "saldoBob": float(r["saldo"]),
            "porcentaje": float(r["porcentaje"]),
        }
        for r in rows
    ]


@router.get(
    "/by-region",
    dependencies=[Depends(require_permission("reportes.ver"))],
)
def get_by_region(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sql = text("""
        SELECT 
            r.name AS region,
            COALESCE(SUM(v.presupuesto_vigente_bob), 0) AS vigente,
            COALESCE(SUM(v.ejecutado_bob), 0) AS ejecutado,
            COALESCE(SUM(v.saldo_bob), 0) AS saldo,
            CASE 
                WHEN COALESCE(SUM(v.presupuesto_vigente_bob), 0) > 0 
                THEN ROUND((COALESCE(SUM(v.ejecutado_bob), 0) / SUM(v.presupuesto_vigente_bob) * 100), 2)
                ELSE 0 
            END AS porcentaje
        FROM v_ejecucion_vs_presupuesto v
        JOIN regiones r ON r.id = v.region_id
        GROUP BY r.name
        ORDER BY r.name;
    """)
    rows = db.execute(sql).mappings().all()
    return [
        {
            "region": r["region"],
            "vigenteBob": float(r["vigente"]),
            "ejecutadoBob": float(r["ejecutado"]),
            "saldoBob": float(r["saldo"]),
            "porcentaje": float(r["porcentaje"]),
        }
        for r in rows
    ]


@router.get(
    "/by-area",
    dependencies=[Depends(require_permission("reportes.ver"))],
)
def get_by_area(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sql = text("""
        SELECT 
            a.name AS area,
            COALESCE(SUM(v.presupuesto_vigente_bob), 0) AS vigente,
            COALESCE(SUM(v.ejecutado_bob), 0) AS ejecutado,
            COALESCE(SUM(v.saldo_bob), 0) AS saldo,
            CASE 
                WHEN COALESCE(SUM(v.presupuesto_vigente_bob), 0) > 0 
                THEN ROUND((COALESCE(SUM(v.ejecutado_bob), 0) / SUM(v.presupuesto_vigente_bob) * 100), 2)
                ELSE 0 
            END AS porcentaje
        FROM v_ejecucion_vs_presupuesto v
        JOIN areas a ON a.id = v.area_id
        GROUP BY a.name
        ORDER BY a.name;
    """)
    rows = db.execute(sql).mappings().all()
    return [
        {
            "area": r["area"],
            "vigenteBob": float(r["vigente"]),
            "ejecutadoBob": float(r["ejecutado"]),
            "saldoBob": float(r["saldo"]),
            "porcentaje": float(r["porcentaje"]),
        }
        for r in rows
    ]


@router.get(
    "/budget-variances",
    dependencies=[Depends(require_permission("reportes.ver"))],
)
def get_budget_variances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sql = text("""
        SELECT 
            ru.name AS rubro,
            COALESCE(c.code, ru.code) AS codigo,
            COALESCE(c.name, ru.name) AS partida,
            f.name AS financiador,
            COALESCE(v.presupuesto_vigente_bob, 0) AS vigente,
            COALESCE(v.ejecutado_bob, 0) AS ejecutado,
            COALESCE(v.saldo_bob, 0) AS saldo,
            v.alerta AS estado
        FROM v_ejecucion_vs_presupuesto v
        JOIN rubros ru ON ru.id = v.rubro_id
        LEFT JOIN cuentas c ON c.id = v.cuenta_id
        JOIN financiadores f ON f.id = v.financiador_id
        WHERE v.alerta IN ('SOBREEJECUCION', 'EJECUCION_SIN_PRESUPUESTO')
        ORDER BY v.saldo_bob ASC;
    """)
    rows = db.execute(sql).mappings().all()
    return [
        {
            "rubro": r["rubro"],
            "codigo": r["codigo"],
            "partida": r["partida"],
            "financiador": r["financiador"],
            "vigenteBob": float(r["vigente"]),
            "ejecutadoBob": float(r["ejecutado"]),
            "saldoBob": float(r["saldo"]),
            "alerta": r["estado"],
        }
        for r in rows
    ]


@router.get(
    "/export",
    dependencies=[Depends(require_permission("reportes.exportar"))],
)
def export_report(
    tipo: str = Query("REP-01", description="Tipo de reporte a exportar (REP-01..REP-07)"),
    format: str = Query("excel", description="Formato de exportación: excel o pdf"),
    moneda: str = Query("BOB", description="Moneda de visualización: BOB o USD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    fmt = format.lower().strip()
    if fmt not in {"excel", "xlsx", "pdf"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no soportado. Use 'excel' o 'pdf'.",
        )

    dataset = build_report_dataset(db, tipo)
    safe_code = dataset.code.replace("/", "-")

    if fmt == "pdf":
        generated_by = getattr(current_user, "full_name", None) or current_user.email
        pdf_bytes = render_pdf_bytes(dataset, generated_by=generated_by, moneda=moneda.upper())
        filename = f"Reporte_{safe_code}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    xlsx_bytes = render_excel_bytes(dataset)
    filename = f"Reporte_{safe_code}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
