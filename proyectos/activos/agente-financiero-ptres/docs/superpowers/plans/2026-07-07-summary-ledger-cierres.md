# Summary Ledger + Cierres Cruzados — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reescribir la reconciliación del pipeline Summary para tratar el archivo como un ledger (una fila por provisión mensual, cierre por `(código, periodo)`), poblar el tablero KPI (filas 3, 5, 11) desde el archivo de Facturación, y actualizar la pantalla de Resumen.

**Architecture:** El flujo `/procesar`→`/confirmar`, el contrato `PipelineSpec` y `core/` no cambian. Todo el cambio vive en `pipelines/summary/`: un normalizador de periodos nuevo, un cruce de señales de cierre, `reconciliar()` reescrito a mantenidas/nuevas/cierres, lectores nuevos (notas de celda DS, hoja Concentrado) y `write.py`/`spec.py`/`orquestador.py` recableados. Frontend `Resumen.jsx` con layout nuevo.

**Tech Stack:** Python 3.14, `uv`, openpyxl, pytest, FastAPI (sin tocar), React + Vite + Tailwind (frontend).

## Global Constraints

- Dependencias con `uv` (`uv run pytest`, `uv add <pkg>`). Nunca `pip`.
- TDD estricto: test que falla → implementación mínima → test pasa → commit.
- No se commitean spreadsheets (`.xlsx`/`.xlsm`): el `.gitignore` raíz los bloquea; los fixtures se regeneran en `conftest.py`.
- Sin comentarios salvo WHY no obvio. Sin docstrings. Responsabilidad única por archivo.
- Modelo Claude para interpretación: `claude-sonnet-4-6` (patrón ya usado en `interpret.py`).
- Mapeo de unidad de negocio fijo: **3000=Consulting, 2000=Engineering, 7000=Digital Services**.
- Columnas KPI: I=3000, J=2000, K=7000. Datos del ledger desde fila 13, headers en fila 12.
- Formato de código válido: `^\d{2}gmx\d+\.` (año+gmx+unidad+punto, resto libre).
- Correr todos los tests desde `pipelines/summary/`... no: correr desde la raíz del proyecto `agente-financiero-ptres/` con `uv run pytest`.

---

### Task 1: Normalizador de periodos

**Files:**
- Create: `pipelines/summary/periodos.py`
- Test: `pipelines/summary/tests/test_periodos.py`

**Interfaces:**
- Produces: `normalizar_periodo(valor, anio_contexto: int | None = None) -> tuple[int, str] | None` — devuelve `(anio, nombre_mes_es)` con `nombre_mes_es` capitalizado en español (`"Abril"`), o `None` si no se puede interpretar. Acepta `datetime`, nombre de mes en español (`"Abril"`, `"abril "`), y abreviaturas de nota DS (`"ENE26"`, `"feb26"`, `"DIC25"`, `"ago"`).

- [ ] **Step 1: Write the failing test**

```python
# pipelines/summary/tests/test_periodos.py
from datetime import datetime

from pipelines.summary.periodos import normalizar_periodo


def test_normaliza_datetime_al_mes_del_periodo():
    assert normalizar_periodo(datetime(2026, 4, 30)) == (2026, "Abril")


def test_normaliza_nombre_mes_espanol_con_anio_contexto():
    assert normalizar_periodo("Abril", anio_contexto=2026) == (2026, "Abril")


def test_normaliza_nombre_mes_con_espacios_y_mayusculas():
    assert normalizar_periodo("  MAYO ", anio_contexto=2026) == (2026, "Mayo")


def test_normaliza_abreviatura_con_anio_de_dos_digitos():
    assert normalizar_periodo("ENE26") == (2026, "Enero")
    assert normalizar_periodo("feb26") == (2026, "Febrero")
    assert normalizar_periodo("DIC25") == (2025, "Diciembre")


def test_normaliza_abreviatura_sin_anio_usa_contexto():
    assert normalizar_periodo("ago", anio_contexto=2026) == (2026, "Agosto")


def test_devuelve_none_si_no_reconoce():
    assert normalizar_periodo("se facturó junto", anio_contexto=2026) is None
    assert normalizar_periodo(None) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pipelines/summary/tests/test_periodos.py -v`
Expected: FAIL con `ModuleNotFoundError: pipelines.summary.periodos`

- [ ] **Step 3: Write minimal implementation**

```python
# pipelines/summary/periodos.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pipelines/summary/tests/test_periodos.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add pipelines/summary/periodos.py pipelines/summary/tests/test_periodos.py
git commit -m "feat(summary): normalizador de periodos (datetime, nombre es, abreviatura nota DS)"
```

---

### Task 2: Cruce de señales de cierre

**Files:**
- Modify: `pipelines/summary/calculate.py`
- Test: `pipelines/summary/tests/test_calculate.py`

**Interfaces:**
- Consumes: nada de otras tareas.
- Produces: `cruzar_cierres(pares_facturacion: list[tuple[str, int, str]], pares_notas_ds: list[tuple[str, int, str]]) -> tuple[list[dict], list[str]]`. Cada par es `(codigo, anio, mes)`. Devuelve `(cierres, alertas)` donde cada cierre es `{"codigo", "anio", "mes", "origen"}` con `origen` en `{"facturacion", "notas_ds", "ambas"}`. Los pares que aparecen en una sola señal generan una alerta de origen único pero **igual** se incluyen en `cierres`.

- [ ] **Step 1: Write the failing test**

```python
# añadir a pipelines/summary/tests/test_calculate.py
from pipelines.summary.calculate import cruzar_cierres


def test_cruzar_cierres_par_en_ambas_sin_alerta():
    cierres, alertas = cruzar_cierres(
        pares_facturacion=[("26gmx7000.010", 2026, "Marzo")],
        pares_notas_ds=[("26gmx7000.010", 2026, "Marzo")],
    )
    assert cierres == [{"codigo": "26gmx7000.010", "anio": 2026, "mes": "Marzo", "origen": "ambas"}]
    assert alertas == []


def test_cruzar_cierres_par_solo_facturacion_cierra_con_alerta():
    cierres, alertas = cruzar_cierres(
        pares_facturacion=[("26gmx3000.001", 2026, "Abril")],
        pares_notas_ds=[],
    )
    assert cierres[0]["origen"] == "facturacion"
    assert any("solo" in a.lower() and "facturaci" in a.lower() for a in alertas)


def test_cruzar_cierres_par_solo_notas_ds_cierra_con_alerta():
    cierres, alertas = cruzar_cierres(
        pares_facturacion=[],
        pares_notas_ds=[("26gmx7000.010", 2026, "Marzo")],
    )
    assert cierres[0]["origen"] == "notas_ds"
    assert any("solo" in a.lower() and "notas" in a.lower() for a in alertas)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pipelines/summary/tests/test_calculate.py::test_cruzar_cierres_par_en_ambas_sin_alerta -v`
Expected: FAIL con `ImportError: cannot import name 'cruzar_cierres'`

- [ ] **Step 3: Write minimal implementation**

