from dataclasses import dataclass
from datetime import datetime, timezone
import html
import io
from typing import Any

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass
class ReportDataset:
    code: str
    title: str
    headers: list[str]
    rows: list[list[Any]]
    numeric_indices: set[int]


def _query_rep_01(db: Session) -> ReportDataset:
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
    return ReportDataset(
        code="REP-01",
        title="Ejecución General vs Techos Presupuestarios",
        headers=[
            "Código", "Cuenta / Partida", "Rubro", "Región", "Área", "Financiador",
            "Ppto Inicial (Bs)", "Modificaciones (Bs)", "Ppto Vigente (Bs)",
            "Ejecutado (Bs)", "Saldo Disponible (Bs)", "% Ejecución", "Estado",
        ],
        rows=[
            [
                r["codigo"], r["cuenta"], r["rubro"], r["region"], r["area"], r["financiador"],
                float(r["inicial"] or 0), float(r["modif"] or 0), float(r["vigente"] or 0),
                float(r["ejecutado"] or 0), float(r["saldo"] or 0), float(r["porcentaje"] or 0),
                r["estado"],
            ]
            for r in rows
        ],
        numeric_indices={6, 7, 8, 9, 10, 11},
    )


def _query_rep_02(db: Session) -> ReportDataset:
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
    return ReportDataset(
        code="REP-02",
        title="Ejecución por Financiador / Donante",
        headers=[
            "Financiador / Donante", "Ppto Inicial (Bs)", "Modificaciones (Bs)",
            "Ppto Vigente (Bs)", "Ejecutado (Bs)", "Saldo Disponible (Bs)", "% Ejecución",
        ],
        rows=[
            [
                r["financiador"], float(r["inicial"] or 0), float(r["modificaciones"] or 0),
                float(r["vigente"] or 0), float(r["ejecutado"] or 0),
                float(r["saldo"] or 0), float(r["porcentaje"] or 0),
            ]
            for r in rows
        ],
        numeric_indices={1, 2, 3, 4, 5, 6},
    )


def _query_rep_03(db: Session) -> ReportDataset:
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
    return ReportDataset(
        code="REP-03",
        title="Ejecución por Región Geográfica",
        headers=["Región", "Ppto Vigente (Bs)", "Ejecutado (Bs)", "Saldo Disponible (Bs)", "% Ejecución"],
        rows=[
            [
                r["region"], float(r["vigente"] or 0), float(r["ejecutado"] or 0),
                float(r["saldo"] or 0), float(r["porcentaje"] or 0),
            ]
            for r in rows
        ],
        numeric_indices={1, 2, 3, 4},
    )


def _query_rep_04(db: Session) -> ReportDataset:
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
    return ReportDataset(
        code="REP-04",
        title="Ejecución por Área Programática",
        headers=["Área Programática", "Ppto Vigente (Bs)", "Ejecutado (Bs)", "Saldo Disponible (Bs)", "% Ejecución"],
        rows=[
            [
                r["area"], float(r["vigente"] or 0), float(r["ejecutado"] or 0),
                float(r["saldo"] or 0), float(r["porcentaje"] or 0),
            ]
            for r in rows
        ],
        numeric_indices={1, 2, 3, 4},
    )


