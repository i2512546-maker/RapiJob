"""
RapiJob - Inicialización de datos de prueba.

Crea el esquema (si no existe), el seed de categorías y usuarios demo con
contraseñas bcrypt reales, usando las credenciales de las variables de entorno
(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME). También funciona en local con
SQLite (fallback) cuando no hay DB_HOST.

Uso:
    python init_passwords.py
"""
import bcrypt

import db
from config import Config

DEFAULT_PASSWORD = "password123"

DEMO_USERS = [
    # nombre, email, telefono, rol, ciudad
    ("Rosa Quispe",   "rosa.cliente@rapijob.pe",    "987654321", "cliente",   "Huancayo"),
    ("Carmen Huaman", "carmen.cliente@rapijob.pe",  "987654322", "cliente",   "El Tambo"),
    ("Juan Perez",    "juan.electrico@rapijob.pe",  "988111222", "proveedor", "El Tambo"),
    ("Carlos Ramos",  "carlos.gasfitero@rapijob.pe", "988333444", "proveedor", "Huancayo"),
    ("Ana Torres",    "ana.electro@rapijob.pe",     "988555666", "proveedor", "Chilca"),
    ("Admin RapiJob", "admin@rapijob.com",          "999000111", "proveedor", "Huancayo"),
]


def main():
    db._detect_engine()
    print(f"Motor de base de datos: {db.ENGINE}")

    if db.ENGINE == "sqlite":
        db.get_db()  # crea esquema + seed de categorías

    pw_hash = bcrypt.hashpw(DEFAULT_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    creados = 0
    for nombre, email, telefono, rol, ciudad in DEMO_USERS:
        existing = db.query_db("SELECT id FROM usuarios WHERE email = %s", [email], one=True)
        if existing:
            db.execute_db("UPDATE usuarios SET clave_hash = %s WHERE email = %s", [pw_hash, email])
            continue
        db.execute_db(
            "INSERT INTO usuarios (nombre, email, clave_hash, telefono, rol, ciudad) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            [nombre, email, pw_hash, telefono, rol, ciudad]
        )
        creados += 1

    print(f"Usuarios demo creados: {creados}")
    print(f"Contraseña para todos: {DEFAULT_PASSWORD}")


if __name__ == "__main__":
    main()