```python
# añadir a pipelines/summary/calculate.py
def cruzar_cierres(
    pares_facturacion: list[tuple[str, int, str]],
    pares_notas_ds: list[tuple[str, int, str]],
) -> tuple[list[dict], list[str]]:
    set_fact = set(pares_facturacion)
    set_notas = set(pares_notas_ds)
    cierres, alertas = [], []
    for par in sorted(set_fact | set_notas):
        codigo, anio, mes = par
        en_fact, en_notas = par in set_fact, par in set_notas
        if en_fact and en_notas:
            origen = "ambas"
        elif en_fact:
            origen = "facturacion"
            alertas.append(f"Cierre de {codigo} ({mes} {anio}) detectado solo en Facturación.")
        else:
            origen = "notas_ds"
            alertas.append(f"Cierre de {codigo} ({mes} {anio}) detectado solo en Notas DS.")
        cierres.append({"codigo": codigo, "anio": anio, "mes": mes, "origen": origen})
    return cierres, alertas
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pipelines/summary/tests/test_calculate.py -k cruzar_cierres -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add pipelines/summary/calculate.py pipelines/summary/tests/test_calculate.py
git commit -m "feat(summary): cruce de señales de cierre facturacion + notas DS"
```

---

### Task 3: `reconciliar()` reescrito a modelo ledger

**Files:**
- Modify: `pipelines/summary/calculate.py`
- Test: `pipelines/summary/tests/test_calculate.py`

**Interfaces:**
- Consumes: `cruzar_cierres` (Task 2). El campo `periodo` de cada fila del ledger es el nombre de mes en español (`"Abril"`) y `anio` es int, tal como los devuelve `leer_provisiones_mes_anterior`.
- Produces: `reconciliar(ledger_vivo: list[dict], cierres: list[dict], provisiones_actuales: list[dict], alertas: list[str] | None = None, codigos_conocidos: set[str] | None = None) -> dict` con llaves `mantenidas`, `nuevas`, `cerradas`, `alertas`. `mantenidas` = filas del ledger no cerradas (intactas). `cerradas` = filas del ledger cuya `(proyecto, anio, mes)` coincide con un cierre. `nuevas` = todas las provisiones actuales, cada una con `codigo_nuevo: bool`. Un cierre que no matchea ninguna fila del ledger genera alerta.

- [ ] **Step 1: Reemplazar los tests viejos de `reconciliar`**

Borra de `test_calculate.py` estos tests obsoletos (probaban el modelo `activas` que ya no existe): `test_reconciliar_cancela_proyecto_facturado`, `test_reconciliar_factura_cancelada_no_cuenta`, `test_reconciliar_activas_tienen_monto_anterior`, `test_reconciliar_actualiza_monto_de_activa_encontrada_en_fuentes`, `test_reconciliar_activa_toma_moneda_y_tc_del_mes_actual`, `test_reconciliar_no_duplica_activa_encontrada_como_nueva`, `test_reconciliar_activa_no_encontrada_en_fuentes_mantiene_monto_y_alerta`. Conserva los de `codigo_nuevo`, `nuevas`, `alertas`, `cruzar_cierres`, `extraer_codigo` y `actualizar_nombres_nuevas`. Añade:

```python
def _fila_ledger(proyecto, anio, periodo, monto=1000, cc=3000):
    return {"proyecto": proyecto, "anio": anio, "periodo": periodo, "monto_mxn": monto,
            "cc": cc, "cliente": "Cliente X", "nombre_proyecto": "N", "moneda": "MXN",
            "monto_original": monto, "tc": 1}


def test_reconciliar_mantiene_fila_no_cerrada_intacta():
    ledger = [_fila_ledger("26gmx3000.001", 2026, "Marzo", monto=1500)]
    resultado = reconciliar(ledger, cierres=[], provisiones_actuales=[])
    assert resultado["mantenidas"] == ledger
    assert resultado["cerradas"] == []


def test_reconciliar_cierra_fila_por_codigo_y_periodo():
    ledger = [
        _fila_ledger("26gmx3000.001", 2026, "Marzo"),
        _fila_ledger("26gmx3000.001", 2026, "Abril"),
    ]
    cierres = [{"codigo": "26gmx3000.001", "anio": 2026, "mes": "Marzo", "origen": "ambas"}]
    resultado = reconciliar(ledger, cierres, provisiones_actuales=[])
    assert len(resultado["cerradas"]) == 1
    assert resultado["cerradas"][0]["periodo"] == "Marzo"
    assert len(resultado["mantenidas"]) == 1
    assert resultado["mantenidas"][0]["periodo"] == "Abril"


def test_reconciliar_cierre_a_fila_inexistente_alerta_sin_tocar():
    ledger = [_fila_ledger("26gmx3000.001", 2026, "Marzo")]
    cierres = [{"codigo": "26gmx9999.999", "anio": 2026, "mes": "Marzo", "origen": "facturacion"}]
    resultado = reconciliar(ledger, cierres, provisiones_actuales=[])
    assert resultado["cerradas"] == []
    assert len(resultado["mantenidas"]) == 1
    assert any("26gmx9999.999" in a for a in resultado["alertas"])


def test_reconciliar_provision_actual_es_fila_nueva_aunque_codigo_exista():
    ledger = [_fila_ledger("26gmx3000.001", 2026, "Marzo")]
    actuales = [{"proyecto": "26gmx3000.001", "monto_mxn": 2000, "cc": 3000, "cliente": "Cliente X"}]
    resultado = reconciliar(ledger, cierres=[], provisiones_actuales=actuales,
                            codigos_conocidos={"26gmx3000.001"})
    assert len(resultado["mantenidas"]) == 1
    assert len(resultado["nuevas"]) == 1
    assert resultado["nuevas"][0]["codigo_nuevo"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pipelines/summary/tests/test_calculate.py -k reconciliar -v`
Expected: FAIL (la firma vieja de `reconciliar` no acepta `cierres` ni devuelve `mantenidas`)

- [ ] **Step 3: Reescribir `reconciliar` en `calculate.py`**

Reemplaza la función `reconciliar` completa (líneas 11-65) por:

```python
def reconciliar(
    ledger_vivo: list[dict],
    cierres: list[dict],
    provisiones_actuales: list[dict],
    alertas: list[str] | None = None,
    codigos_conocidos: set[str] | None = None,
) -> dict:
    alertas = list(alertas or [])
    codigos_conocidos = codigos_conocidos or set()

    cierres_por_clave = {(c["codigo"], c["anio"], c["mes"]): c for c in cierres}
    claves_aplicadas = set()

    mantenidas, cerradas = [], []
    for fila in ledger_vivo:
        clave = (fila["proyecto"], fila.get("anio"), fila.get("periodo"))
        if clave in cierres_por_clave:
            cerradas.append(fila)
            claves_aplicadas.add(clave)
        else:
            mantenidas.append(fila)

    for clave, cierre in cierres_por_clave.items():
        if clave not in claves_aplicadas:
            codigo, anio, mes = clave
            alertas.append(
                f"Cierre de {codigo} ({mes} {anio}, origen {cierre['origen']}) no encontró "
                "fila abierta en el ledger — no se aplicó, requiere revisión manual."
            )

    nuevas = [
        {**p, "codigo_nuevo": p["proyecto"] not in codigos_conocidos}
        for p in provisiones_actuales
    ]

    return {
        "mantenidas": mantenidas,
        "cerradas": cerradas,
        "nuevas": nuevas,
        "alertas": alertas,
    }
```

