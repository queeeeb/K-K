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
