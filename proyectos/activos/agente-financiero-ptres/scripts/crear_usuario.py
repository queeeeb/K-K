import argparse
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import auth
from core.db import get_connection, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea un usuario para el Agente Financiero P3")
    parser.add_argument("username")
    args = parser.parse_args()

    if sys.stdin.isatty():
        password = getpass.getpass("Contraseña: ")
    else:
        password = sys.stdin.readline().rstrip("\n")

    db_path = os.environ.get("AGENTE_DB_PATH", "agente.db")
    conn = get_connection(db_path)
    init_db(conn)
    auth.crear_usuario(conn, args.username, password)
    print(f"Usuario '{args.username}' creado.")


if __name__ == "__main__":
    main()