Deja `extraer_codigo` y `actualizar_nombres_nuevas` como están, pero en `actualizar_nombres_nuevas` no hay cambios (sigue operando sobre `plan["resumen"]["nuevas"]` y `plan["detalle"]["filas"]`).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pipelines/summary/tests/test_calculate.py -v`
Expected: PASS (todos)

- [ ] **Step 5: Commit**

```bash
git add pipelines/summary/calculate.py pipelines/summary/tests/test_calculate.py
git commit -m "feat(summary): reconciliar como ledger (mantenidas/cerradas/nuevas)"
```

---

### Task 4: Facturación con periodo → pares de cierre

**Files:**
- Modify: `pipelines/summary/extract_fuentes.py`
- Modify: `pipelines/summary/tests/test_extract_fuentes.py`

**Interfaces:**
- Consumes: `normalizar_periodo` (Task 1), `extraer_codigo` (existente en calculate).
- Produces: `pares_cierre_facturacion(rows: list[list], estructura: dict) -> list[tuple[str, int, str]]`. Usa `estructura["proyecto_columna"]`, `estructura["estado_columna"]` y `estructura["periodo_columna"]`. Solo filas con estado en `{"Sin pagar", "Pagado"}` (excluye `Cancelado`). Extrae el prefijo del código (formato guión) y normaliza el `Periodo`. Filas cuyo periodo no se puede normalizar se omiten.

- [ ] **Step 1: Write the failing test**

```python
# añadir a pipelines/summary/tests/test_extract_fuentes.py
from datetime import datetime

from pipelines.summary.extract_fuentes import pares_cierre_facturacion


def test_pares_cierre_facturacion_extrae_codigo_y_periodo():
    rows = [
        ["Proyecto", "Estado", "Periodo"],
        ["26gmx3000.007-P3 USA- Borgwarner", "Sin pagar", datetime(2026, 4, 30)],
    ]
    estructura = {"proyecto_columna": 0, "estado_columna": 1, "periodo_columna": 2}
    assert pares_cierre_facturacion(rows, estructura) == [("26gmx3000.007", 2026, "Abril")]


def test_pares_cierre_facturacion_ignora_cancelado():
    rows = [
        ["Proyecto", "Estado", "Periodo"],
        ["26gmx3000.007-P3 USA", "Cancelado", datetime(2026, 4, 30)],
    ]
    estructura = {"proyecto_columna": 0, "estado_columna": 1, "periodo_columna": 2}
    assert pares_cierre_facturacion(rows, estructura) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pipelines/summary/tests/test_extract_fuentes.py -k pares_cierre -v`
Expected: FAIL con `ImportError: cannot import name 'pares_cierre_facturacion'`

- [ ] **Step 3: Write minimal implementation**

```python
# en pipelines/summary/extract_fuentes.py, añadir import arriba:
from pipelines.summary.calculate import extraer_codigo
from pipelines.summary.periodos import normalizar_periodo

_ESTADOS_FACTURADO = {"Sin pagar", "Pagado"}


def pares_cierre_facturacion(rows: list[list], estructura: dict) -> list[tuple[str, int, str]]:
    proyecto_col = estructura["proyecto_columna"]
    estado_col = estructura["estado_columna"]
    periodo_col = estructura["periodo_columna"]
    pares = []
    for row in rows[1:]:
        if not row[proyecto_col] or _texto(row[estado_col]) not in _ESTADOS_FACTURADO:
            continue
        periodo = normalizar_periodo(row[periodo_col])
        if periodo is None:
            continue
        codigo = extraer_codigo(row[proyecto_col], formato="guion")
        pares.append((codigo, periodo[0], periodo[1]))
    return pares
```

Nota: verificar que no haya import circular — `calculate.py` no importa `extract_fuentes`, así que el import es seguro.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pipelines/summary/tests/test_extract_fuentes.py -k pares_cierre -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add pipelines/summary/extract_fuentes.py pipelines/summary/tests/test_extract_fuentes.py
git commit -m "feat(summary): pares de cierre desde Facturacion (codigo + periodo)"
```

---

### Task 5: Lectura + interpretación de notas de celda DS

**Files:**
- Modify: `pipelines/summary/extract.py`
- Modify: `pipelines/summary/interpret.py`
- Modify: `pipelines/summary/tests/test_extract.py`
- Modify: `pipelines/summary/tests/test_interpret.py`

**Interfaces:**
- Consumes: `normalizar_periodo` (Task 1).
- Produces:
  - `leer_notas_num_factura_ds(ruta: str, num_factura_col: int, codigo_col: int, fila_inicio: int) -> list[dict]` — abre el workbook (openpyxl, sin data_only) y por cada fila desde `fila_inicio` con nota de celda en la columna `num_factura_col`, devuelve `{"codigo", "nota"}` (el código viene de `codigo_col`). Filas sin nota se omiten.
  - `interpret_notas_ds(notas: list[dict], anthropic_client, anio_contexto: int) -> list[tuple[str, int, str]]` — manda las notas a Claude, que devuelve por cada nota la lista de meses cubiertos; se normaliza cada mes con `normalizar_periodo(..., anio_contexto)` y se devuelven pares `(codigo, anio, mes)`. Notas cuyo mes no se puede normalizar generan (silenciosamente aquí) su omisión — la alerta la agrega el orquestador comparando entrada vs salida.

- [ ] **Step 1: Write the failing test (lectura de notas)**

```python
# añadir a pipelines/summary/tests/test_extract.py
from openpyxl.comments import Comment

from pipelines.summary.extract import leer_notas_num_factura_ds


def test_leer_notas_num_factura_ds(tmp_path):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "2026"
    ws.cell(row=6, column=4, value="26gmx7000.010")       # codigo_col=3 (0-idx) -> col 4
    celda = ws.cell(row=6, column=8, value="DS-2026-020")  # num_factura_col=7 (0-idx) -> col 8
    celda.comment = Comment("ENE26 100\nFEB26 200", "Estela")
    ws.cell(row=7, column=4, value="26gmx7000.011")
    ws.cell(row=7, column=8, value="DS-2026-021")          # sin nota
    ruta = tmp_path / "ds.xlsx"
    wb.save(ruta)

    resultado = leer_notas_num_factura_ds(str(ruta), num_factura_col=7, codigo_col=3, fila_inicio=5)

    assert resultado == [{"codigo": "26gmx7000.010", "nota": "ENE26 100\nFEB26 200"}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pipelines/summary/tests/test_extract.py -k notas -v`
Expected: FAIL con `ImportError: cannot import name 'leer_notas_num_factura_ds'`

- [ ] **Step 3: Implement `leer_notas_num_factura_ds`**

```python
# añadir a pipelines/summary/extract.py
from openpyxl import load_workbook


def leer_notas_num_factura_ds(
    ruta: str, num_factura_col: int, codigo_col: int, fila_inicio: int
) -> list[dict]:
    wb = load_workbook(ruta)
    sheet = wb[wb.sheetnames[0]] if "2026" not in wb.sheetnames else wb["2026"]
    resultado = []
    for row in range(fila_inicio + 1, sheet.max_row + 1):
        celda = sheet.cell(row=row, column=num_factura_col + 1)
        if celda.comment is None:
            continue
        codigo = sheet.cell(row=row, column=codigo_col + 1).value
        if isinstance(codigo, str) and codigo.strip():
            resultado.append({"codigo": codigo.strip(), "nota": celda.comment.text.strip()})
    return resultado
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pipelines/summary/tests/test_extract.py -k notas -v`
Expected: PASS

