import os
import shutil
import tempfile

UPLOAD_SPEC = {
    "summary": {
        "base": "Libro base (Summary_provision .xlsm)",
        "facturacion": "Detalle de Facturación",
        "ds": "Provisiones DS",
        "engineering": "Provisiones ES / Engineering",
        "consulting": "Overview Consulting",
    },
    "pl": {
        "movimientos": "Movimientos Auxiliares por Segmento",
    },
}

SALIDA_EXT = {"summary": ".xlsm", "pl": ".xlsx"}

CONTENT_TYPE = {
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
}

_EXTENSIONES_VALIDAS = {".xlsx", ".xlsm"}


class SubidaInvalida(Exception):
    def __init__(self, detalle: str):
        self.detalle = detalle
        super().__init__(detalle)


def slots_para(pipeline: str) -> dict[str, str]:
    return UPLOAD_SPEC.get(pipeline, {})


def validar_subidas(pipeline: str, nombres: dict[str, str]) -> None:
    requeridos = set(slots_para(pipeline))
    faltantes = requeridos - set(nombres)
    if faltantes:
        raise SubidaInvalida(f"Faltan archivos: {', '.join(sorted(faltantes))}")
    for slot, filename in nombres.items():
        ext = os.path.splitext(filename)[1].lower()
        if ext not in _EXTENSIONES_VALIDAS:
            raise SubidaInvalida(f"Extensión inválida en '{slot}': {filename}")


def _base_dir() -> str:
    return os.path.join(tempfile.gettempdir(), "orion")


def dir_token(token: str) -> str:
    return os.path.join(_base_dir(), token)


def guardar_archivos(token: str, archivos: dict[str, tuple[str, bytes]]) -> dict[str, str]:
    d = dir_token(token)
    os.makedirs(d, exist_ok=True)
    rutas = {}
    for slot, (filename, contenido) in archivos.items():
        ext = os.path.splitext(filename)[1].lower()
        destino = os.path.join(d, f"{slot}{ext}")
        with open(destino, "wb") as f:
            f.write(contenido)
        rutas[slot] = destino
    return rutas


def rutas_token(token: str) -> dict[str, str]:
    d = dir_token(token)
    if not os.path.isdir(d):
        return {}
    out = {}
    for nombre in os.listdir(d):
        slot, _ = os.path.splitext(nombre)
        if slot == "salida":
            continue
        out[slot] = os.path.join(d, nombre)
    return out


def ruta_salida(token: str, ext: str) -> str:
    return os.path.join(dir_token(token), f"salida{ext}")


def salida_existente(token: str) -> str | None:
    d = dir_token(token)
    if not os.path.isdir(d):
        return None
    for nombre in os.listdir(d):
        if nombre.startswith("salida"):
            return os.path.join(d, nombre)
    return None


def limpiar_token(token: str) -> None:
    shutil.rmtree(dir_token(token), ignore_errors=True)
