# Autenticación JWT — Agente Financiero P3 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Proteger `/procesar/{pipeline}`, `/confirmar/{pipeline}` y `/rechazar/{pipeline}` con autenticación JWT, con un usuario individual por persona de P3, token expirando a las 8 horas.

**Architecture:** Tabla `usuarios` en el mismo SQLite (`core/db.py`) con `password_hash` (bcrypt). Login (`POST /login`) verifica credenciales y emite un JWT firmado (HS256, `PyJWT`) con `sub`=username y `exp`=+8h. Una dependencia de FastAPI (`core/auth.py:get_current_user`, vía `core/api.py`) decodifica el header `Authorization: Bearer <token>` en cada endpoint protegido. No hay endpoint público de registro — los usuarios se crean con un script de línea de comandos (`scripts/crear_usuario.py`) que corre quien administra el servidor.

**Tech Stack:** `PyJWT` (codificar/decodificar tokens), `bcrypt` (hash de contraseñas), `fastapi.security.HTTPBearer` (extraer el header Authorization).

## Global Constraints

- El secreto de firma del JWT vive en la variable de entorno `AGENTE_JWT_SECRET` — nunca hardcoded, nunca con valor default en producción.
- El token expira exactamente a las 8 horas (`TOKEN_EXPIRE_HOURS = 8` en `core/auth.py`).
- Ningún dato real de P3 en tests — usuarios/contraseñas de prueba son sintéticos (ver `CLAUDE.md` raíz del repo K-K).
- `core/` sigue sin conocer lógica de negocio de ningún pipeline — `auth.py` es genérico para los 3 pipelines, igual que `lock.py` y `audit_log.py`.

---

## Task 1: Tabla `usuarios` en la base de datos

**Files:**
- Modify: `core/db.py`
- Test: `tests/test_db.py` (nuevo)

**Interfaces:**
- Produces: `init_db(conn)` crea también la tabla `usuarios(id, username UNIQUE, password_hash, created_at)`, usada por `core/auth.py` (Task 2).

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_db.py`:

```python
import sqlite3

from core.db import get_connection, init_db


def test_init_db_creates_usuarios_table():
    conn = get_connection(":memory:")
    init_db(conn)

    conn.execute(
        "INSERT INTO usuarios (username, password_hash, created_at) VALUES (?, ?, datetime('now'))",
        ("luis", "hash-falso"),
    )
    conn.commit()

    row = conn.execute("SELECT username FROM usuarios WHERE username = ?", ("luis",)).fetchone()
    assert row["username"] == "luis"


def test_usuarios_username_is_unique():
    conn = get_connection(":memory:")
    init_db(conn)

    conn.execute(
        "INSERT INTO usuarios (username, password_hash, created_at) VALUES (?, ?, datetime('now'))",
        ("luis", "hash-falso"),
    )
    conn.commit()

    try:
        conn.execute(
            "INSERT INTO usuarios (username, password_hash, created_at) VALUES (?, ?, datetime('now'))",
            ("luis", "otro-hash"),
        )
        conn.commit()
        raised = False
    except sqlite3.IntegrityError:
        raised = True

    assert raised
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `uv run pytest tests/test_db.py -v`
Expected: FAIL — `sqlite3.OperationalError: no such table: usuarios`

- [ ] **Step 3: Agregar la tabla en `init_db`**

En `core/db.py`, dentro de `init_db`, después del `CREATE TABLE IF NOT EXISTS locks` existente y antes del `conn.commit()` final:

```python
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
```

- [ ] **Step 4: Correr el test para confirmar que pasa**

Run: `uv run pytest tests/test_db.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add core/db.py tests/test_db.py
git commit -m "feat(auth): agrega tabla usuarios a la base de datos"
```

---

## Task 2: Dependencias — `PyJWT` y `bcrypt`

**Files:**
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: imports `jwt` (PyJWT) y `bcrypt` disponibles para Task 3.

- [ ] **Step 1: Agregar las dependencias**