def _query_rep_06(db: Session) -> ReportDataset:
    sql = text("""
        SELECT
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
    return ReportDataset(
        code="REP-06",
        title="Informe de Desviaciones Críticas y Alertas",
        headers=[
            "Código", "Partida Presupuestaria", "Financiador",
            "Ppto Vigente (Bs)", "Gasto Real (Bs)", "Déficit / Saldo (Bs)", "Diagnóstico",
        ],
        rows=[
            [
                r["codigo"], r["partida"], r["financiador"],
                float(r["vigente"] or 0), float(r["ejecutado"] or 0),
                float(r["saldo"] or 0), r["estado"],
            ]
            for r in rows
        ],
        numeric_indices={3, 4, 5},
    )


def _query_rep_07(db: Session) -> ReportDataset:
    sql = text("""
        SELECT
            l.created_at,
            COALESCE(u.full_name, u.email, 'Sistema') AS usuario,
            l.action,
            l.entity,
            COALESCE(l.entity_id, '-') AS entity_id,
            COALESCE(l.prev_hash, '') AS prev_hash,
            COALESCE(l.row_hash, '') AS row_hash
        FROM audit_logs l
        LEFT JOIN users u ON u.id = l.user_id
        ORDER BY l.created_at DESC
        LIMIT 200;
    """)
    rows = db.execute(sql).mappings().all()
    return ReportDataset(
        code="REP-07",
        title="Pistas de Auditoría y Trazabilidad SHA-256",
        headers=["Fecha / Hora", "Usuario", "Operación", "Entidad", "ID", "Hash Previo", "Hash Actual (SHA-256)"],
        rows=[
            [
                r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r["created_at"] else "",
                r["usuario"],
                r["action"],
                r["entity"],
                r["entity_id"],
                (r["prev_hash"][:16] + "...") if r["prev_hash"] else "-",
                (r["row_hash"][:16] + "...") if r["row_hash"] else "-",
            ]
            for r in rows
        ],
        numeric_indices=set(),
    )


_REPORT_BUILDERS = {
    "REP-01": _query_rep_01,
    "REP-02": _query_rep_02,
    "REP-03": _query_rep_03,
    "REP-04": _query_rep_04,
    "REP-05": _query_rep_01,
    "REP-06": _query_rep_06,
    "REP-07": _query_rep_07,
}


def build_report_dataset(db: Session, tipo: str) -> ReportDataset:
    key = (tipo or "REP-01").upper()
    builder = _REPORT_BUILDERS.get(key, _query_rep_01)
    dataset = builder(db)
    if key == "REP-05":
        dataset.code = "REP-05"
        dataset.title = "Flujo y Ejecución Presupuestaria Detallada"
    return dataset


def render_excel_bytes(dataset: ReportDataset) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = dataset.code[:31]

    header_fill = PatternFill(start_color="2B255C", end_color="2B255C", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

    ws.append(dataset.headers)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for row in dataset.rows:
        ws.append(row)

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


def _format_cell(value: Any, is_numeric: bool) -> str:
    if is_numeric and isinstance(value, (int, float)):
        return f"{value:,.2f}"
    return html.escape(str(value if value is not None else ""))


def _compute_col_widths(
    headers: list[str],
    rows: list[list[Any]],
    numeric_indices: set[int],
) -> list[float]:
    """Compute percentage widths summing to 100% so wide tables never overflow."""
    n = len(headers)
    if n == 0:
        return []

    sample_rows = rows[:50]
    weights: list[float] = []
    for idx, h in enumerate(headers):
        # Header words can wrap, so weight by longest word + a fraction of total header
        header_words = [len(w) for w in h.split()] or [len(h)]
        header_weight = max(max(header_words) + 2, len(h) * 0.55)

        if idx in numeric_indices:
            max_num_len = max(
                (len(_format_cell(r[idx], True)) for r in sample_rows if idx < len(r)),
                default=8,
            )
            w = max(header_weight, max_num_len + 2, 10.0)
        else:
            avg_text_len = (
                sum(len(str(r[idx] or "")) for r in sample_rows if idx < len(r)) / max(len(sample_rows), 1)
            )
            w = max(header_weight, min(avg_text_len * 0.85, 28.0), 8.0)
        weights.append(w)

    total = sum(weights) or 1.0
    return [round((w / total) * 100.0, 2) for w in weights]


def render_pdf_bytes(dataset: ReportDataset, generated_by: str, moneda: str = "BOB") -> bytes:
    from weasyprint import HTML

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    is_wide = len(dataset.headers) >= 10
    col_widths = _compute_col_widths(dataset.headers, dataset.rows, dataset.numeric_indices)
    colgroup_html = "<colgroup>" + "".join(f'<col style="width: {w}%;" />' for w in col_widths) + "</colgroup>"

    headers_html = "".join(
        f'<th class="{"num" if idx in dataset.numeric_indices else ""}">{html.escape(h)}</th>'
        for idx, h in enumerate(dataset.headers)
    )

    if dataset.rows:
        rows_html = "".join(
            "<tr>"
            + "".join(
                f'<td class="{"num" if idx in dataset.numeric_indices else ""}">{_format_cell(val, idx in dataset.numeric_indices)}</td>'
                for idx, val in enumerate(row)
            )
            + "</tr>"
            for row in dataset.rows
        )
    else:
        colspan = max(len(dataset.headers), 1)
        rows_html = f'<tr><td colspan="{colspan}" class="empty">Sin registros para este reporte.</td></tr>'

    base_font = "6.8pt" if is_wide else "8.5pt"
    th_font = "6.6pt" if is_wide else "8pt"
    cell_pad = "3.5px 4px" if is_wide else "5px 7px"

    html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8" />
<style>
  @page {{
    size: A4 landscape;
    margin: 12mm 10mm 14mm 10mm;
    @bottom-left {{
      content: "Enseña por Bolivia";
      font-family: "DejaVu Sans", sans-serif;
      font-size: 7.5pt;
      color: #64748b;
    }}
    @bottom-right {{
      content: "Página " counter(page) " de " counter(pages);
      font-family: "DejaVu Sans", sans-serif;
      font-size: 7.5pt;
      color: #64748b;
    }}
  }}
  * {{
    box-sizing: border-box;
  }}
  body {{
    font-family: "DejaVu Sans", sans-serif;
    font-size: {base_font};
    color: #0f172a;
    margin: 0;
  }}
  .doc-header {{
    border-bottom: 2px solid #2B255C;
    padding-bottom: 8px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }}
  .brand {{
    font-size: 9pt;
    font-weight: 700;
    color: #2B255C;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  h1 {{
    font-size: 13pt;
    margin: 2px 0 0 0;
    color: #0f172a;
  }}
  .meta {{
    text-align: right;
    font-size: 7.5pt;
    color: #475569;
    line-height: 1.4;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
  }}
  thead {{
    display: table-header-group;
  }}
  tr {{
    page-break-inside: avoid;
  }}
  th {{
    background-color: #2B255C;
    color: #ffffff;
    font-weight: 700;
    text-align: left;
    padding: {cell_pad};
    font-size: {th_font};
    line-height: 1.25;
    border: 1px solid #2B255C;
    white-space: normal;
    overflow-wrap: break-word;
    word-wrap: break-word;
  }}
  td {{
    padding: {cell_pad};
    border-bottom: 1px solid #e2e8f0;
    vertical-align: top;
    line-height: 1.25;
    overflow-wrap: break-word;
    word-wrap: break-word;
  }}
  tbody tr:nth-child(even) {{
    background-color: #f8fafc;
  }}
  .num {{
    text-align: right;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }}
  .empty {{
    text-align: center;
    padding: 16px;
    color: #64748b;
  }}
</style>
</head>
<body>
  <header class="doc-header">
    <div>
      <div class="brand">Enseña por Bolivia · {html.escape(dataset.code)}</div>
      <h1>{html.escape(dataset.title)}</h1>
    </div>
    <div class="meta">
      <div><strong>Moneda base:</strong> {html.escape(moneda)}</div>
      <div><strong>Generado:</strong> {html.escape(generated_at)}</div>
      <div><strong>Usuario:</strong> {html.escape(generated_by)}</div>
    </div>
  </header>
  <table>
    {colgroup_html}
    <thead><tr>{headers_html}</tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</body>
</html>"""

    return HTML(string=html_doc).write_pdf()
