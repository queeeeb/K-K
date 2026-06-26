import json
import os
import re
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

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


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Agente Financiero P3", docs_url=None, redoc_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
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
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest):
    conn = _conn()
    try:
        token = auth.autenticar(conn, body.usuario, body.password)
    except auth.InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    return {"access_token": token, "token_type": "bearer", "expires_in": auth.TOKEN_EXPIRE_HOURS * 3600}


def _validar_pipeline(pipeline: str) -> str:
    if not re.fullmatch(r"[a-z0-9_-]+", pipeline):
        raise HTTPException(status_code=400, detail="Pipeline inválido")
    try:
        return registry.get(pipeline)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline}' no registrado")


@app.post("/procesar/{pipeline}")
def procesar(pipeline: str, body: ProcesarRequest, usuario_autenticado: str = Depends(get_current_user)):
    spec = _validar_pipeline(pipeline)
    conn = _conn()
    token = str(uuid.uuid4())

    try:
        acquire_lock(conn, pipeline, body.mes, token=token, locked_by=usuario_autenticado)
    except LockHeldError as exc:
        raise HTTPException(status_code=409, detail=f"Locked by {exc.locked_by}")

    try:
        raw_files = {source: None for source in spec.sources}
        estructura = spec.interpret(raw_files)
        plan = spec.calculate(estructura, estado_anterior=None)

        conn.execute(
            "INSERT INTO plans (token, pipeline, mes, plan_json, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
            (token, pipeline, body.mes, json.dumps(plan)),
        )
        conn.commit()
    except Exception:
        release_lock(conn, pipeline, body.mes)
        raise

    return {"token": token, "resumen": plan["resumen"]}


@app.post("/confirmar/{pipeline}")
def confirmar(pipeline: str, body: TokenRequest, usuario_autenticado: str = Depends(get_current_user)):
    spec = _validar_pipeline(pipeline)
    conn = _conn()

    row = conn.execute(
        "SELECT mes, plan_json FROM plans WHERE token = ? AND pipeline = ?", (body.token, pipeline)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Token not found")

    plan = json.loads(row["plan_json"])
    try:
        reporte = spec.write(plan["detalle"], archivo_destino=None)
    except Exception:
        release_lock(conn, pipeline, row["mes"])
        conn.execute("DELETE FROM plans WHERE token = ?", (body.token,))
        conn.commit()
        raise

    audit_log.log_write(
        conn, pipeline, row["mes"], fila="*", valor_anterior=None,
        valor_nuevo=json.dumps(reporte), usuario=usuario_autenticado,
    )
    release_lock(conn, pipeline, row["mes"])
    conn.execute("DELETE FROM plans WHERE token = ?", (body.token,))
    conn.commit()

    return {"reporte": reporte}


@app.post("/rechazar/{pipeline}")
def rechazar(pipeline: str, body: TokenRequest, usuario_autenticado: str = Depends(get_current_user)):
    _validar_pipeline(pipeline)
    conn = _conn()
    row = conn.execute(
        "SELECT mes FROM plans WHERE token = ? AND pipeline = ?", (body.token, pipeline)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Token not found")

    audit_log.log_write(
        conn, pipeline, row["mes"], fila="*", valor_anterior=None,
        valor_nuevo="rechazado", usuario=usuario_autenticado,
    )
    release_lock(conn, pipeline, row["mes"])
    conn.execute("DELETE FROM plans WHERE token = ?", (body.token,))
    conn.commit()

    return {"status": "rechazado"}