En `pyproject.toml`, en `[project].dependencies`, agregar después de `"pydantic>=2.9",`:

```toml
    "pyjwt>=2.9",
    "bcrypt>=4.2",
```

- [ ] **Step 2: Instalar**

Run: `uv sync`
Expected: instala `pyjwt` y `bcrypt` sin errores, lockfile actualizado.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build(auth): agrega pyjwt y bcrypt como dependencias"
```

---

## Task 3: `core/auth.py` — hashing, tokens, autenticación

**Files:**
- Create: `core/auth.py`
- Test: `tests/test_auth.py` (nuevo)

**Interfaces:**
- Consumes: `core.db.get_connection`, `core.db.init_db` (Task 1).
- Produces (usado por Task 4 y por `scripts/crear_usuario.py` en Task 5):
  - `hash_password(password: str) -> str`
  - `verify_password(password: str, password_hash: str) -> bool`
  - `crear_usuario(conn: sqlite3.Connection, username: str, password: str) -> None`
  - `autenticar(conn: sqlite3.Connection, username: str, password: str) -> str` (retorna el JWT)
  - `create_access_token(username: str) -> str`
  - `decode_access_token(token: str) -> str` (retorna el username, o lanza `InvalidTokenError`)
  - `InvalidCredentialsError`, `InvalidTokenError` (excepciones)
  - `TOKEN_EXPIRE_HOURS = 8`

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/test_auth.py`:

```python
import os
import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from core import auth
from core.db import get_connection, init_db


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setenv("AGENTE_JWT_SECRET", "secreto-de-prueba-no-real")


@pytest.fixture
def conn():
    c = get_connection(":memory:")
    init_db(c)
    return c


def test_hash_password_is_not_plaintext():
    hashed = auth.hash_password("clave123")
    assert hashed != "clave123"


def test_verify_password_accepts_correct_password():
    hashed = auth.hash_password("clave123")
    assert auth.verify_password("clave123", hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = auth.hash_password("clave123")
    assert auth.verify_password("otra-clave", hashed) is False


def test_crear_usuario_then_autenticar(conn):
    auth.crear_usuario(conn, "luis", "clave123")

    token = auth.autenticar(conn, "luis", "clave123")

    assert auth.decode_access_token(token) == "luis"


def test_autenticar_con_password_incorrecto_lanza_error(conn):
    auth.crear_usuario(conn, "luis", "clave123")

    with pytest.raises(auth.InvalidCredentialsError):
        auth.autenticar(conn, "luis", "clave-equivocada")


def test_autenticar_usuario_inexistente_lanza_error(conn):
    with pytest.raises(auth.InvalidCredentialsError):
        auth.autenticar(conn, "no-existe", "clave123")


def test_create_access_token_expira_en_8_horas():
    token = auth.create_access_token("luis")
    payload = jwt.decode(token, os.environ["AGENTE_JWT_SECRET"], algorithms=["HS256"])

    expira = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    emitido_mas_8h = datetime.now(timezone.utc) + timedelta(hours=8)

    assert abs((expira - emitido_mas_8h).total_seconds()) < 5


def test_decode_access_token_rechaza_token_expirado():
    payload = {
        "sub": "luis",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    token_expirado = jwt.encode(payload, os.environ["AGENTE_JWT_SECRET"], algorithm="HS256")

    with pytest.raises(auth.InvalidTokenError):
        auth.decode_access_token(token_expirado)


def test_decode_access_token_rechaza_firma_invalida():
    token_ajeno = jwt.encode({"sub": "luis", "exp": time.time() + 3600}, "otro-secreto", algorithm="HS256")

    with pytest.raises(auth.InvalidTokenError):
        auth.decode_access_token(token_ajeno)
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `uv run pytest tests/test_auth.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.auth'`

- [ ] **Step 3: Implementar `core/auth.py`**

