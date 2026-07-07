import dataclasses
import os
import tempfile
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from core.registry import register
from pipelines.summary.spec import build_summary_spec
from pipelines.pl.spec import build_pl_spec


def _mock_interpret_summary(raw_files):
    return {
        "ledger_vivo": [
            {"proyecto": "26gmx3000.001", "anio": 2026, "periodo": "Abril", "monto_mxn": 150000,
             "cc": 3000, "cliente": "BorgWarner MX", "nombre_proyecto": "", "moneda": "MXN",
             "monto_original": 150000, "tc": 1},
            {"proyecto": "26gmx4000.002", "anio": 2026, "periodo": "Abril", "monto_mxn": 80000,
             "cc": 4000, "cliente": "P3 USA", "nombre_proyecto": "", "moneda": "MXN",
             "monto_original": 80000, "tc": 1},
        ],
        "cierres": [
            {"codigo": "26gmx3000.001", "anio": 2026, "mes": "Abril", "origen": "facturacion"},
        ],
        "provisiones_actuales": [
            {"proyecto": "26gmx2000.005", "monto_mxn": 200000, "cc": 2000, "cliente": "Cliente Nuevo",
             "moneda": "MXN", "monto_original": 200000, "tc": 1}
        ],
        "concentrado": {},
        "alertas": [],
    }


def _build_interpret_summary():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or api_key.startswith("sk-ant-local"):
        return None

    import anthropic
    from pipelines.summary.orquestador import interpretar_summary

    client = anthropic.Anthropic(api_key=api_key)

    def interpret(raw_files):
        faltantes = [
            slot for slot in ("base", "facturacion", "ds", "engineering", "consulting")
            if not raw_files.get(slot) or not os.path.exists(raw_files[slot])
        ]
        if faltantes:
            raise RuntimeError(f"Faltan archivos subidos para Summary: {', '.join(faltantes)}")
        return interpretar_summary(
            raw_files, client, mes=raw_files.get("_mes"),
            tipos_cambio_override=raw_files.get("_tc"),
        )

    return interpret


def _build_write_summary():
    from pipelines.summary.write import escribir_hoja_mes

    reportes_dir = os.environ.get("AGENTE_REPORTES_DIR", "reportes")
    os.makedirs(reportes_dir, exist_ok=True)

    def write(detalle, archivo_destino=None):
        nombre = f"Summary_{detalle['hoja_mes_nuevo']}.xlsm"
        ruta = os.path.join(reportes_dir, nombre)
        alertas_kpi = escribir_hoja_mes(
            ruta_origen=detalle["ruta_origen"],
            ruta_destino=ruta,
            hoja_mes_anterior=detalle["hoja_mes_anterior"],
            hoja_mes_nuevo=detalle["hoja_mes_nuevo"],
            filas=detalle["filas"],
            concentrado=detalle["concentrado"],
            mes_actual=detalle["mes_actual"],
        )
        counts = detalle["counts"]
        return {
            "archivo": nombre,
            "filas_escritas": counts["mantenidas"] + counts["nuevas"] + counts["cerradas"],
            "cerradas": counts["cerradas"],
            "mantenidas": counts["mantenidas"],
            "nuevas": counts["nuevas"],
            "alertas_kpi": alertas_kpi,
        }

    return write


def _build_drive_service():
    json_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not json_path or not os.path.exists(json_path):
        return None
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds = service_account.Credentials.from_service_account_file(
        json_path, scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)


def _build_interpret_pl(drive_service):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or api_key.startswith("sk-ant-local"):
        return None

    import anthropic
    from pipelines.pl.interpret import interpret_pl

    client = anthropic.Anthropic(api_key=api_key)

    def interpret(raw_files):
        # raw_files = {slot: ruta} de los archivos subidos en Orión. El P&L usa el
        # ContPaq "Movimientos Auxiliares" que el usuario sube (ya no se baja de Drive).
        ruta = (raw_files or {}).get("movimientos")
        if not ruta or not os.path.exists(ruta):
            raise RuntimeError("Falta el archivo de Movimientos Auxiliares (P&L) subido")
        with open(ruta, "rb") as f:
            wb_bytes = f.read()
        return interpret_pl(wb_bytes, client)

    return interpret


def _build_write_pl():
    from pipelines.pl.write import escribir_pl

    reportes_dir = os.environ.get("AGENTE_REPORTES_DIR", "reportes")
    os.makedirs(reportes_dir, exist_ok=True)

    def write(detalle, archivo_destino=None):
        periodo = detalle["periodo"]
        nombre = f"PL_{periodo.replace('-', '_')}.xlsx"
        ruta = os.path.join(reportes_dir, nombre)
        escribir_pl(ruta_destino=ruta, plan=detalle["plan"], periodo=periodo)
        return {"archivo": nombre, "net_profit": detalle["plan"]["totales"]["NET_PROFIT"]["TOTAL"]}

    return write


_drive_service = _build_drive_service()
_interpret_pl = _build_interpret_pl(_drive_service)

if _interpret_pl is None:
    def _interpret_pl(raw_files):
        return {
            "cuentas": [
                {"numero": "4110-002-001-000", "label": "Ventas internacionales", "rubro": "INCOMES",
                 "segmentos": {"BO": {"cargos": 0, "abonos": 280000}, "CONS OPS": {"cargos": 0, "abonos": 150000}, "ING": {"cargos": 0, "abonos": 0}, "DIGITAL SOLUTIONS": {"cargos": 0, "abonos": 0}}},
                {"numero": "6100-001-001-000", "label": "Honorarios consultores", "rubro": "EXPENSES",
                 "segmentos": {"BO": {"cargos": 90000, "abonos": 0}, "CONS OPS": {"cargos": 60000, "abonos": 0}, "ING": {"cargos": 0, "abonos": 0}, "DIGITAL SOLUTIONS": {"cargos": 0, "abonos": 0}}},
            ]
        }


_interpret_summary_real = _build_interpret_summary()

_summary_spec = build_summary_spec(
    interpret_override=_interpret_summary_real or _mock_interpret_summary,
    ruta_origen="agente.db",
    ruta_destino="agente.db",
    hoja_mes_anterior="2026_Abr",
    hoja_mes_nuevo="2026_May",
)

if _interpret_summary_real is not None:
    register(dataclasses.replace(_summary_spec, write=_build_write_summary()))
else:
    register(dataclasses.replace(
        _summary_spec,
        write=lambda detalle, archivo_destino: {
            "archivo": "mock_summary_mayo.xlsm",
            "filas_escritas": detalle["counts"]["mantenidas"] + detalle["counts"]["nuevas"] + detalle["counts"]["cerradas"],
            "cerradas": detalle["counts"]["cerradas"],
            "mantenidas": detalle["counts"]["mantenidas"],
            "nuevas": detalle["counts"]["nuevas"],
        },
    ))

_pl_spec = build_pl_spec(
    interpret_override=_interpret_pl,
    ruta_destino="agente.db",
    periodo="2026-03",
)
register(dataclasses.replace(
    _pl_spec,
    write=_build_write_pl(),
))


if __name__ == "__main__":
    host = os.getenv("AGENTE_HOST", "127.0.0.1")
    uvicorn.run("core.api:app", host=host, port=8000, reload=False)
