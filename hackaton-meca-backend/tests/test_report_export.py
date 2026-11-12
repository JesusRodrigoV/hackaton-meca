from app.services.report_export import (
    ReportDataset,
    _compute_col_widths,
    render_excel_bytes,
    render_pdf_bytes,
)


def _sample_dataset() -> ReportDataset:
    return ReportDataset(
        code="REP-02",
        title="Ejecución por Financiador / Donante",
        headers=["Financiador", "Ppto Vigente (Bs)", "Ejecutado (Bs)", "% Ejecución"],
        rows=[
            ["CATALYST", 100000.0, 45000.0, 45.0],
            ["CEL & KJCF", 50000.0, 25000.0, 50.0],
        ],
        numeric_indices={1, 2, 3},
    )


def _wide_dataset() -> ReportDataset:
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
                "5.1.01",
                "Sueldos y Salarios Personal Docente y Administrativo de Programas",
                "Talento Humano",
                "La Paz",
                "Formación",
                "CATALYST",
                1250000.00,
                50000.00,
                1300000.00,
                1350000.00,
                -50000.00,
                103.85,
                "SOBREEJECUCION",
            ]
        ],
        numeric_indices={6, 7, 8, 9, 10, 11},
    )


def test_render_excel_bytes_returns_valid_xlsx():
    xlsx = render_excel_bytes(_sample_dataset())
    assert xlsx[:2] == b"PK"
    assert len(xlsx) > 1000


def test_render_pdf_bytes_returns_valid_pdf():
    pdf = render_pdf_bytes(_sample_dataset(), generated_by="test@ensenaporbolivia.org", moneda="BOB")
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1000


def test_wide_table_col_widths_sum_to_100_and_render_pdf():
    ds = _wide_dataset()
    widths = _compute_col_widths(ds.headers, ds.rows, ds.numeric_indices)
    assert len(widths) == len(ds.headers)
    assert 99.5 <= sum(widths) <= 100.5
    pdf = render_pdf_bytes(ds, generated_by="test@ensenaporbolivia.org", moneda="BOB")
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1000