```python
import os
import sqlite3
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 8


class InvalidCredentialsError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


def _secret_key() -> str:
    secret = os.environ.get("AGENTE_JWT_SECRET")
    if not secret:
        raise RuntimeError("AGENTE_JWT_SECRET no está configurado")
    return secret


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def crear_usuario(conn: sqlite3.Connection, username: str, password: str) -> None:
    conn.execute(
        "INSERT INTO usuarios (username, password_hash, created_at) VALUES (?, ?, datetime('now'))",
        (username, hash_password(password)),
    )
    conn.commit()


def create_access_token(username: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "exp": expires_at}
    return jwt.encode(payload, _secret_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, _secret_key(), algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError() from exc
    return payload["sub"]


def autenticar(conn: sqlite3.Connection, username: str, password: str) -> str:
    row = conn.execute(
        "SELECT password_hash FROM usuarios WHERE username = ?", (username,)
    ).fetchone()
    if row is None or not verify_password(password, row["password_hash"]):
        raise InvalidCredentialsError()
    return create_access_token(username)
```

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `uv run pytest tests/test_auth.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add core/auth.py tests/test_auth.py
git commit -m "feat(auth): hashing de contraseñas y emisión/verificación de JWT"
```

---

## Task 4: Proteger `/procesar`, `/confirmar`, `/rechazar` en `core/api.py`

**Files:**
- Modify: `core/api.py`
- Modify: `tests/conftest.py`
- Modify: `tests/test_api.py`

**Interfaces:**
- Consumes: `core.auth.autenticar`, `core.auth.decode_access_token`, `core.auth.InvalidCredentialsError`, `core.auth.InvalidTokenError` (Task 3).
- Produces: `POST /login` (body `{usuario, password}` → `{access_token, token_type, expires_in}`); dependencia `get_current_user` reutilizable si se agregan endpoints futuros.

**Nota de diseño:** hoy `ProcesarRequest.usuario` es un campo que cualquiera puede llenar con cualquier nombre — eso es lo que hace que el bloqueo (`lock`) no sea confiable. Este task lo reemplaza: el usuario que queda registrado en el `lock` pasa a ser el del token (`usuario_autenticado`), no un campo del body.

- [ ] **Step 1: Actualizar el fixture de tests para crear un usuario y loguear**

Modificar `tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient

from core import auth
from core.api import _conn, app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers(monkeypatch):
    monkeypatch.setenv("AGENTE_JWT_SECRET", "secreto-de-prueba-no-real")

    def _headers_for(username: str, password: str = "clave123") -> dict[str, str]:
        conn = _conn()
        auth.crear_usuario(conn, username, password)
        token = auth.create_access_token(username)
        return {"Authorization": f"Bearer {token}"}

    return _headers_for
```

- [ ] **Step 2: Escribir los tests que fallan (login + endpoints protegidos)**

Reemplazar el contenido de `tests/test_api.py` con:

```python
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


def test_login_con_credenciales_correctas_devuelve_token(client, auth_headers):
    auth_headers("luis")  # crea el usuario "luis"
    response = client.post("/login", json={"usuario": "luis", "password": "clave123"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 8 * 3600
    assert "access_token" in body


def test_login_con_password_incorrecto_devuelve_401(client, auth_headers):
    auth_headers("luis")
    response = client.post("/login", json={"usuario": "luis", "password": "clave-equivocada"})

    assert response.status_code == 401


def test_procesar_sin_token_devuelve_401(client):
    response = client.post("/procesar/fake", json={"mes": "2026_May"})
    assert response.status_code == 401


def test_procesar_then_confirmar(client, auth_headers):
    headers = auth_headers("luis")

    response = client.post("/procesar/fake", json={"mes": "2026_May"}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert "token" in body
    assert body["resumen"]["nuevas"][0]["proyecto"] == "X-1"

    response = client.post("/confirmar/fake", json={"token": body["token"]}, headers=headers)
    assert response.status_code == 200
    assert response.json()["reporte"]["filas_escritas"] == 1


def test_procesar_locked_returns_409(client, auth_headers):
    headers_luis = auth_headers("luis")
    headers_oswaldo = auth_headers("oswaldo")

    first = client.post("/procesar/fake", json={"mes": "2026_May"}, headers=headers_luis)
    assert first.status_code == 200

    second = client.post("/procesar/fake", json={"mes": "2026_May"}, headers=headers_oswaldo)
    assert second.status_code == 409
    assert "luis" in second.json()["detail"]


def test_rechazar_frees_lock(client, auth_headers):
    headers_luis = auth_headers("luis")
    headers_oswaldo = auth_headers("oswaldo")

    first = client.post("/procesar/fake", json={"mes": "2026_May"}, headers=headers_luis)
    token = first.json()["token"]

    rechazar = client.post("/rechazar/fake", json={"token": token}, headers=headers_luis)
    assert rechazar.status_code == 200

    second = client.post("/procesar/fake", json={"mes": "2026_May"}, headers=headers_oswaldo)
    assert second.status_code == 200
```

