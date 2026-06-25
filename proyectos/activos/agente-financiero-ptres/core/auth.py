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
