# Agente Financiero P3 — Backend `core/` + Pipeline Summary — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the backend (no frontend yet) for the P3 financial agent platform: the shared `core/` plumbing (`PipelineSpec` contract, lock, audit log, generic `/procesar` + `/confirmar` API) and the first real pipeline, Summary, wired into it end-to-end against synthetic fixture files.

**Architecture:** FastAPI service. `core/` knows nothing about Summary's business logic — it only calls the 4 functions declared by whichever `PipelineSpec` is registered (`sources`, `interpret`, `calculate`, `write`). Plan-in-progress and per-month locks are persisted in a local SQLite file so a service restart between `/procesar` and `/confirmar` doesn't lose state. Drive access and the Anthropic client are both injected as parameters into the functions that need them, so every test runs offline against fakes — no real Drive credentials or API key required to run the test suite.

**Tech Stack:** Python 3.12, `uv` (dependency management), FastAPI, `openpyxl`, `anthropic` SDK (`claude-opus-4-8`), `google-api-python-client` + `google-auth` (Drive, service account), `pytest`.

## Global Constraints

- Never commit real P3 data (montos, clientes, archivos completos) — all fixtures are synthetic, invented data only (spec section 12 / repo `CLAUDE.md`).
- `core/` never imports from `pipelines/<name>/` directly — it only calls through the `PipelineSpec` it receives from the registry.
- `interpret` functions never return calculated money values — only structure (header row, column indices, currency, which rows are projects). All arithmetic lives in `calculate`.
- `write` never touches rows 1–11 of the Summary sheet (tablero KPI).
- Every function that talks to an external service (Drive API, Anthropic API) takes the client as a parameter — no module-level client construction — so tests can inject a fake.

---

## File Structure

```
agente-financiero-ptres/
├── pyproject.toml
├── main.py                          # uvicorn entrypoint, mounts core.api
├── core/
│   ├── __init__.py
│   ├── db.py                        # SQLite schema + connection helper
│   ├── lock.py                      # acquire/release/check lock per (pipeline, mes)
│   ├── audit_log.py                 # log_write(...)
│   ├── pipeline_spec.py             # PipelineSpec, Plan dataclasses
│   ├── registry.py                  # register(spec) / get(name)
│   ├── drive_client.py              # find_file/download_file/upload_file
│   └── api.py                       # FastAPI router: /procesar, /confirmar, /rechazar
├── pipelines/
│   └── summary/
│       ├── __init__.py
│       ├── interpret.py             # 4 interpreters (DS, Engineering, Consulting, Facturación)
│       ├── calculate.py             # reconciliation + money calculation
│       ├── write.py                 # openpyxl writer
│       ├── spec.py                  # SummaryPipelineSpec, registers with core
│       └── tests/
│           ├── fixtures/
│           │   ├── make_fixtures.py      # script that generates the .xlsx/.xlsm below
│           │   ├── summary_abril.xlsm
│           │   ├── facturacion_mayo.xlsx
│           │   ├── provisiones_ds_mayo.xlsx
│           │   ├── provisiones_engineering_mayo.xlsx
│           │   └── overview_consulting_mayo.xlsx
│           ├── test_interpret.py
│           ├── test_calculate.py
│           ├── test_write.py
│           └── test_spec_end_to_end.py
└── tests/
    ├── conftest.py
    ├── test_db.py
    ├── test_lock.py
    ├── test_audit_log.py
    └── test_api.py
```

---

### Task 1: Project scaffolding

**Files:**
- Create: `agente-financiero-ptres/pyproject.toml`
- Create: `agente-financiero-ptres/main.py`
- Create: `agente-financiero-ptres/core/__init__.py`
- Create: `agente-financiero-ptres/core/api.py`
- Create: `agente-financiero-ptres/tests/conftest.py`
- Create: `agente-financiero-ptres/tests/test_api.py`

**Interfaces:**
- Produces: `core.api.app` (FastAPI instance), `GET /health` → `{"status": "ok"}`.

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "agente-financiero-ptres"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "openpyxl>=3.1",
    "anthropic>=0.40",
    "google-api-python-client>=2.150",
    "google-auth>=2.35",
    "pydantic>=2.9",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "httpx>=0.27",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["core", "pipelines"]
```

- [ ] **Step 2: Run `uv sync` to create the lockfile and virtualenv**

Run (from `agente-financiero-ptres/`): `uv sync`
Expected: creates `.venv/` and `uv.lock`, no errors.

- [ ] **Step 3: Create minimal `core/__init__.py` and `core/api.py`**

`core/__init__.py`:
```python
```

`core/api.py`:
```python
from fastapi import FastAPI