- [ ] **Step 3: Correr los tests para confirmar que fallan**

Run: `uv run pytest tests/test_api.py -v`
Expected: FAIL — `404 Not Found` en `/login` (no existe todavía) y `422`/`200` inesperados en los endpoints sin proteger.

- [ ] **Step 4: Implementar login y proteger los endpoints en `core/api.py`**

Reemplazar el contenido completo de `core/api.py`:

```python
import json
import os
import uuid

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from core import audit_log, auth, registry
from core.db import get_connection, init_db
from core.lock import LockHeldError, acquire_lock, release_lock


class ProcesarRequest(BaseModel):
    mes: str


class TokenRequest(BaseModel):
    token: str


class LoginRequest(BaseModel):
    usuario: str
    password: str


app = FastAPI(title="Agente Financiero P3")
_bearer_scheme = HTTPBearer()


def _db_path() -> str:
    return os.environ.get("AGENTE_DB_PATH", "agente.db")


def _conn():
    conn = get_connection(_db_path())
    init_db(conn)
    return conn


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme)) -> str:
    try:
        return auth.decode_access_token(credentials.credentials)
    except auth.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/login")
def login(body: LoginRequest):
    conn = _conn()
    try:
        token = auth.autenticar(conn, body.usuario, body.password)
    except auth.InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    return {"access_token": token, "token_type": "bearer", "expires_in": auth.TOKEN_EXPIRE_HOURS * 3600}


@app.post("/procesar/{pipeline}")
def procesar(pipeline: str, body: ProcesarRequest, usuario_autenticado: str = Depends(get_current_user)):
    spec = registry.get(pipeline)
    conn = _conn()
    token = str(uuid.uuid4())

    try:
        acquire_lock(conn, pipeline, body.mes, token=token, locked_by=usuario_autenticado)
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
def confirmar(pipeline: str, body: TokenRequest, usuario_autenticado: str = Depends(get_current_user)):
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
def rechazar(pipeline: str, body: TokenRequest, usuario_autenticado: str = Depends(get_current_user)):
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

- [ ] **Step 5: Correr los tests para confirmar que pasan**

Run: `uv run pytest tests/test_api.py -v`
Expected: PASS (8 tests)

- [ ] **Step 6: Correr toda la suite del repo para confirmar que nada más se rompió**

Run: `uv run pytest -v`
Expected: PASS — incluye `pipelines/summary` y `pipelines/pl`, que no dependen de `usuario` en el body.

- [ ] **Step 7: Commit**

```bash
git add core/api.py tests/conftest.py tests/test_api.py
git commit -m "feat(auth): protege /procesar /confirmar /rechazar con JWT y agrega /login"
```

---

## Task 5: Script para crear usuarios

**Files:**
- Create: `scripts/crear_usuario.py`
- Test: `tests/test_crear_usuario_script.py` (nuevo)

**Interfaces:**
- Consumes: `core.auth.crear_usuario`, `core.db.get_connection`, `core.db.init_db` (Task 1, Task 3).

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_crear_usuario_script.py`:

```python
import subprocess
import sys

from core.db import get_connection, init_db


def test_crear_usuario_script_inserta_usuario(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("AGENTE_DB_PATH", str(db_path))

    resultado = subprocess.run(
        [sys.executable, "scripts/crear_usuario.py", "montserrat", "clave-segura-123"],
        env={**__import__("os").environ, "AGENTE_DB_PATH": str(db_path)},
        capture_output=True,
        text=True,
    )

    assert resultado.returncode == 0
    assert "montserrat" in resultado.stdout

    conn = get_connection(str(db_path))
    init_db(conn)
    row = conn.execute("SELECT username FROM usuarios WHERE username = ?", ("montserrat",)).fetchone()
    assert row["username"] == "montserrat"
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `uv run pytest tests/test_crear_usuario_script.py -v`
Expected: FAIL — `FileNotFoundError` / `can't open file 'scripts/crear_usuario.py'`

- [ ] **Step 3: Implementar `scripts/crear_usuario.py`**

```python
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import auth
from core.db import get_connection, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea un usuario para el Agente Financiero P3")
    parser.add_argument("username")
    parser.add_argument("password")
    args = parser.parse_args()

    db_path = os.environ.get("AGENTE_DB_PATH", "agente.db")
    conn = get_connection(db_path)
    init_db(conn)
    auth.crear_usuario(conn, args.username, args.password)
    print(f"Usuario '{args.username}' creado.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Correr el test para confirmar que pasa**

Run: `uv run pytest tests/test_crear_usuario_script.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/crear_usuario.py tests/test_crear_usuario_script.py
git commit -m "feat(auth): script de línea de comandos para crear usuarios"
```

---

## Task 6: Documentar autenticación en el README

**Files:**
- Modify: `README.md`

**Interfaces:**
- Ninguna (solo documentación).

- [ ] **Step 1: Agregar sección de autenticación**

En `README.md`, agregar al final del archivo (después de la sección "Relación con otros proyectos del repo"):

```markdown

## Autenticación

Todos los endpoints de escritura (`/procesar/{pipeline}`, `/confirmar/{pipeline}`, `/rechazar/{pipeline}`) requieren un JWT en el header `Authorization: Bearer <token>`.

- **Obtener un token:** `POST /login` con `{"usuario": "...", "password": "..."}` → `{"access_token": "...", "token_type": "bearer", "expires_in": 28800}` (8 horas).
- **Crear un usuario nuevo:** `uv run python scripts/crear_usuario.py <username> <password>` — no hay endpoint público de registro, a propósito.
- **Variable de entorno requerida en el servidor:** `AGENTE_JWT_SECRET` — secreto de firma del JWT, nunca con valor por default. Generar uno con `python -c "import secrets; print(secrets.token_hex(32))"` y guardarlo fuera del repo.
- Cada persona de P3 tiene su propio usuario; el campo `locked_by` del módulo `lock` ahora se llena con el usuario autenticado, no con un campo libre del request.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs(auth): documenta login, creación de usuarios y AGENTE_JWT_SECRET"
```

---

## Self-Review

**Spec coverage:**
- Autenticación con usuarios individuales por persona → Task 1 (tabla usuarios), Task 3 (`crear_usuario`/`autenticar`), Task 5 (script de creación) ✅
- JWT con expiración de 8 horas → Task 3 (`TOKEN_EXPIRE_HOURS = 8`, tests de expiración) ✅
- `/procesar`, `/confirmar`, `/rechazar` protegidos → Task 4 ✅
- Esto resuelve el pendiente #4 de la sección 14 de `pipelines/summary/ESPECIFICACION.md` ("Confirmar el mecanismo de autenticación de la interfaz") — al cerrar el plan, actualizar esa línea en la spec marcándola como resuelta.

**Placeholder scan:** sin TBD/TODO; todos los pasos tienen código completo.

**Type consistency:** `get_current_user` devuelve `str` (username) en Task 4, mismo tipo que `decode_access_token` en Task 3; `crear_usuario(conn, username, password)` usado igual en Task 3 (tests), Task 4 (conftest) y Task 5 (script).
