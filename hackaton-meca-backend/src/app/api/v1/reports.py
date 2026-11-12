import io
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, require_permission
from app.db.session import get_db
from app.models.security import User

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
def export_report_excel(
    tipo: str = Query("general", description="Tipo de reporte a exportar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sql = text("""
        SELECT 
            COALESCE(c.code, ru.code) AS codigo,
            COALESCE(c.name, ru.name) AS cuenta,
            ru.name AS rubro,
            r.name AS region,
            a.name AS area,
            f.name AS financiador,
            v.presupuesto_inicial_bob AS inicial,
            v.modificaciones_bob AS modif,
            v.presupuesto_vigente_bob AS vigente,
            v.ejecutado_bob AS ejecutado,
            v.saldo_bob AS saldo,
            COALESCE(v.pct_ejecucion, 0) AS porcentaje,
            v.alerta AS estado
        FROM v_ejecucion_vs_presupuesto v
        JOIN regiones r ON r.id = v.region_id
        JOIN areas a ON a.id = v.area_id
        JOIN financiadores f ON f.id = v.financiador_id
        JOIN rubros ru ON ru.id = v.rubro_id
        LEFT JOIN cuentas c ON c.id = v.cuenta_id
        ORDER BY r.name, ru.code;
    """)
    rows = db.execute(sql).mappings().all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ejecucion Presupuestaria"

    # Encabezado institucional
    header_fill = PatternFill(start_color="2B255C", end_color="2B255C", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

    headers = [
        "Código", "Cuenta / Partida", "Rubro", "Región", "Área", "Financiador",
        "Ppto Inicial (Bs)", "Modificaciones (Bs)", "Ppto Vigente (Bs)",
        "Ejecutado (Bs)", "Saldo Disponible (Bs)", "% Ejecución", "Estado"
    ]
    ws.append(headers)

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for r in rows:
        ws.append([
            r["codigo"],
            r["cuenta"],
            r["rubro"],
            r["region"],
            r["area"],
            r["financiador"],
            float(r["inicial"] or 0),
            float(r["modif"] or 0),
            float(r["vigente"] or 0),
            float(r["ejecutado"] or 0),
            float(r["saldo"] or 0),
            float(r["porcentaje"] or 0),
            r["estado"],
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"Reporte_Presupuestario_MECA_{tipo}.xlsx"
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