- [ ] **Step 5: Write the failing test (interpret notas)**

```python
# añadir a pipelines/summary/tests/test_interpret.py
from pipelines.summary.interpret import interpret_notas_ds


class _ClienteFake:
    def __init__(self, texto):
        self._texto = texto
        self.messages = self
    def create(self, **kwargs):
        class _M:
            def __init__(self, t): self.content = [type("C", (), {"text": t})]
        return _M(self._texto)


def test_interpret_notas_ds_devuelve_pares_por_mes():
    cliente = _ClienteFake('[{"codigo": "26gmx7000.010", "meses": ["ENE26", "FEB26"]}]')
    notas = [{"codigo": "26gmx7000.010", "nota": "ENE26 100\nFEB26 200"}]
    resultado = interpret_notas_ds(notas, cliente, anio_contexto=2026)
    assert ("26gmx7000.010", 2026, "Enero") in resultado
    assert ("26gmx7000.010", 2026, "Febrero") in resultado


def test_interpret_notas_ds_vacio_sin_llamar_claude():
    resultado = interpret_notas_ds([], _ClienteFake("[]"), anio_contexto=2026)
    assert resultado == []
```

- [ ] **Step 6: Run test to verify it fails**

Run: `uv run pytest pipelines/summary/tests/test_interpret.py -k notas_ds -v`
Expected: FAIL con `ImportError: cannot import name 'interpret_notas_ds'`

- [ ] **Step 7: Implement `interpret_notas_ds`**

```python
# en pipelines/summary/interpret.py
from pipelines.summary.periodos import normalizar_periodo


def interpret_notas_ds(notas, anthropic_client, anio_contexto: int):
    if not notas:
        return []
    prompt = (
        "Cada objeto tiene un 'codigo' de proyecto y una 'nota' de captura manual que indica a qué "
        "mes(es) de provisión corresponde una factura. La nota trae abreviaturas inconsistentes "
        "(ej. 'ENE26', 'feb26', 'DIC25', 'ago') y a veces montos o texto libre que debes ignorar. "
        "Para cada objeto devuelve el código y la lista de meses cubiertos, cada mes como cadena "
        "corta tipo 'ENE26' (mes de 3 letras + año de 2 dígitos si la nota lo indica). Si la nota no "
        "indica ningún mes claro, devuelve lista vacía para ese código. Responde ÚNICAMENTE un JSON "
        "array de objetos {codigo, meses}, sin explicación.\n\n"
        f"Notas: {notas}"
    )
    message = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        timeout=_TIMEOUT_SEGUNDOS,
        messages=[{"role": "user", "content": prompt}],
    )
    texto = message.content[0].text.strip()
    inicio, fin = texto.find("["), texto.rfind("]")
    datos = json.loads(texto[inicio:fin + 1]) if inicio != -1 else []
    pares = []
    for obj in datos:
        for mes_txt in obj.get("meses", []):
            normalizado = normalizar_periodo(mes_txt, anio_contexto=anio_contexto)
            if normalizado is not None:
                pares.append((obj["codigo"], normalizado[0], normalizado[1]))
    return pares
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `uv run pytest pipelines/summary/tests/test_interpret.py -k notas_ds pipelines/summary/tests/test_extract.py -k notas -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add pipelines/summary/extract.py pipelines/summary/interpret.py pipelines/summary/tests/test_extract.py pipelines/summary/tests/test_interpret.py
git commit -m "feat(summary): lectura + interpretacion de notas de celda DS a pares de cierre"
```

---

### Task 6: Lector de la hoja Concentrado (Facturación)

**Files:**
- Create: `pipelines/summary/concentrado.py`
- Test: `pipelines/summary/tests/test_concentrado.py`

**Interfaces:**
- Produces: `leer_concentrado(ruta: str) -> dict`. Devuelve `{3000: {"facturado": float, "canceladas": float}, 2000: {...}, 7000: {...}}` leyendo la hoja `Concentrado`. Layout fijo del archivo real: columnas A/B = Consulting (3000), D/E = Digital Services (7000), G/H = Engineering (2000); fila 2 = facturado bruto, fila 3 = canceladas. Si la hoja `Concentrado` no existe, devuelve `{}`.

- [ ] **Step 1: Write the failing test**

```python
# pipelines/summary/tests/test_concentrado.py
from openpyxl import Workbook

from pipelines.summary.concentrado import leer_concentrado


