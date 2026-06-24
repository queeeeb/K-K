from pathlib import Path

from openpyxl import load_workbook

from pipelines.summary.write import escribir_hoja_mes

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_escribir_hoja_mes_no_toca_kpi(tmp_path):
    destino = tmp_path / "summary_mayo.xlsm"
    filas = [
        ["Q-3", "Provision", 2026, "Mayo", 2000, "Cliente Cuatro", "Proyecto Cuatro", "26gmx2000.005",
         "MXN", 3000, 1, 3000, 0, 3000, 0, 0, 3000, "", ""],
    ]

    escribir_hoja_mes(
        ruta_origen=str(FIXTURES_DIR / "summary_abril.xlsm"),
        ruta_destino=str(destino),
        hoja_mes_anterior="2026_Abr",
        hoja_mes_nuevo="2026_May",
        filas=filas,
    )

    wb = load_workbook(destino)
    nueva = wb["2026_May"]

    for row in range(1, 12):
        assert nueva.cell(row=row, column=1).value == f"KPI fila {row}"

    assert nueva.cell(row=12, column=1).value == "Cotizacion"
    assert nueva.cell(row=13, column=8).value == "26gmx2000.005"
    assert nueva.cell(row=14, column=1).value is None


def test_escribir_hoja_mes_preserva_hoja_anterior(tmp_path):
    destino = tmp_path / "summary_mayo.xlsm"

    escribir_hoja_mes(
        ruta_origen=str(FIXTURES_DIR / "summary_abril.xlsm"),
        ruta_destino=str(destino),
        hoja_mes_anterior="2026_Abr",
        hoja_mes_nuevo="2026_May",
        filas=[],
    )

    wb = load_workbook(destino)
    abril = wb["2026_Abr"]
    assert abril.cell(row=13, column=8).value == "26gmx3000.001"
