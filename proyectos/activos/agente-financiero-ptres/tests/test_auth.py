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
