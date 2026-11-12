from app.services.report_export import (
    ReportDataset,
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


def test_render_excel_bytes_returns_valid_xlsx():
    xlsx = render_excel_bytes(_sample_dataset())
    assert xlsx[:2] == b"PK"
    assert len(xlsx) > 1000


def test_render_pdf_bytes_returns_valid_pdf():
    pdf = render_pdf_bytes(_sample_dataset(), generated_by="test@ensenaporbolivia.org", moneda="BOB")
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1000