app = FastAPI(title="Agente Financiero P3")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Create `main.py`**

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run("core.api:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 5: Write the failing test**

`tests/conftest.py`:
```python
import pytest
from fastapi.testclient import TestClient

from core.api import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
```

`tests/test_api.py`:
```python
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_api.py -v`
Expected: `test_health PASSED`

- [ ] **Step 7: Commit**

```bash
git add agente-financiero-ptres/pyproject.toml agente-financiero-ptres/uv.lock agente-financiero-ptres/main.py agente-financiero-ptres/core/__init__.py agente-financiero-ptres/core/api.py agente-financiero-ptres/tests/conftest.py agente-financiero-ptres/tests/test_api.py
git commit -m "feat(core): scaffold FastAPI service with health check"
```

---

### Task 2: `core/db.py` — SQLite schema and connection helper

**Files:**
- Create: `core/db.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Produces:
  - `get_connection(db_path: str) -> sqlite3.Connection`
  - `init_db(conn: sqlite3.Connection) -> None` — creates `plans` and `locks` tables if missing.
  - Schema: `plans(token TEXT PRIMARY KEY, pipeline TEXT, mes TEXT, plan_json TEXT, created_at TEXT)`
  - Schema: `locks(pipeline TEXT, mes TEXT, token TEXT, locked_by TEXT, created_at TEXT, PRIMARY KEY (pipeline, mes))`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_db.py
import sqlite3

from core.db import get_connection, init_db


def test_init_db_creates_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = get_connection(db_path)
    init_db(conn)

    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {"plans", "locks"}.issubset(tables)


def test_get_connection_returns_row_factory_dict(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = get_connection(db_path)
    init_db(conn)
    conn.execute(
        "INSERT INTO plans (token, pipeline, mes, plan_json, created_at) VALUES (?, ?, ?, ?, ?)",
        ("tok-1", "summary", "2026_May", "{}", "2026-06-24T00:00:00"),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM plans WHERE token = ?", ("tok-1",)).fetchone()
    assert row["pipeline"] == "summary"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_db.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.db'`

- [ ] **Step 3: Write implementation**

```python
# core/db.py
import sqlite3


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS plans (
            token TEXT PRIMARY KEY,
            pipeline TEXT NOT NULL,
            mes TEXT NOT NULL,
            plan_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS locks (
            pipeline TEXT NOT NULL,
            mes TEXT NOT NULL,
            token TEXT NOT NULL,
            locked_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (pipeline, mes)
        )
        """
    )
    conn.commit()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_db.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add agente-financiero-ptres/core/db.py agente-financiero-ptres/tests/test_db.py
git commit -m "feat(core): add SQLite schema for plans and locks"
```

---

### Task 3: `core/lock.py` — per-month lock

**Files:**
- Create: `core/lock.py`
- Test: `tests/test_lock.py`

**Interfaces:**
- Consumes: `core.db.get_connection`, `core.db.init_db` (Task 2).
- Produces:
  - `class LockHeldError(Exception)` — `.locked_by: str` attribute.
  - `acquire_lock(conn: sqlite3.Connection, pipeline: str, mes: str, token: str, locked_by: str) -> None` — raises `LockHeldError` if already locked by someone else for that `(pipeline, mes)`.
  - `release_lock(conn: sqlite3.Connection, pipeline: str, mes: str) -> None`
  - `get_lock_holder(conn: sqlite3.Connection, pipeline: str, mes: str) -> str | None`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_lock.py
import pytest

from core.db import get_connection, init_db
from core.lock import LockHeldError, acquire_lock, get_lock_holder, release_lock


@pytest.fixture
def conn(tmp_path):
    c = get_connection(str(tmp_path / "test.db"))
    init_db(c)
    return c


def test_acquire_lock_when_free(conn):
    acquire_lock(conn, "summary", "2026_May", token="tok-1", locked_by="luis")
    assert get_lock_holder(conn, "summary", "2026_May") == "luis"


def test_acquire_lock_when_taken_raises(conn):
    acquire_lock(conn, "summary", "2026_May", token="tok-1", locked_by="luis")

    with pytest.raises(LockHeldError) as exc_info:
        acquire_lock(conn, "summary", "2026_May", token="tok-2", locked_by="oswaldo")

    assert exc_info.value.locked_by == "luis"


def test_release_lock_frees_it(conn):
    acquire_lock(conn, "summary", "2026_May", token="tok-1", locked_by="luis")
    release_lock(conn, "summary", "2026_May")
    assert get_lock_holder(conn, "summary", "2026_May") is None

    acquire_lock(conn, "summary", "2026_May", token="tok-2", locked_by="oswaldo")
    assert get_lock_holder(conn, "summary", "2026_May") == "oswaldo"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_lock.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.lock'`

- [ ] **Step 3: Write implementation**

```python
# core/lock.py
import sqlite3
from datetime import datetime, timezone


class LockHeldError(Exception):
    def __init__(self, locked_by: str):
        self.locked_by = locked_by
        super().__init__(f"Locked by {locked_by}")


def get_lock_holder(conn: sqlite3.Connection, pipeline: str, mes: str) -> str | None:
    row = conn.execute(
        "SELECT locked_by FROM locks WHERE pipeline = ? AND mes = ?", (pipeline, mes)
    ).fetchone()
    return row["locked_by"] if row else None


def acquire_lock(
    conn: sqlite3.Connection, pipeline: str, mes: str, token: str, locked_by: str
) -> None:
    holder = get_lock_holder(conn, pipeline, mes)
    if holder is not None:
        raise LockHeldError(holder)

    conn.execute(
        "INSERT INTO locks (pipeline, mes, token, locked_by, created_at) VALUES (?, ?, ?, ?, ?)",
        (pipeline, mes, token, locked_by, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def release_lock(conn: sqlite3.Connection, pipeline: str, mes: str) -> None:
    conn.execute("DELETE FROM locks WHERE pipeline = ? AND mes = ?", (pipeline, mes))
    conn.commit()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_lock.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add agente-financiero-ptres/core/lock.py agente-financiero-ptres/tests/test_lock.py
git commit -m "feat(core): add per-month lock with held-by error"
```

---

### Task 4: `core/audit_log.py` — write history

**Files:**
- Create: `core/audit_log.py`
- Test: `tests/test_audit_log.py`

**Interfaces:**
- Consumes: `core.db.get_connection`, `core.db.init_db` (Task 2).
- Produces:
  - `log_write(conn, pipeline: str, mes: str, fila: str, valor_anterior: str | None, valor_nuevo: str) -> None`
  - `get_log(conn, pipeline: str, mes: str) -> list[dict]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_audit_log.py
import pytest

from core.audit_log import get_log, log_write
from core.db import get_connection, init_db


@pytest.fixture
def conn(tmp_path):
    c = get_connection(str(tmp_path / "test.db"))
    init_db(c)
    return c


def test_log_write_and_get_log(conn):
    log_write(conn, "summary", "2026_May", fila="26gmx3000.104", valor_anterior="1000.00", valor_nuevo="1200.00")
    log_write(conn, "summary", "2026_May", fila="26gmx2000.007", valor_anterior=None, valor_nuevo="500.00")

    entries = get_log(conn, "summary", "2026_May")

    assert len(entries) == 2
    assert entries[0]["fila"] == "26gmx3000.104"
    assert entries[0]["valor_anterior"] == "1000.00"
    assert entries[1]["valor_anterior"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_audit_log.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.audit_log'`

- [ ] **Step 3: Write implementation**

```python
# core/audit_log.py
import sqlite3
from datetime import datetime, timezone


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline TEXT NOT NULL,
            mes TEXT NOT NULL,
            fila TEXT NOT NULL,
            valor_anterior TEXT,
            valor_nuevo TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def log_write(
    conn: sqlite3.Connection,
    pipeline: str,
    mes: str,
    fila: str,
    valor_anterior: str | None,
    valor_nuevo: str,
) -> None:
    _ensure_table(conn)
    conn.execute(
        "INSERT INTO audit_log (pipeline, mes, fila, valor_anterior, valor_nuevo, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (pipeline, mes, fila, valor_anterior, valor_nuevo, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def get_log(conn: sqlite3.Connection, pipeline: str, mes: str) -> list[dict]:
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT fila, valor_anterior, valor_nuevo, created_at FROM audit_log "
        "WHERE pipeline = ? AND mes = ? ORDER BY id ASC",
        (pipeline, mes),
    ).fetchall()
    return [dict(row) for row in rows]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_audit_log.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add agente-financiero-ptres/core/audit_log.py agente-financiero-ptres/tests/test_audit_log.py
git commit -m "feat(core): add audit log for written rows"
```

---

### Task 5: `core/pipeline_spec.py` + `core/registry.py`

**Files:**
- Create: `core/pipeline_spec.py`
- Create: `core/registry.py`
- Test: `tests/test_registry.py`

**Interfaces:**
- Produces:
  - `@dataclass class PipelineSpec: name: str; sources: list[str]; interpret: Callable; calculate: Callable; write: Callable`
  - `@dataclass class Plan: token: str; pipeline: str; mes: str; resumen: dict; detalle: dict` — `resumen` is what gets shown to the user, `detalle` is the full data `write` will need.
  - `register(spec: PipelineSpec) -> None`
  - `get(name: str) -> PipelineSpec` — raises `KeyError` if not registered.
  - `clear_registry() -> None` — test helper to reset global state between tests.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_registry.py
import pytest

from core.pipeline_spec import PipelineSpec
from core.registry import clear_registry, get, register


@pytest.fixture(autouse=True)
def reset_registry():
    clear_registry()
    yield
    clear_registry()


def _dummy(*args, **kwargs):
    return {}


def test_register_and_get():
    spec = PipelineSpec(name="dummy", sources=["a.xlsx"], interpret=_dummy, calculate=_dummy, write=_dummy)
    register(spec)

    assert get("dummy") is spec


def test_get_unknown_raises_key_error():
    with pytest.raises(KeyError):
        get("does-not-exist")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_registry.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.pipeline_spec'`

- [ ] **Step 3: Write implementation**

```python
# core/pipeline_spec.py
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class PipelineSpec:
    name: str
    sources: list[str]
    interpret: Callable[..., Any]
    calculate: Callable[..., Any]
    write: Callable[..., Any]


@dataclass
class Plan:
    token: str
    pipeline: str
    mes: str
    resumen: dict
    detalle: dict
```

```python
# core/registry.py
from core.pipeline_spec import PipelineSpec

_registry: dict[str, PipelineSpec] = {}


def register(spec: PipelineSpec) -> None:
    _registry[spec.name] = spec


def get(name: str) -> PipelineSpec:
    return _registry[name]


def clear_registry() -> None:
    _registry.clear()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_registry.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add agente-financiero-ptres/core/pipeline_spec.py agente-financiero-ptres/core/registry.py agente-financiero-ptres/tests/test_registry.py
git commit -m "feat(core): add PipelineSpec contract and registry"
```

---

### Task 6: `core/drive_client.py` — Drive file lookup, download, upload

**Files:**
- Create: `core/drive_client.py`
- Test: `tests/test_drive_client.py`

**Interfaces:**
- Produces:
  - `class FileNotFoundOnDrive(Exception)` — `.pattern: str`
  - `find_file_id(service, name_pattern: str, folder_id: str) -> str` — lists files in `folder_id`, matches by exact name; raises `FileNotFoundOnDrive` if none match.
  - `download_file(service, file_id: str) -> bytes`
  - `upload_file(service, file_id: str, content: bytes) -> None`
- The real `service` is a `googleapiclient.discovery.Resource` built elsewhere (out of scope for this plan — section 14 of the Summary spec, Drive folder/auth still pending with the client). These 3 functions only depend on `service.files()` returning an object with `.list()`, `.get_media()` and `.update()` — exactly what a `MagicMock` can stand in for in tests, so no real Drive credentials are needed here.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_drive_client.py
from unittest.mock import MagicMock

import pytest

from core.drive_client import FileNotFoundOnDrive, download_file, find_file_id, upload_file


def test_find_file_id_matches_exact_name():
    service = MagicMock()
    service.files().list().execute.return_value = {
        "files": [{"id": "abc123", "name": "2026_Summary_provision.xlsm"}]
    }

    file_id = find_file_id(service, "2026_Summary_provision.xlsm", folder_id="folder-1")

    assert file_id == "abc123"


def test_find_file_id_raises_when_missing():
    service = MagicMock()
    service.files().list().execute.return_value = {"files": []}

    with pytest.raises(FileNotFoundOnDrive) as exc_info:
        find_file_id(service, "no_existe.xlsx", folder_id="folder-1")

    assert exc_info.value.pattern == "no_existe.xlsx"


def test_download_file_returns_bytes():
    service = MagicMock()
    service.files().get_media().execute.return_value = b"contenido-binario"

    content = download_file(service, "abc123")

    assert content == b"contenido-binario"


def test_upload_file_calls_update():
    service = MagicMock()

    upload_file(service, "abc123", b"contenido-nuevo")

    service.files().update.assert_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_drive_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.drive_client'`

- [ ] **Step 3: Write implementation**

```python
# core/drive_client.py
import io

from googleapiclient.http import MediaIoBaseUpload


class FileNotFoundOnDrive(Exception):
    def __init__(self, pattern: str):
        self.pattern = pattern
        super().__init__(f"No file matching '{pattern}' found on Drive")


def find_file_id(service, name_pattern: str, folder_id: str) -> str:
    response = (
        service.files()
        .list(q=f"'{folder_id}' in parents and name = '{name_pattern}'", fields="files(id, name)")
        .execute()
    )
    files = response.get("files", [])
    if not files:
        raise FileNotFoundOnDrive(name_pattern)
    return files[0]["id"]


def download_file(service, file_id: str) -> bytes:
    return service.files().get_media(fileId=file_id).execute()


def upload_file(service, file_id: str, content: bytes) -> None:
    media = MediaIoBaseUpload(io.BytesIO(content), mimetype="application/octet-stream")
    service.files().update(fileId=file_id, media_body=media).execute()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_drive_client.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add agente-financiero-ptres/core/drive_client.py agente-financiero-ptres/tests/test_drive_client.py
git commit -m "feat(core): add Drive find/download/upload wrappers"
```

---

### Task 7: `core/api.py` — generic `/procesar`, `/confirmar`, `/rechazar`

**Files:**
- Modify: `core/api.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `core.db` (Task 2), `core.lock` (Task 3), `core.audit_log` (Task 4), `core.registry`/`core.pipeline_spec` (Task 5).
- Produces:
  - `POST /procesar/{pipeline}` body `{"mes": str, "usuario": str}` → `200 {"token": str, "resumen": dict}` or `409 {"detail": "Locked by <usuario>"}`.
  - `POST /confirmar/{pipeline}` body `{"token": str}` → `200 {"reporte": dict}` or `404` if token unknown.
  - `POST /rechazar/{pipeline}` body `{"token": str}` → `200 {"status": "rechazado"}`.
  - This task does NOT wire a real pipeline — it registers a small in-test fake `PipelineSpec` to validate the generic orchestration in isolation, exactly the way Task 11 will later validate it again with the real Summary spec.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_api.py (extend existing file)
import pytest

from core.pipeline_spec import PipelineSpec
from core.registry import clear_registry, register


@pytest.fixture(autouse=True)
def fake_pipeline(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTE_DB_PATH", str(tmp_path / "test.db"))
    clear_registry()

    def fake_interpret(raw_files):
        return {"raw": raw_files}

    def fake_calculate(estructura, estado_anterior):
        return {
            "resumen": {"nuevas": [{"proyecto": "X-1", "monto_mxn": 100}]},
            "detalle": {"filas": [{"proyecto": "X-1", "monto_mxn": 100}]},
        }

    def fake_write(plan_detalle, archivo_destino):
        return {"archivo": "fake.xlsm", "filas_escritas": len(plan_detalle["filas"])}

    register(
        PipelineSpec(
            name="fake", sources=["fuente.xlsx"], interpret=fake_interpret,
            calculate=fake_calculate, write=fake_write,
        )
    )
    yield
    clear_registry()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_procesar_then_confirmar(client):
    response = client.post("/procesar/fake", json={"mes": "2026_May", "usuario": "luis"})
    assert response.status_code == 200
    body = response.json()
    assert "token" in body
    assert body["resumen"]["nuevas"][0]["proyecto"] == "X-1"

    response = client.post("/confirmar/fake", json={"token": body["token"]})
    assert response.status_code == 200
    assert response.json()["reporte"]["filas_escritas"] == 1


def test_procesar_locked_returns_409(client):
    first = client.post("/procesar/fake", json={"mes": "2026_May", "usuario": "luis"})
    assert first.status_code == 200

    second = client.post("/procesar/fake", json={"mes": "2026_May", "usuario": "oswaldo"})
    assert second.status_code == 409
    assert "luis" in second.json()["detail"]


def test_rechazar_frees_lock(client):
    first = client.post("/procesar/fake", json={"mes": "2026_May", "usuario": "luis"})
    token = first.json()["token"]

    rechazar = client.post("/rechazar/fake", json={"token": token})
    assert rechazar.status_code == 200

    second = client.post("/procesar/fake", json={"mes": "2026_May", "usuario": "oswaldo"})
    assert second.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api.py -v`
Expected: FAIL — `/procesar/fake` returns 404 (route doesn't exist yet).

- [ ] **Step 3: Write implementation**

```python
# core/api.py
import json
import os
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core import audit_log, registry
from core.db import get_connection, init_db
from core.lock import LockHeldError, acquire_lock, release_lock

app = FastAPI(title="Agente Financiero P3")


def _db_path() -> str:
    return os.environ.get("AGENTE_DB_PATH", "agente.db")


def _conn():
    conn = get_connection(_db_path())
    init_db(conn)
    return conn


class ProcesarRequest(BaseModel):
    mes: str
    usuario: str


class TokenRequest(BaseModel):
    token: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/procesar/{pipeline}")
def procesar(pipeline: str, body: ProcesarRequest):
    spec = registry.get(pipeline)
    conn = _conn()
    token = str(uuid.uuid4())

    try:
        acquire_lock(conn, pipeline, body.mes, token=token, locked_by=body.usuario)
    except LockHeldError as exc:
        raise HTTPException(status_code=409, detail=f"Locked by {exc.locked_by}")

    raw_files = {source: None for source in spec.sources}
    estructura = spec.interpret(raw_files)
    plan = spec.calculate(estructura, estado_anterior=None)

    conn.execute(
        "INSERT INTO plans (token, pipeline, mes, plan_json, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
        (token, pipeline, body.mes, json.dumps(plan)),
    )
    conn.commit()

    return {"token": token, "resumen": plan["resumen"]}


@app.post("/confirmar/{pipeline}")
def confirmar(pipeline: str, body: TokenRequest):
    spec = registry.get(pipeline)
    conn = _conn()

    row = conn.execute(
        "SELECT mes, plan_json FROM plans WHERE token = ? AND pipeline = ?", (body.token, pipeline)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Token not found")

    plan = json.loads(row["plan_json"])
    reporte = spec.write(plan["detalle"], archivo_destino=None)

    audit_log.log_write(
        conn, pipeline, row["mes"], fila="*", valor_anterior=None, valor_nuevo=json.dumps(reporte)
    )
    release_lock(conn, pipeline, row["mes"])
    conn.execute("DELETE FROM plans WHERE token = ?", (body.token,))
    conn.commit()

    return {"reporte": reporte}


@app.post("/rechazar/{pipeline}")
def rechazar(pipeline: str, body: TokenRequest):
    conn = _conn()
    row = conn.execute(
        "SELECT mes FROM plans WHERE token = ? AND pipeline = ?", (body.token, pipeline)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Token not found")

    release_lock(conn, pipeline, row["mes"])
    conn.execute("DELETE FROM plans WHERE token = ?", (body.token,))
    conn.commit()

    return {"status": "rechazado"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_api.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add agente-financiero-ptres/core/api.py agente-financiero-ptres/tests/test_api.py
git commit -m "feat(core): wire generic /procesar, /confirmar, /rechazar against PipelineSpec"
```

---

### Task 8: Synthetic fixtures for the Summary pipeline

**Files:**
- Create: `pipelines/summary/tests/fixtures/make_fixtures.py`
- Create (generated by running the script): `pipelines/summary/tests/fixtures/summary_abril.xlsm`, `facturacion_mayo.xlsx`, `provisiones_ds_mayo.xlsx`, `provisiones_engineering_mayo.xlsx`, `overview_consulting_mayo.xlsx`

**Interfaces:**
- Produces: 5 fixture files on disk, all with invented data, matching the real column/sheet layout documented in `pipelines/summary/ESPECIFICACION.md` section 2.

- [ ] **Step 1: Write the fixture-generation script**

```python
# pipelines/summary/tests/fixtures/make_fixtures.py
"""Generates synthetic .xlsx/.xlsm fixtures with the real column layout but invented data.
Run with: uv run python pipelines/summary/tests/fixtures/make_fixtures.py
"""
from pathlib import Path

from openpyxl import Workbook

FIXTURES_DIR = Path(__file__).parent


def make_summary_abril() -> None:
    wb = Workbook()
    sheet = wb.active
    sheet.title = "2026_Abr"

    for row in range(1, 12):
        sheet.cell(row=row, column=1, value=f"KPI fila {row}")

    headers = ["Cotizacion", "Cierre", "Año", "Periodo", "CC", "Cliente", "Nombre Proyecto",
               "Proyecto", "Moneda", "Provision", "T/C Provision", "PROVISION MXN", "usd",
               "MXN", "EUR", "CAD", "TOTAL MXN", "Referencia", "Comentarios"]
    for col, header in enumerate(headers, start=1):
        sheet.cell(row=12, column=col, value=header)

    rows = [
        ["Q-1", "Provision", 2026, "Abril", 3000, "Cliente Uno", "Proyecto Uno",
         "26gmx3000.001", "USD", 1000, 17.95, 17950, 1000, 0, 0, 0, 17950, "", ""],
        ["Q-2", "Provision", 2026, "Abril", 7000, "Cliente Dos", "Proyecto Dos",
         "26gmx7000.002", "MXN", 5000, 1, 5000, 0, 5000, 0, 0, 5000, "", ""],
    ]
    for offset, row_values in enumerate(rows, start=13):
        for col, value in enumerate(row_values, start=1):
            sheet.cell(row=offset, column=col, value=value)

    wb.save(FIXTURES_DIR / "summary_abril.xlsm")


def make_facturacion_mayo() -> None:
    wb = Workbook()
    detalle = wb.active
    detalle.title = "Detalle"
    detalle.append(["Proyecto", "Estado", "Monto"])
    detalle.append(["26gmx3000.001-Cliente Uno- Proyecto Uno", "Pagado", 1000])
    detalle.append(["26gmx7000.099-Cliente Tres- Proyecto Tres", "Sin pagar", 2000])

    concentrado = wb.create_sheet("Concentrado")
    concentrado.append(["Segmento", "Total"])
    concentrado.append(["CONSULTING", 1000])
    concentrado.append(["DS", 2000])

    wb.save(FIXTURES_DIR / "facturacion_mayo.xlsx")


def make_provisiones_ds_mayo() -> None:
    wb = Workbook()
    sheet = wb.active
    sheet.title = "2026"
    sheet.cell(row=1, column=1, value="Proyecto")
    sub_headers = ["PROVISION", "NUM.FACTURA", "MONTO", "Diferencia+", "Diferencia-", "Acumulados"]
    for col, header in enumerate(sub_headers, start=2):
        sheet.cell(row=2, column=col, value=f"Mayo {header}")
    sheet.cell(row=3, column=1, value="26gmx7000.002")
    sheet.cell(row=3, column=2, value=5000)

    wb.save(FIXTURES_DIR / "provisiones_ds_mayo.xlsx")


def make_provisiones_engineering_mayo() -> None:
    wb = Workbook()
    sheet = wb.active
    sheet.title = "Hoja1"
    sheet.append(["Proyecto", "Jan", "Feb", "Mar", "Apr", "May"])
    sheet.append(["26gmx2000.005-Cliente Cuatro", 0, 0, 0, 0, 3000])

    wb.save(FIXTURES_DIR / "provisiones_engineering_mayo.xlsx")


def make_overview_consulting_mayo() -> None:
    wb = Workbook()
    sheet = wb.active
    sheet.title = "2026.05"
    sheet.append(["STATUS", "PROJECT", "Moneda", "Total honorarios"])
    sheet.append(["PROVISION", "26gmx3000.001\nCliente Uno\nProyecto Uno", "USD", 600])
    sheet.append(["", "", "", 400])

    wb.save(FIXTURES_DIR / "overview_consulting_mayo.xlsx")


if __name__ == "__main__":
    make_summary_abril()
    make_facturacion_mayo()
    make_provisiones_ds_mayo()
    make_provisiones_engineering_mayo()
    make_overview_consulting_mayo()
    print("Fixtures written to", FIXTURES_DIR)
```

- [ ] **Step 2: Run the script to generate the fixtures**

Run: `uv run python pipelines/summary/tests/fixtures/make_fixtures.py`
Expected: prints `Fixtures written to ...` and creates the 5 files listed above.

- [ ] **Step 3: Commit**

```bash
git add agente-financiero-ptres/pipelines/summary/tests/fixtures/
git commit -m "test(summary): add synthetic fixture files for the 4 sources + previous Summary"
```

---

### Task 9: `pipelines/summary/interpret.py`

**Files:**
- Create: `pipelines/summary/interpret.py`
- Test: `pipelines/summary/tests/test_interpret.py`

**Interfaces:**
- Produces:
  - `interpret_ds(rows: list[list], anthropic_client) -> dict` → `{"mes_columna": int, "provision_columna": int, "codigo_columna": int, "filas_proyecto": list[int]}`
  - `interpret_engineering(rows: list[list], anthropic_client) -> dict` → `{"mes_columna": int, "codigo_columna": int, "filas_proyecto": list[int]}`
  - `interpret_consulting(rows: list[list], anthropic_client) -> dict` → `{"status_columna": int, "project_columna": int, "moneda_columna": int, "monto_columna": int}`
  - `interpret_facturacion(rows: list[list], anthropic_client) -> dict` → `{"proyecto_columna": int, "estado_columna": int}`
  - All 4 functions take `anthropic_client` as a parameter (never construct one internally) so tests inject a fake that returns canned JSON instead of calling the real API.

- [ ] **Step 1: Write the failing test**

```python
# pipelines/summary/tests/test_interpret.py
import json
from unittest.mock import MagicMock

from pipelines.summary.interpret import interpret_ds, interpret_engineering


def _fake_client(json_response: dict):
    client = MagicMock()
    message = MagicMock()
    message.content = [MagicMock(text=json.dumps(json_response))]
    client.messages.create.return_value = message
    return client


def test_interpret_ds_returns_structure():
    rows = [
        ["Proyecto", "Mayo PROVISION", "Mayo NUM.FACTURA"],
        ["26gmx7000.002", 5000, ""],
    ]
    fake_client = _fake_client(
        {"mes_columna": 1, "provision_columna": 1, "codigo_columna": 0, "filas_proyecto": [1]}
    )

    result = interpret_ds(rows, anthropic_client=fake_client)

    assert result["provision_columna"] == 1
    assert result["filas_proyecto"] == [1]
    fake_client.messages.create.assert_called_once()


def test_interpret_engineering_returns_structure():
    rows = [
        ["Proyecto", "Jan", "Feb", "Mar", "Apr", "May"],
        ["26gmx2000.005-Cliente Cuatro", 0, 0, 0, 0, 3000],
    ]
    fake_client = _fake_client({"mes_columna": 5, "codigo_columna": 0, "filas_proyecto": [1]})

    result = interpret_engineering(rows, anthropic_client=fake_client)

    assert result["mes_columna"] == 5
    assert result["filas_proyecto"] == [1]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pipelines/summary/tests/test_interpret.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipelines.summary.interpret'`

- [ ] **Step 3: Write implementation**

```python
# pipelines/summary/interpret.py
import json


def _ask_claude_for_structure(anthropic_client, prompt: str) -> dict:
    message = anthropic_client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(message.content[0].text)


def interpret_ds(rows: list[list], anthropic_client) -> dict:
    prompt = (
        "Esta es una hoja de provisiones DS. Cada mes es un bloque de 6 sub-columnas "
        "(PROVISION/NUM.FACTURA/MONTO/Diferencia+/Diferencia-/Acumulados). Identifica, para el "
        "mes más reciente presente, la columna de PROVISION, la columna de código de proyecto, "
        "y qué filas son filas de proyecto (excluye notas sueltas). "
        "Responde solo JSON con las llaves: mes_columna, provision_columna, codigo_columna, filas_proyecto.\n\n"
        f"Filas: {rows}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)


def interpret_engineering(rows: list[list], anthropic_client) -> dict:
    prompt = (
        "Esta es una hoja de provisiones Engineering: una columna por mes en inglés. "
        "Identifica la columna del mes más reciente, la columna de código de proyecto "
        "(formato código-cliente), y qué filas son filas de proyecto. "
        "Responde solo JSON con las llaves: mes_columna, codigo_columna, filas_proyecto.\n\n"
        f"Filas: {rows}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)


def interpret_consulting(rows: list[list], anthropic_client) -> dict:
    prompt = (
        "Esta es la hoja Overview Consulting. Cada proyecto ocupa un bloque de varias filas; "
        "solo la primera fila del bloque tiene STATUS/PROJECT/moneda, y el monto final es la suma "
        "de varias celdas 'Total honorarios' del bloque. El código de proyecto viene en una celda "
        "multilínea (código\\ncliente\\ndescripción). Identifica las columnas de STATUS, PROJECT, "
        "moneda y monto. Responde solo JSON con las llaves: status_columna, project_columna, "
        "moneda_columna, monto_columna.\n\n"
        f"Filas: {rows}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)


def interpret_facturacion(rows: list[list], anthropic_client) -> dict:
    prompt = (
        "Esta es la hoja Detalle de Facturación. El código de proyecto viene con guión "
        "(código-cliente-descripción). Identifica la columna de proyecto y la columna de estado "
        "de la factura. Responde solo JSON con las llaves: proyecto_columna, estado_columna.\n\n"
        f"Filas: {rows}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pipelines/summary/tests/test_interpret.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add agente-financiero-ptres/pipelines/summary/interpret.py agente-financiero-ptres/pipelines/summary/tests/test_interpret.py
git commit -m "feat(summary): add 4 interpreters with injectable Anthropic client"
```

---

### Task 10: `pipelines/summary/calculate.py`

**Files:**
- Create: `pipelines/summary/calculate.py`
- Test: `pipelines/summary/tests/test_calculate.py`

**Interfaces:**
- Consumes: the `dict` shapes produced by `interpret.py` functions (Task 9) — but `calculate` takes already-extracted plain values (project code, currency, amount), not raw sheet rows, so it can be tested without any interpreter or Claude involved.
- Produces:
  - `extraer_codigo(texto: str, formato: str) -> str` — `formato` is one of `"limpio"`, `"guion"`, `"multilinea"`; extracts the project code prefix per the rules in the spec.
  - `reconciliar(provisiones_mes_anterior: list[dict], facturas_mes: list[dict], provisiones_nuevas: list[dict]) -> dict` → `{"canceladas": [...], "activas": [...], "nuevas": [...]}`. Each provisión dict has `{"proyecto": str, "monto_mxn": float, "cc": int, "cliente": str}`; each factura dict has `{"proyecto": str, "estado": str}`.

- [ ] **Step 1: Write the failing test**

```python
# pipelines/summary/tests/test_calculate.py
from pipelines.summary.calculate import extraer_codigo, reconciliar


def test_extraer_codigo_limpio():
    assert extraer_codigo("26gmx7000.002", formato="limpio") == "26gmx7000.002"


def test_extraer_codigo_guion():
    assert extraer_codigo("26gmx3000.001-Cliente Uno- Proyecto Uno", formato="guion") == "26gmx3000.001"


def test_extraer_codigo_multilinea():
    assert extraer_codigo("26gmx3000.001\nCliente Uno\nProyecto Uno", formato="multilinea") == "26gmx3000.001"


def test_reconciliar_cancela_proyecto_facturado():
    provisiones_anteriores = [{"proyecto": "26gmx3000.001", "monto_mxn": 1000, "cc": 3000, "cliente": "Cliente Uno"}]
    facturas = [{"proyecto": "26gmx3000.001-Cliente Uno- Proyecto Uno", "estado": "Pagado"}]

    resultado = reconciliar(provisiones_anteriores, facturas, provisiones_nuevas=[])

    assert len(resultado["canceladas"]) == 1
    assert resultado["canceladas"][0]["proyecto"] == "26gmx3000.001"
    assert resultado["activas"] == []


def test_reconciliar_factura_cancelada_no_cuenta():
    provisiones_anteriores = [{"proyecto": "26gmx3000.001", "monto_mxn": 1000, "cc": 3000, "cliente": "Cliente Uno"}]
    facturas = [{"proyecto": "26gmx3000.001-Cliente Uno- Proyecto Uno", "estado": "Cancelado"}]

    resultado = reconciliar(provisiones_anteriores, facturas, provisiones_nuevas=[])

    assert resultado["activas"][0]["proyecto"] == "26gmx3000.001"
    assert resultado["canceladas"] == []


def test_reconciliar_detecta_provision_nueva():
    resultado = reconciliar(
        provisiones_mes_anterior=[],
        facturas_mes=[],
        provisiones_nuevas=[{"proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000, "cliente": "Cliente Cuatro"}],
    )

    assert resultado["nuevas"][0]["proyecto"] == "26gmx2000.005"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pipelines/summary/tests/test_calculate.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipelines.summary.calculate'`

- [ ] **Step 3: Write implementation**

```python
# pipelines/summary/calculate.py


def extraer_codigo(texto: str, formato: str) -> str:
    if formato == "limpio":
        return texto.strip()
    if formato == "guion":
        return texto.split("-")[0].strip()
    if formato == "multilinea":
        return texto.split("\n")[0].strip()
    raise ValueError(f"Formato de código desconocido: {formato}")


def reconciliar(provisiones_mes_anterior: list[dict], facturas_mes: list[dict], provisiones_nuevas: list[dict]) -> dict:
    facturados = {
        extraer_codigo(f["proyecto"], formato="guion")
        for f in facturas_mes
        if f["estado"] in ("Sin pagar", "Pagado")
    }

    canceladas = []
    activas = []
    for provision in provisiones_mes_anterior:
        codigo = extraer_codigo(provision["proyecto"], formato="limpio")
        if codigo in facturados:
            canceladas.append(provision)
        else:
            activas.append(provision)

    return {"canceladas": canceladas, "activas": activas, "nuevas": list(provisiones_nuevas)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pipelines/summary/tests/test_calculate.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add agente-financiero-ptres/pipelines/summary/calculate.py agente-financiero-ptres/pipelines/summary/tests/test_calculate.py
git commit -m "feat(summary): add deterministic code extraction and reconciliation"
```

---

### Task 11: `pipelines/summary/write.py`

**Files:**
- Create: `pipelines/summary/write.py`
- Test: `pipelines/summary/tests/test_write.py`

**Interfaces:**
- Consumes: the fixture `summary_abril.xlsm` (Task 8), the `reconciliar(...)` output shape (Task 10).
- Produces:
  - `escribir_hoja_mes(ruta_origen: str, ruta_destino: str, hoja_mes_anterior: str, hoja_mes_nuevo: str, filas: list[list]) -> None` — opens `ruta_origen`, duplicates `hoja_mes_anterior` as `hoja_mes_nuevo`, clears rows 12+ in the new sheet, writes `filas` starting at row 13, saves to `ruta_destino`. Never modifies rows 1–11.

- [ ] **Step 1: Write the failing test**

```python
# pipelines/summary/tests/test_write.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pipelines/summary/tests/test_write.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipelines.summary.write'`

- [ ] **Step 3: Write implementation**

```python
# pipelines/summary/write.py
from copy import copy

from openpyxl import load_workbook


def _duplicate_sheet(wb, origen_titulo: str, nuevo_titulo: str):
    origen = wb[origen_titulo]
    nueva = wb.copy_worksheet(origen)
    nueva.title = nuevo_titulo
    return nueva


def _limpiar_seccion_b(sheet) -> None:
    for row in sheet.iter_rows(min_row=12, max_row=sheet.max_row):
        for cell in row:
            cell.value = None


def escribir_hoja_mes(
    ruta_origen: str,
    ruta_destino: str,
    hoja_mes_anterior: str,
    hoja_mes_nuevo: str,
    filas: list[list],
) -> None:
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

    wb.save(ruta_destino)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pipelines/summary/tests/test_write.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add agente-financiero-ptres/pipelines/summary/write.py agente-financiero-ptres/pipelines/summary/tests/test_write.py
git commit -m "feat(summary): add openpyxl writer that never touches rows 1-11"
```

---

### Task 12: `pipelines/summary/spec.py` — wire it into `core`

**Files:**
- Create: `pipelines/summary/spec.py`
- Test: `pipelines/summary/tests/test_spec_end_to_end.py`

**Interfaces:**
- Consumes: `core.pipeline_spec.PipelineSpec`, `core.registry.register` (Task 5); `pipelines.summary.calculate.reconciliar` (Task 10); `pipelines.summary.write.escribir_hoja_mes` (Task 11).
- Produces:
  - `SUMMARY_SPEC = PipelineSpec(name="summary", sources=[...], interpret=..., calculate=..., write=...)`
  - `summary_calculate(estructura: dict, estado_anterior: dict) -> dict` — adapts `reconciliar(...)`'s output into the `{"resumen": ..., "detalle": ...}` shape the generic API (Task 7) expects.
  - `summary_write(detalle: dict, archivo_destino) -> dict` — adapts `escribir_hoja_mes(...)` into the generic `write(plan_detalle, archivo_destino)` signature.
  - This task does not call `interpret.py`'s Claude-backed functions for the end-to-end test — it stubs `interpret` with a fixed return value, since Tasks 9–11 already cover the interpreters and calculation/write in isolation. The point of this test is proving the 3 pieces compose correctly through the real `core` API.

- [ ] **Step 1: Write the failing test**

```python
# pipelines/summary/tests/test_spec_end_to_end.py
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from core.api import app
from core.registry import clear_registry, register
from pipelines.summary.spec import build_summary_spec

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTE_DB_PATH", str(tmp_path / "test.db"))
    clear_registry()

    destino = tmp_path / "summary_mayo.xlsm"

    def fake_interpret(raw_files):
        return {
            "provisiones_mes_anterior": [
                {"proyecto": "26gmx3000.001", "monto_mxn": 1000, "cc": 3000, "cliente": "Cliente Uno"}
            ],
            "facturas_mes": [
                {"proyecto": "26gmx3000.001-Cliente Uno- Proyecto Uno", "estado": "Pagado"}
            ],
            "provisiones_nuevas": [
                {"proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000, "cliente": "Cliente Cuatro"}
            ],
        }

    spec = build_summary_spec(
        interpret_override=fake_interpret,
        ruta_origen=str(FIXTURES_DIR / "summary_abril.xlsm"),
        ruta_destino=str(destino),
        hoja_mes_anterior="2026_Abr",
        hoja_mes_nuevo="2026_May",
    )
    register(spec)
    yield TestClient(app), destino
    clear_registry()


def test_procesar_confirmar_escribe_archivo(client):
    test_client, destino = client

    procesar = test_client.post("/procesar/summary", json={"mes": "2026_May", "usuario": "luis"})
    assert procesar.status_code == 200
    resumen = procesar.json()["resumen"]
    assert len(resumen["canceladas"]) == 1
    assert len(resumen["nuevas"]) == 1

    confirmar = test_client.post("/confirmar/summary", json={"token": procesar.json()["token"]})
    assert confirmar.status_code == 200

    wb = load_workbook(destino)
    hoja = wb["2026_May"]
    assert hoja.cell(row=13, column=8).value == "26gmx2000.005"
    for row in range(1, 12):
        assert hoja.cell(row=row, column=1).value == f"KPI fila {row}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pipelines/summary/tests/test_spec_end_to_end.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipelines.summary.spec'`

- [ ] **Step 3: Write implementation**

```python
# pipelines/summary/spec.py
from core.pipeline_spec import PipelineSpec
from pipelines.summary.calculate import reconciliar
from pipelines.summary.write import escribir_hoja_mes

SOURCES = [
    "{mes}_Facturacion_sem.xlsx",
    "FORMATO_PROVISIONES_P3_DS_{mes}.xlsx",
    "Provisiones_ES_{mes}.xlsx",
    "PROVISIONES_Overview_Projects_{mes}.xlsx",
]


def build_summary_spec(
    interpret_override,
    ruta_origen: str,
    ruta_destino: str,
    hoja_mes_anterior: str,
    hoja_mes_nuevo: str,
) -> PipelineSpec:
    def calculate(estructura: dict, estado_anterior) -> dict:
        resultado = reconciliar(
            provisiones_mes_anterior=estructura["provisiones_mes_anterior"],
            facturas_mes=estructura["facturas_mes"],
            provisiones_nuevas=estructura["provisiones_nuevas"],
        )
        filas = [
            [
                "", "Provision", 2026, hoja_mes_nuevo.split("_")[1], p["cc"], p["cliente"], "",
                p["proyecto"], "MXN", p["monto_mxn"], 1, p["monto_mxn"], 0, p["monto_mxn"], 0, 0,
                p["monto_mxn"], "", "",
            ]
            for p in resultado["activas"] + resultado["nuevas"]
        ]
        return {"resumen": resultado, "detalle": {"filas": filas}}

    def write(detalle: dict, archivo_destino) -> dict:
        escribir_hoja_mes(
            ruta_origen=ruta_origen,
            ruta_destino=ruta_destino,
            hoja_mes_anterior=hoja_mes_anterior,
            hoja_mes_nuevo=hoja_mes_nuevo,
            filas=detalle["filas"],
        )
        return {"archivo": ruta_destino, "filas_escritas": len(detalle["filas"])}

    return PipelineSpec(
        name="summary",
        sources=SOURCES,
        interpret=interpret_override,
        calculate=calculate,
        write=write,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pipelines/summary/tests/test_spec_end_to_end.py -v`
Expected: 1 passed

- [ ] **Step 5: Run the full test suite**

Run: `uv run pytest -v`
Expected: all tests across `tests/` and `pipelines/summary/tests/` pass.

- [ ] **Step 6: Commit**

```bash
git add agente-financiero-ptres/pipelines/summary/spec.py agente-financiero-ptres/pipelines/summary/tests/test_spec_end_to_end.py
git commit -m "feat(summary): wire SummaryPipelineSpec end-to-end through the generic API"
```

---

## What this plan does NOT cover (deliberately)

- The real `interpret` function that composes the 4 per-source interpreters (Task 9) plus `core.drive_client` (Task 6) into the single `estructura` dict `calculate` (Task 10) expects — Task 12 stubs this with a fixed fake to validate wiring. Building the real composition is the next task once real Drive folder access (spec section 14, item 5) is confirmed with the client.
- Frontend (React/Vite SPA) — separate plan once this backend is validated.
- Real Google Drive credentials/folder wiring, real Anthropic API key usage — `drive_client` and `interpret` are built against fakes; plugging in real credentials is a deploy-time config step, not new code.
- Discrepancy-alert threshold and "provisión reabierta" detection — still pending client answers (spec section 14, items 8–9).
- Interface authentication — pending decision (spec section 14, item 4).
