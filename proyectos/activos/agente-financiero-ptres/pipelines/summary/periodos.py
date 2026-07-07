import re
from datetime import datetime

_MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
          "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
_POR_NOMBRE = {m.lower(): i + 1 for i, m in enumerate(_MESES)}
_POR_ABREV = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}


def normalizar_periodo(valor, anio_contexto: int | None = None) -> tuple[int, str] | None:
    if isinstance(valor, datetime):
        return (valor.year, _MESES[valor.month - 1])
    if not isinstance(valor, str):
        return None
    texto = valor.strip().lower()
    if texto in _POR_NOMBRE and anio_contexto is not None:
        return (anio_contexto, _MESES[_POR_NOMBRE[texto] - 1])
    match = re.match(r"^([a-z]{3})[a-z]*\.?\s*(\d{2})?$", texto)
    if match:
        abrev, anio_dos = match.group(1), match.group(2)
        if abrev in _POR_ABREV:
            anio = 2000 + int(anio_dos) if anio_dos else anio_contexto
            if anio is not None:
                return (anio, _MESES[_POR_ABREV[abrev] - 1])
    return None
