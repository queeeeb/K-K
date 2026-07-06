import re

from openpyxl import load_workbook

from pipelines.summary.extract import leer_provisiones_mes_anterior
from pipelines.summary.extract_fuentes import (
    extraer_consulting,
    extraer_ds,
    extraer_engineering,
    extraer_facturacion,
)
from pipelines.summary.historial import todos_los_codigos_conocidos
from pipelines.summary.interpret import (
    interpret_consulting,
    interpret_ds,
    interpret_engineering,
    interpret_facturacion,
)


def _cargar_rows(ruta: str, hoja: str | None = None) -> list[list]:
    wb = load_workbook(ruta, data_only=True)
    sheet = wb[hoja] if hoja and hoja in wb.sheetnames else wb[wb.sheetnames[0]]
    return [[cell.value for cell in row] for row in sheet.iter_rows()]


_FORMATO_CODIGO_VALIDO = re.compile(r"^\d{2}gmx\d+\.")


def _separar_sospechosos(provisiones: list[dict]) -> tuple[list[dict], list[str]]:
    validas, alertas = [], []
    for p in provisiones:
        if not _FORMATO_CODIGO_VALIDO.match(p["proyecto"]):
            alertas.append(
                f"Código con formato sospechoso excluido de la extracción automática, "
                f"requiere revisión manual: {p['proyecto']!r}"
            )
        else:
            validas.append(p)
    return validas, alertas


def interpretar_summary(raw_files: dict[str, str], client, mes: str | None = None) -> dict:
    wb_base = load_workbook(raw_files["base"], data_only=True, keep_vba=True)
    hojas = wb_base.sheetnames
    hoja_mes_anterior = hojas[-1]

    provisiones_mes_anterior = leer_provisiones_mes_anterior(wb_base, hoja_mes_anterior)
    codigos_conocidos = todos_los_codigos_conocidos(wb_base, hojas)

    rows_facturacion = _cargar_rows(raw_files["facturacion"], hoja="Detalle")
    estructura_facturacion = interpret_facturacion(rows_facturacion, client)
    facturas_mes = extraer_facturacion(rows_facturacion, estructura_facturacion)

    rows_ds = _cargar_rows(raw_files["ds"], hoja="2026")
    estructura_ds = interpret_ds(rows_ds, client)
    ds_actuales = extraer_ds(rows_ds, estructura_ds)

    rows_engineering = _cargar_rows(raw_files["engineering"], hoja="Hoja1")
    estructura_engineering = interpret_engineering(rows_engineering, client)
    engineering_actuales = extraer_engineering(rows_engineering, estructura_engineering)

    rows_consulting = _cargar_rows(raw_files["consulting"])
    estructura_consulting = interpret_consulting(rows_consulting, client)
    consulting_actuales = extraer_consulting(rows_consulting, estructura_consulting)

    provisiones_actuales, alertas = _separar_sospechosos(
        ds_actuales + engineering_actuales + consulting_actuales
    )

    return {
        "provisiones_mes_anterior": provisiones_mes_anterior,
        "facturas_mes": facturas_mes,
        "provisiones_actuales": provisiones_actuales,
        "codigos_conocidos": codigos_conocidos,
        "alertas": alertas,
        "ruta_base": raw_files["base"],
        "hoja_mes_anterior": hoja_mes_anterior,
        "hoja_mes_nuevo": mes,
    }