def _archivo_concentrado(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Concentrado"
    ws["A2"], ws["B2"] = "CONSULTING", 6050968.44
    ws["A3"], ws["B3"] = "CANCELADAS", 552468.62
    ws["D2"], ws["E2"] = "DIGITAL SERVICES", 5871693.18
    ws["D3"], ws["E3"] = "CANCELADAS", 0
    ws["G2"], ws["H2"] = "ENGINEERING", 1784778.64
    ws["G3"], ws["H3"] = "CANCELADAS", 0
    ruta = tmp_path / "fact.xlsx"
    wb.save(ruta)
    return str(ruta)


def test_leer_concentrado_mapea_unidades(tmp_path):
    resultado = leer_concentrado(_archivo_concentrado(tmp_path))
    assert resultado[3000] == {"facturado": 6050968.44, "canceladas": 552468.62}
    assert resultado[7000] == {"facturado": 5871693.18, "canceladas": 0}
    assert resultado[2000] == {"facturado": 1784778.64, "canceladas": 0}


def test_leer_concentrado_sin_hoja_devuelve_vacio(tmp_path):
    wb = Workbook()
    wb.active.title = "Detalle"
    ruta = tmp_path / "sin.xlsx"
    wb.save(ruta)
    assert leer_concentrado(str(ruta)) == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pipelines/summary/tests/test_concentrado.py -v`
Expected: FAIL con `ModuleNotFoundError: pipelines.summary.concentrado`

- [ ] **Step 3: Write minimal implementation**

```python
# pipelines/summary/concentrado.py
from openpyxl import load_workbook

_COLUMNAS_UNIDAD = {3000: ("B", "A"), 7000: ("E", "D"), 2000: ("H", "G")}


def leer_concentrado(ruta: str) -> dict:
    wb = load_workbook(ruta, data_only=True)
    if "Concentrado" not in wb.sheetnames:
        return {}
    ws = wb["Concentrado"]
    resultado = {}
    for unidad, (col_valor, _) in _COLUMNAS_UNIDAD.items():
        facturado = ws[f"{col_valor}2"].value or 0
        canceladas = ws[f"{col_valor}3"].value or 0
        resultado[unidad] = {"facturado": facturado, "canceladas": canceladas}
    return resultado
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pipelines/summary/tests/test_concentrado.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add pipelines/summary/concentrado.py pipelines/summary/tests/test_concentrado.py
git commit -m "feat(summary): lector de hoja Concentrado (facturado/canceladas por unidad)"
```

---

### Task 7: `write.py` — KPI filas 3/5/11 y orden de filas

**Files:**
- Modify: `pipelines/summary/write.py`
- Modify: `pipelines/summary/tests/test_write.py`

**Interfaces:**
- Consumes: `concentrado` (dict de Task 6), `filas` ya ordenadas (mantenidas-vivas → cerradas → nuevas) por `spec.py` (Task 8).
- Produces: `escribir_hoja_mes(ruta_origen, ruta_destino, hoja_mes_anterior, hoja_mes_nuevo, filas, concentrado, mes_actual)`. Añade dos parámetros: `concentrado: dict` y `mes_actual: str` (nombre de mes en español, para excluirlo del cálculo de la fila 11). Escribe: fila 3 (Facturacion) e I/J/K desde `concentrado`; fila 5 (C.Facturacion) canceladas; fila 11 (Prov. Antiguas por facturar) = suma de PROVISON MXN (col L, índice 11 de cada fila) de filas con `Cierre` que empieza por "Provision" y `Periodo` (índice 3) distinto de `mes_actual`, por unidad (col E índice 4). Devuelve `list[str]` de alertas (ej. Concentrado ausente).

- [ ] **Step 1: Write the failing test**

```python
# añadir a pipelines/summary/tests/test_write.py
from openpyxl import load_workbook

from pipelines.summary.write import escribir_hoja_mes


def _fila(cierre, cc, periodo, monto, proyecto="26gmx3000.001"):
    return ["", cierre, 2026, periodo, cc, "Cli", "Nom", proyecto, "MXN",
            monto, 1, monto, "", "", "", "", "", "", ""]


def test_write_puebla_kpi_filas_3_y_5_desde_concentrado(tmp_path, base_xlsm):
    concentrado = {3000: {"facturado": 6050968.44, "canceladas": 552468.62},
                   2000: {"facturado": 1784778.64, "canceladas": 0},
                   7000: {"facturado": 5871693.18, "canceladas": 298668.65}}
    destino = tmp_path / "out.xlsm"
    escribir_hoja_mes(base_xlsm, str(destino), "2026_Abr", "2026_May",
                      [_fila("Provision", 3000, "Mayo", 1000)], concentrado, "Mayo")
    ws = load_workbook(destino, data_only=False, keep_vba=True)["2026_May"]
    assert ws.cell(row=3, column=9).value == 6050968.44
    assert ws.cell(row=5, column=9).value == 552468.62
    assert ws.cell(row=3, column=11).value == 5871693.18


def test_write_fila_11_suma_provisiones_periodo_anterior_por_unidad(tmp_path, base_xlsm):
    filas = [
        _fila("Provision", 3000, "Marzo", 100),   # periodo anterior -> suma
        _fila("Provision", 3000, "Mayo", 500),     # mes actual -> NO suma
        _fila("Cancelar", 3000, "Marzo", 999),     # cancelada -> NO suma
    ]
    destino = tmp_path / "out.xlsm"
    escribir_hoja_mes(base_xlsm, str(destino), "2026_Abr", "2026_May", filas, {}, "Mayo")
    ws = load_workbook(destino, data_only=False, keep_vba=True)["2026_May"]
    assert ws.cell(row=11, column=9).value == 100
```

Nota: el fixture `base_xlsm` debe existir en `conftest.py` (workbook con hoja `2026_Abr` y tablero KPI mínimo). Si no existe, créalo en `conftest.py` regenerándolo con openpyxl (hoja `2026_Abr`, headers en fila 12, celdas B6/B7/B8 con USD/EUR/CAD). Ver Task 10 fixtures.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pipelines/summary/tests/test_write.py -k "concentrado or fila_11" -v`
Expected: FAIL (firma vieja de `escribir_hoja_mes` no acepta `concentrado`/`mes_actual`)

- [ ] **Step 3: Implement**

```python
# reemplazar escribir_hoja_mes y añadir helpers en write.py
_COL_KPI_POR_UNIDAD = {3000: 9, 2000: 10, 7000: 11}


def _poblar_facturacion_kpi(sheet, concentrado: dict) -> list[str]:
    if not concentrado:
        for col in _COL_KPI_POR_UNIDAD.values():
            sheet.cell(row=3, column=col, value=None)
            sheet.cell(row=5, column=col, value=None)
        return ["Hoja Concentrado ausente en Facturación — filas 3 y 5 del KPI quedaron en blanco."]
    for unidad, col in _COL_KPI_POR_UNIDAD.items():
        datos = concentrado.get(unidad, {})
        sheet.cell(row=3, column=col, value=datos.get("facturado"))
        sheet.cell(row=5, column=col, value=datos.get("canceladas"))
    return []


def _poblar_antiguas_por_facturar(sheet, filas: list[list], mes_actual: str) -> None:
    suma = {3000: 0.0, 2000: 0.0, 7000: 0.0}
    for fila in filas:
        cierre = (fila[1] or "").strip() if isinstance(fila[1], str) else ""
        periodo = (fila[3] or "").strip() if isinstance(fila[3], str) else ""
        unidad, monto = fila[4], fila[11]
        if cierre.startswith("Provision") and periodo != mes_actual and unidad in suma:
            if isinstance(monto, (int, float)):
                suma[unidad] += monto
    for unidad, col in _COL_KPI_POR_UNIDAD.items():
        sheet.cell(row=11, column=col, value=suma[unidad] or 0)


def escribir_hoja_mes(
    ruta_origen: str,
    ruta_destino: str,
    hoja_mes_anterior: str,
    hoja_mes_nuevo: str,
    filas: list[list],
    concentrado: dict,
    mes_actual: str,
) -> list[str]:
    wb = load_workbook(ruta_origen, keep_vba=ruta_origen.endswith(".xlsm"))
    nueva = _duplicate_sheet(wb, hoja_mes_anterior, hoja_mes_nuevo)
    _limpiar_seccion_b(nueva)

    encabezados = [
        "Cotizacion", "Cierre", "Año", "Periodo", "CC", "Cliente", "Nombre Proyecto",
        "Proyecto", "Moneda", "Provision", "T/C Provision", "PROVISION MXN", "usd",
        "MXN", "EUR", "CAD", "TOTAL MXN", "Referencia", "Comentarios",
    ]
    for col, header in enumerate(encabezados, start=1):
        nueva.cell(row=12, column=col, value=header)
    for offset, fila in enumerate(filas, start=13):
        for col, valor in enumerate(fila, start=1):
            nueva.cell(row=offset, column=col, value=valor)

    ultima_fila = 12 + len(filas) if filas else 13
    _actualizar_formulas_kpi(nueva, ultima_fila)
    alertas = _poblar_facturacion_kpi(nueva, concentrado)
    _poblar_antiguas_por_facturar(nueva, filas, mes_actual)

    wb.save(ruta_destino)
    return alertas
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pipelines/summary/tests/test_write.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pipelines/summary/write.py pipelines/summary/tests/test_write.py pipelines/summary/tests/conftest.py
git commit -m "feat(summary): KPI filas 3/5 desde Concentrado y fila 11 por unidad"
```

---

### Task 8: `spec.py` — recablear detalle, filas y alertas

**Files:**
- Modify: `pipelines/summary/spec.py`
- Modify: `pipelines/summary/tests/test_spec.py`

**Interfaces:**
- Consumes: `reconciliar` (Task 3), `escribir_hoja_mes` con firma nueva (Task 7).
- Produces: `build_summary_spec(...)` cuyo `calculate` devuelve `{"resumen": {...}, "detalle": {...}}` donde `resumen` tiene `mantenidas`/`cerradas`/`nuevas`/`alertas` y `detalle.filas` en orden mantenidas-vivas → cerradas → nuevas. `detalle` incluye `concentrado` y `mes_actual` para pasarlos a `write`. `resumen` incluye `cierres` (los del cruce, para la UI, con su `origen`).

- [ ] **Step 1: Write the failing test**

```python
# reemplazar el cuerpo relevante de pipelines/summary/tests/test_spec.py
from pipelines.summary.spec import build_summary_spec


def _estructura_minima():
    return {
        "ledger_vivo": [
            {"proyecto": "26gmx3000.001", "anio": 2026, "periodo": "Abril", "monto_mxn": 1000,
             "cc": 3000, "cliente": "Cli", "nombre_proyecto": "N", "moneda": "MXN",
             "monto_original": 1000, "tc": 1},
        ],
        "cierres": [],
        "provisiones_actuales": [
            {"proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000, "cliente": "Nuevo",
             "moneda": "MXN", "monto_original": 3000, "tc": 1},
        ],
        "concentrado": {3000: {"facturado": 1, "canceladas": 0}},
        "codigos_conocidos": {"26gmx3000.001"},
        "alertas": [],
        "hoja_mes_nuevo": "2026_May",
        "hoja_mes_anterior": "2026_Abr",
        "ruta_base": "irrelevante.xlsm",
    }


def test_spec_calculate_produce_grupos_ledger():
    spec = build_summary_spec(lambda *a, **k: {}, "o.xlsm", "d.xlsm", "2026_Abr", "2026_May")
    plan = spec.calculate(_estructura_minima(), estado_anterior=None)
    assert len(plan["resumen"]["mantenidas"]) == 1
    assert len(plan["resumen"]["nuevas"]) == 1
    assert plan["detalle"]["mes_actual"] == "Mayo"
    # orden: mantenida (Abril) primero, nueva (Mayo) al final
    assert plan["detalle"]["filas"][0][3] == "Abril"
    assert plan["detalle"]["filas"][-1][7] == "26gmx2000.005"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pipelines/summary/tests/test_spec.py::test_spec_calculate_produce_grupos_ledger -v`
Expected: FAIL (calculate espera `provisiones_mes_anterior`, KeyError o estructura vieja)

- [ ] **Step 3: Reescribir `calculate`/`write` en `spec.py`**

Reemplaza las funciones internas `calculate` y `write` (líneas 20-86) por:

```python
    def calculate(estructura: dict, estado_anterior) -> dict:
        hoja_mes_nuevo_actual = estructura.get("hoja_mes_nuevo") or hoja_mes_nuevo
        hoja_mes_anterior_actual = estructura.get("hoja_mes_anterior") or hoja_mes_anterior
        ruta_origen_actual = estructura.get("ruta_base") or ruta_origen
        anio_actual, mes_actual = hoja_mes_nuevo_actual.split("_", 1)

        resultado = reconciliar(
            ledger_vivo=estructura["ledger_vivo"],
            cierres=estructura.get("cierres", []),
            provisiones_actuales=estructura["provisiones_actuales"],
            alertas=estructura.get("alertas", []),
            codigos_conocidos=estructura.get("codigos_conocidos"),
        )

        def _fila(p: dict, cierre: str) -> list:
            moneda = p.get("moneda", "MXN")
            monto_original = p.get("monto_original", p["monto_mxn"])
            tc = p.get("tc", 1)
            anio = p.get("anio") or int(anio_actual)
            periodo = p.get("periodo") or mes_actual
            cancelada = cierre == "Cancelar"
            usd = monto_original if cancelada and moneda == "USD" else ""
            mxn = p["monto_mxn"] if cancelada and moneda == "MXN" else ""
            eur = monto_original if cancelada and moneda == "EUR" else ""
            cad = monto_original if cancelada and moneda == "CAD" else ""
            total_mxn = p["monto_mxn"] if cancelada else ""
            return ["", cierre, anio, periodo, p["cc"], p["cliente"], p.get("nombre_proyecto", ""),
                    p["proyecto"], moneda, monto_original, tc, p["monto_mxn"], usd, mxn, eur, cad,
                    total_mxn, "", ""]

        filas = (
            [_fila(p, "Provision") for p in resultado["mantenidas"]]
            + [_fila(p, "Cancelar") for p in resultado["cerradas"]]
            + [_fila(p, "Provision") for p in resultado["nuevas"]]
        )
        resultado["cierres"] = estructura.get("cierres", [])
        detalle = {
            "filas": filas,
            "counts": {
                "mantenidas": len(resultado["mantenidas"]),
                "cerradas": len(resultado["cerradas"]),
                "nuevas": len(resultado["nuevas"]),
            },
            "ruta_origen": ruta_origen_actual,
            "hoja_mes_anterior": hoja_mes_anterior_actual,
            "hoja_mes_nuevo": hoja_mes_nuevo_actual,
            "concentrado": estructura.get("concentrado", {}),
            "mes_actual": mes_actual,
        }
        return {"resumen": resultado, "detalle": detalle}

    def write(detalle: dict, archivo_destino) -> dict:
        destino = archivo_destino or ruta_destino
        alertas_kpi = escribir_hoja_mes(
            ruta_origen=detalle["ruta_origen"],
            ruta_destino=destino,
            hoja_mes_anterior=detalle["hoja_mes_anterior"],
            hoja_mes_nuevo=detalle["hoja_mes_nuevo"],
            filas=detalle["filas"],
            concentrado=detalle["concentrado"],
            mes_actual=detalle["mes_actual"],
        )
        counts = detalle["counts"]
        return {
            "archivo": destino,
            "filas_escritas": counts["mantenidas"] + counts["cerradas"] + counts["nuevas"],
            "mantenidas": counts["mantenidas"],
            "cerradas": counts["cerradas"],
            "nuevas": counts["nuevas"],
            "alertas_kpi": alertas_kpi,
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pipelines/summary/tests/test_spec.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pipelines/summary/spec.py pipelines/summary/tests/test_spec.py
git commit -m "feat(summary): spec recableado a grupos ledger + concentrado en write"
```

---

### Task 9: Orquestador — ensamblar ledger, cierres, concentrado

**Files:**
- Modify: `pipelines/summary/orquestador.py`
- Modify: `pipelines/summary/tests/test_orquestador.py`

**Interfaces:**
- Consumes: `leer_provisiones_mes_anterior` (renombrado semánticamente a ledger vivo, sin cambio de firma), `pares_cierre_facturacion` (Task 4), `leer_notas_num_factura_ds`+`interpret_notas_ds` (Task 5), `leer_concentrado` (Task 6), `cruzar_cierres` (Task 2).
- Produces: `interpretar_summary(raw_files, client, mes) -> dict` con llaves `ledger_vivo`, `cierres`, `provisiones_actuales`, `concentrado`, `codigos_conocidos`, `alertas`, `ruta_base`, `hoja_mes_anterior`, `hoja_mes_nuevo`.

- [ ] **Step 1: Write the failing test**

```python
# añadir a pipelines/summary/tests/test_orquestador.py — test de ensamblado con dobles
from pipelines.summary import orquestador


def test_interpretar_summary_ensambla_cierres_y_concentrado(monkeypatch, tmp_path):
    # dobles deterministas para no depender de Claude ni de archivos reales
    monkeypatch.setattr(orquestador, "_cargar_rows", lambda ruta, hoja=None: [["h"]])
    monkeypatch.setattr(orquestador, "leer_provisiones_mes_anterior",
                        lambda wb, hoja: [{"proyecto": "26gmx3000.001", "anio": 2026,
                                           "periodo": "Marzo", "monto_mxn": 1000, "cc": 3000,
                                           "cliente": "Cli", "nombre_proyecto": "N",
                                           "moneda": "MXN", "monto_original": 1000, "tc": 1}])
    monkeypatch.setattr(orquestador, "todos_los_codigos_conocidos", lambda wb, hojas: set())
    monkeypatch.setattr(orquestador, "leer_tipos_cambio", lambda wb, hoja: {})
    monkeypatch.setattr(orquestador, "interpret_facturacion", lambda rows, c: {"proyecto_columna": 0, "estado_columna": 1, "periodo_columna": 2})
    monkeypatch.setattr(orquestador, "pares_cierre_facturacion", lambda rows, est: [("26gmx3000.001", 2026, "Marzo")])
    monkeypatch.setattr(orquestador, "interpret_ds", lambda rows, c, mes_numero=None: {"provision_columna": 6, "codigo_columna": 3, "fila_inicio_datos": 5, "cliente_columna": 1, "nombre_columna": 2, "moneda_columna": 4})
    monkeypatch.setattr(orquestador, "extraer_ds", lambda rows, est: [])
    monkeypatch.setattr(orquestador, "leer_notas_num_factura_ds", lambda *a, **k: [])
    monkeypatch.setattr(orquestador, "interpret_notas_ds", lambda notas, c, anio_contexto: [])
    monkeypatch.setattr(orquestador, "interpret_engineering", lambda rows, c, mes_numero=None: {"codigo_columna": 0, "mes_columna": 1, "nombre_columna": 2, "fila_inicio_datos": 1})
    monkeypatch.setattr(orquestador, "extraer_engineering", lambda rows, est: [])
    monkeypatch.setattr(orquestador, "interpret_consulting", lambda rows, c: {"status_columna": 0, "project_columna": 1, "trigger_columna": 2, "monto_columna": 3})
    monkeypatch.setattr(orquestador, "extraer_consulting", lambda rows, est: [])
    monkeypatch.setattr(orquestador, "leer_concentrado", lambda ruta: {3000: {"facturado": 1, "canceladas": 0}})

    from openpyxl import Workbook
    wb = Workbook(); wb.active.title = "2026_Abr"; ruta = tmp_path / "base.xlsm"; wb.save(ruta)
    monkeypatch.setattr(orquestador, "load_workbook", lambda *a, **k: __import__("openpyxl").load_workbook(ruta))

    raw = {"base": str(ruta), "facturacion": "f", "ds": "d", "engineering": "e", "consulting": "c"}
    resultado = orquestador.interpretar_summary(raw, client=None, mes="2026-05")

    assert resultado["cierres"] == [{"codigo": "26gmx3000.001", "anio": 2026, "mes": "Marzo", "origen": "facturacion"}]
    assert resultado["concentrado"] == {3000: {"facturado": 1, "canceladas": 0}}
    assert "ledger_vivo" in resultado
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pipelines/summary/tests/test_orquestador.py -k ensambla -v`
Expected: FAIL (la salida usa `provisiones_mes_anterior`, no `ledger_vivo`/`cierres`/`concentrado`)

- [ ] **Step 3: Reescribir `interpretar_summary`**

Actualiza imports (añade `pares_cierre_facturacion`, `leer_notas_num_factura_ds`, `interpret_notas_ds`, `leer_concentrado`, `cruzar_cierres`) y reemplaza el cuerpo desde la lectura de facturación:

```python
    anio_contexto = int(mes.split("-")[0]) if mes else None
    ledger_vivo = leer_provisiones_mes_anterior(wb_base, hoja_mes_anterior)

    rows_facturacion = _cargar_rows(raw_files["facturacion"], hoja="Detalle")
    estructura_facturacion = interpret_facturacion(rows_facturacion, client)
    pares_fact = pares_cierre_facturacion(rows_facturacion, estructura_facturacion)

    rows_ds = _cargar_rows(raw_files["ds"], hoja="2026")
    estructura_ds = interpret_ds(rows_ds, client, mes_numero=mes_numero)
    ds_actuales = extraer_ds(rows_ds, estructura_ds)
    notas_ds = leer_notas_num_factura_ds(
        raw_files["ds"],
        num_factura_col=estructura_ds["provision_columna"] + 1,
        codigo_col=estructura_ds["codigo_columna"],
        fila_inicio=estructura_ds["fila_inicio_datos"],
    )
    pares_notas = interpret_notas_ds(notas_ds, client, anio_contexto=anio_contexto)

    rows_engineering = _cargar_rows(raw_files["engineering"], hoja="Hoja1")
    estructura_engineering = interpret_engineering(rows_engineering, client, mes_numero=mes_numero)
    engineering_actuales = extraer_engineering(rows_engineering, estructura_engineering)

    rows_consulting = _cargar_rows(raw_files["consulting"], hoja=mes.replace("-", ".") if mes else None)
    estructura_consulting = interpret_consulting(rows_consulting, client)
    consulting_actuales = extraer_consulting(rows_consulting, estructura_consulting)

    cierres, alertas_cierre = cruzar_cierres(pares_fact, pares_notas)
    concentrado = leer_concentrado(raw_files["facturacion"])

    provisiones_convertidas, alertas_conversion = _convertir_a_mxn(
        ds_actuales + engineering_actuales + consulting_actuales, tipos_cambio
    )
    provisiones_actuales, alertas_sospechosos = _separar_sospechosos(provisiones_convertidas)
    alertas = alertas_conversion + alertas_sospechosos + alertas_cierre

    return {
        "ledger_vivo": ledger_vivo,
        "cierres": cierres,
        "provisiones_actuales": provisiones_actuales,
        "concentrado": concentrado,
        "codigos_conocidos": codigos_conocidos,
        "alertas": alertas,
        "ruta_base": raw_files["base"],
        "hoja_mes_anterior": hoja_mes_anterior,
        "hoja_mes_nuevo": _hoja_desde_mes_iso(mes) if mes else None,
    }
```

Deja intactas las líneas previas (`wb_base`, `hojas`, `hoja_mes_anterior`, `codigos_conocidos`, `tipos_cambio`, `mes_numero`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest pipelines/summary/tests/test_orquestador.py -v`
Expected: PASS (ajustar los tests viejos que esperaban `provisiones_mes_anterior` en la salida — renombrar la aserción a `ledger_vivo`)

- [ ] **Step 5: Commit**

```bash
git add pipelines/summary/orquestador.py pipelines/summary/tests/test_orquestador.py
git commit -m "feat(summary): orquestador ensambla ledger, cierres cruzados y concentrado"
```

---

### Task 10: Fixtures, end-to-end y suite completa

**Files:**
- Modify: `pipelines/summary/tests/conftest.py`
- Modify: `pipelines/summary/tests/make_fixtures.py` (si existe; si no, ajustar el generador donde esté)
- Modify: `pipelines/summary/tests/test_spec_end_to_end.py`

**Interfaces:**
- Consumes: todo lo anterior.
- Produces: fixture `base_xlsm` (path a un `.xlsm` con hoja `2026_Abr`, headers fila 12, tablero KPI mínimo con B6/B7/B8=USD/EUR/CAD) y actualización del e2e para el flujo mantenidas/cerradas/nuevas.

- [ ] **Step 1: Añadir/verificar fixture `base_xlsm` en `conftest.py`**

```python
# en pipelines/summary/tests/conftest.py
import pytest
from openpyxl import Workbook


@pytest.fixture
def base_xlsm(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "2026_Abr"
    ws.cell(row=6, column=2, value="USD")
    ws.cell(row=7, column=2, value="EUR")
    ws.cell(row=8, column=2, value="CAD")
    headers = ["Cotizacion", "Cierre", "Año", "Periodo", "CC", "Cliente", "Nombre Proyecto",
               "Proyecto", "Moneda", "Provision", "T/C Provision", "PROVISION MXN", "usd",
               "MXN", "EUR", "CAD", "TOTAL MXN", "Referencia", "Comentarios"]
    for col, h in enumerate(headers, start=1):
        ws.cell(row=12, column=col, value=h)
    ruta = tmp_path / "base.xlsm"
    wb.save(ruta)
    return str(ruta)
```

- [ ] **Step 2: Actualizar el e2e**

En `test_spec_end_to_end.py`, cambia la estructura de entrada a las llaves nuevas (`ledger_vivo`, `cierres`, `provisiones_actuales`, `concentrado`) y las aserciones de salida (`resultado["mantenidas"]`, `resultado["cerradas"]`, `resultado["nuevas"]`, `resultado["alertas_kpi"]`). Verifica que una fila del ledger no cerrada aparece en la hoja escrita con su `Cierre=Provision` intacto y una nueva con `Periodo` = mes actual.

- [ ] **Step 3: Run the full suite**

Run: `uv run pytest -q`
Expected: PASS — toda la suite verde. Si algún test viejo de `test_spec.py`/`test_write.py`/`test_orquestador.py` sigue con la firma vieja, actualízalo a la nueva.

- [ ] **Step 4: Commit**

```bash
git add pipelines/summary/tests/
git commit -m "test(summary): fixtures base_xlsm y e2e para modelo ledger"
```

---

### Task 11: Frontend `Resumen.jsx` — layout ledger

**Files:**
- Modify: `frontend/src/components/Resumen.jsx`
- Modify: `frontend/src/App.jsx` (si mapea counts del reporte)

**Interfaces:**
- Consumes: el `resumen` del plan (`mantenidas`, `nuevas`, `cerradas`, `cierres`, `alertas`).
- Produces: pantalla con secciones "Se mantienen" (colapsable, solo conteo por defecto), "Nuevas del mes" (con la tarjeta existente de nombrar códigos), "Cierres detectados" (tabla con badge de origen `Facturación`/`Notas DS`/`Ambas`), "Alertas" (lista). Contadores del encabezado: Se mantienen / Nuevas / Cierres / Alertas.

- [ ] **Step 1: Leer el componente actual y su consumo de datos**

Run: revisar `frontend/src/components/Resumen.jsx` para ver cómo lee hoy `activas`/`nuevas`/`canceladas` y la tarjeta de nombrar.

- [ ] **Step 2: Reemplazar las secciones**

Sustituir la sección "Activas" por "Se mantienen" (colapsable con conteo). Añadir sección "Cierres detectados" que mapea `resumen.cierres` a filas `{codigo, mes, origen}` con un badge de color por origen. Conservar intacta la tarjeta "Códigos nuevos sin nombre de cliente" (Guardar y continuar / Continuar sin nombrar). Mantener "Alertas".

Mapa de badge de origen:
```jsx
const ORIGEN_BADGE = {
  ambas: { label: "Ambas", clase: "bg-emerald-100 text-emerald-700" },
  facturacion: { label: "Facturación", clase: "bg-sky-100 text-sky-700" },
  notas_ds: { label: "Notas DS", clase: "bg-amber-100 text-amber-700" },
};
```

- [ ] **Step 3: Verificar en Docker**

Run: `docker compose up -d --build` y abrir `http://localhost`, procesar Summary con los archivos de prueba de Mayo; confirmar que las 4 secciones y los badges de origen se ven correctamente.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Resumen.jsx frontend/src/App.jsx
git commit -m "feat(frontend): Resumen con secciones ledger (mantenidas/nuevas/cierres/alertas)"
```

---

### Task 12: Validación con datos reales de Mayo 2026

**Files:**
- Ninguno de producción — validación manual contra el Summary real.

- [ ] **Step 1: Correr el pipeline real** con `ANTHROPIC_API_KEY`, el archivo base sin la hoja de Mayo (para que Abril sea el mes anterior) + los 4 archivos de fuente de Mayo en `...\P3\AGENTE\`, generando `Summary_2026_May` nuevo.

- [ ] **Step 2: Comparar celda a celda** el KPI generado contra el `Summary_2026_May.xlsm` real:
  - Filas 3 y 5 deben cuadrar exacto con la hoja `Concentrado` de Facturación.
  - Fila 11: DS (K11) debe cuadrar exacto; documentar la diferencia esperada en Consulting (I11) y Engineering (J11=0) como pendiente de criterio con P3.
  - Cierres: revisar que cada `Cancelar` aplicado corresponde a una factura real de ese `(código, periodo)`.

- [ ] **Step 3: Registrar hallazgos** en el memory del proyecto y decidir con Luis qué queda pendiente de P3 (criterio exacto de fila 11 en Consulting/Engineering).

---

## Self-Review

**Spec coverage:**
- Sección 1 (cierre cruzado) → Tasks 1, 2, 4, 5, 9. ✓
- Sección 2 (mantener + nuevas) → Tasks 3, 8. ✓
- Sección 3 (write + KPI 3/5/11) → Tasks 6, 7. ✓
- Sección 4 (frontend) → Task 11. ✓
- Validación → Task 12. ✓

**Placeholder scan:** sin TBD/TODO; todo el código concreto. La única incertidumbre declarada (fila 11 Consulting/Engineering) está marcada explícitamente como pendiente de P3, no como placeholder de implementación.

**Type consistency:** `reconciliar` devuelve `mantenidas`/`cerradas`/`nuevas`/`alertas` (Task 3) y se consume así en spec (Task 8) y write cuenta con `mantenidas`/`cerradas`/`nuevas` (Task 7). `cruzar_cierres` devuelve dicts `{codigo, anio, mes, origen}` (Task 2) consumidos por clave `(codigo, anio, mes)` en reconciliar (Task 3) y por `origen` en el frontend (Task 11). `normalizar_periodo` devuelve `(anio, mes)` usado en Tasks 4, 5. Consistente.

## Notas de proceso

- Repo actual: commit `8a99a4e`, rama `feat/interfaz-subida`, local sin push (patrón del proyecto — no pushear salvo que Luis lo pida).
- Confidencialidad: los archivos reales de `...\P3\AGENTE\` no se commitean; la validación de Task 12 es local.
