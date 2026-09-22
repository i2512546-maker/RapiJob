"""
RapiJob - Script de inicialización
Genera hashes bcrypt reales para las contraseñas del seed.
Ejecutar después de docker compose up: python init_passwords.py
"""
import os
import sys
import psycopg2
from werkzeug.security import generate_password_hash

DEFAULT_PASSWORD = "password123"


def main():
    url = os.environ.get("DATABASE_URL", sys.argv[1] if len(sys.argv) > 1 else
                         "postgresql://postgres:postgres@localhost:5432/rapijob")
    pw = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PASSWORD

    print(f"Conectando a: {url}")
    conn = psycopg2.connect(url)
    conn.autocommit = True
    cur = conn.cursor()

    pw_hash = generate_password_hash(pw)
    print(f"Hash generado para password: '{pw}'")

    cur.execute("UPDATE users SET password = %s WHERE password != %s", (pw_hash, pw_hash))
    updated = cur.rowcount
    print(f"Passwords actualizados: {updated} usuarios")

    cur.close()
    conn.close()
    print("Listo! Credenciales: admin@rapijob.com / password123")


if __name__ == "__main__":
    main()
