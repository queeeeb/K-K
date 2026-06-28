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
        "provisiones_mes_anterior": [
            {"proyecto": "26gmx3000.001", "monto_mxn": 150000, "cc": 3000, "cliente": "BorgWarner MX"},
            {"proyecto": "26gmx4000.002", "monto_mxn": 80000,  "cc": 4000, "cliente": "P3 USA"},
        ],
        "facturas_mes": [
            {"proyecto": "26gmx3000.001-BorgWarner MX- Proyecto Uno", "estado": "Pagado"}
        ],
        "provisiones_nuevas": [
            {"proyecto": "26gmx2000.005", "monto_mxn": 200000, "cc": 2000, "cliente": "Cliente Nuevo"}
        ],
        "alertas": [],
    }


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
    from core.drive_client import find_file_id, download_file

    client = anthropic.Anthropic(api_key=api_key)
    folder_id = os.environ.get("DRIVE_FOLDER_ID", "")
    drive_file_name = os.environ.get("DRIVE_PL_FILE_NAME", "")
    ruta_local = os.environ.get("AGENTE_LOCAL_PL_FILE", "")

    def interpret(raw_files):
        if drive_service and folder_id and drive_file_name:
            file_id = find_file_id(drive_service, drive_file_name, folder_id)
            wb_bytes = download_file(drive_service, file_id)
        elif ruta_local and os.path.exists(ruta_local):
            with open(ruta_local, "rb") as f:
                wb_bytes = f.read()
        else:
            raise RuntimeError("No hay fuente configurada para el archivo P&L")
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


_summary_spec = build_summary_spec(
    interpret_override=_mock_interpret_summary,
    ruta_origen="agente.db",
    ruta_destino="agente.db",
    hoja_mes_anterior="2026_Abr",
    hoja_mes_nuevo="2026_May",
)
register(dataclasses.replace(
    _summary_spec,
    write=lambda detalle, archivo_destino: {
        "archivo": "mock_summary_mayo.xlsm",
        "filas_escritas": detalle["counts"]["activas"] + detalle["counts"]["nuevas"],
        "canceladas": detalle["counts"]["canceladas"],
        "activas": detalle["counts"]["activas"],
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
