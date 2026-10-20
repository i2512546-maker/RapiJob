"""
RapiJob - Capa de base de datos.

Motor principal: MySQL (Alwaysdata) vía PyMySQL.
Fallback local: SQLite (rapijob.db) cuando no hay DB_HOST configurado.

API pública:
- query_db(query, args=None, one=False)  -> filas (dict) o None
- execute_db(query, args=None)           -> id del último INSERT (o None)
- get_db()                               -> conexión activa
- is_mysql()                             -> True si el motor es MySQL

Las consultas usan marcadores %s (estilo MySQL). SQLite los traduce a ?.
Nunca se concatena texto en el SQL: todo va parametrizado.
"""
import os
import re
import sqlite3
import threading
from datetime import datetime, date

from config import Config

try:
    import pymysql
    from pymysql.cursors import DictCursor
    _HAS_PYMYSQL = True
except Exception:
    pymysql = None
    _HAS_PYMYSQL = False

ENGINE = None
_local = threading.local()
_mysql_schema_ready = False


# ---------------------------------------------------------------------------
# Detección de motor
# ---------------------------------------------------------------------------
def _detect_engine():
    global ENGINE
    if ENGINE:
        return
    if Config.is_mysql_configured() and _HAS_PYMYSQL:
        try:
            conn = pymysql.connect(
                host=Config.DB_HOST, port=Config.DB_PORT,
                user=Config.DB_USER, password=Config.DB_PASSWORD,
                database=Config.DB_NAME, connect_timeout=5,
            )
            conn.close()
            ENGINE = "mysql"
            return
        except Exception:
            pass
    ENGINE = "sqlite"


def is_mysql():
    _detect_engine()
    return ENGINE == "mysql"


def _mysql_schema_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "schema_mysql.sql")


def _ensure_mysql_schema(conn):
    """Crea las tablas en MySQL si aún no existen (idempotente)."""
    global _mysql_schema_ready
    if _mysql_schema_ready:
        return
    path = _mysql_schema_path()
    statements = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            statements = [s.strip() for s in fh.read().split(";") if s.strip()]
    with conn.cursor() as cur:
        for stmt in statements:
            low = stmt.lstrip().lower()
            if low.startswith(("create", "set names", "use ")):
                cur.execute(stmt)
        # seed de categorías si está vacío
        cur.execute("SELECT COUNT(*) AS c FROM categorias")
        if cur.fetchone()["c"] == 0:
            for nombre in _SEED_CATEGORIAS:
                cur.execute("INSERT IGNORE INTO categorias (nombre) VALUES (%s)", (nombre,))
    conn.commit()
    _mysql_schema_ready = True


# ---------------------------------------------------------------------------
# Conexiones
# ---------------------------------------------------------------------------
def _mysql_connect():
    return pymysql.connect(
        host=Config.DB_HOST, port=Config.DB_PORT,
        user=Config.DB_USER, password=Config.DB_PASSWORD,
        database=Config.DB_NAME, charset="utf8mb4",
        cursorclass=DictCursor, autocommit=True,
    )


def _translate(query):
    q = re.sub(r"%s::\w+", "%s", query)   # quita casts ::uuid / ::int
    q = q.replace("%s", "?")
    q = re.sub(r"\bILIKE\b", "LIKE", q, flags=re.IGNORECASE)
    return q


_DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}$")
_D_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _sqlite_row_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        v = row[idx]
        if isinstance(v, str):
            if _DT_RE.match(v):
                v = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            elif _D_RE.match(v):
                v = date.fromisoformat(v)
        d[col[0]] = v
    return d


def _sqlite_connect(path):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = _sqlite_row_factory
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _mysql_get():
    if not getattr(_local, "conn", None):
        _local.conn = _mysql_connect()
        _ensure_mysql_schema(_local.conn)
    return _local.conn


def _sqlite_get():
    if not getattr(_local, "conn", None):
        _local.conn = _sqlite_connect(Config.SQLITE_PATH)
        _ensure_sqlite_schema(_local.conn)
    return _local.conn


def get_db():
    _detect_engine()
    return _mysql_get() if ENGINE == "mysql" else _sqlite_get()


# ---------------------------------------------------------------------------
# Ejecución de consultas (parametrizadas)
# ---------------------------------------------------------------------------
def query_db(query, args=None, one=False):
    _detect_engine()
    args = list(args or [])
    if ENGINE == "mysql":
        conn = _mysql_get()
        try:
            conn.ping(reconnect=True)
        except Exception:
            _local.conn = _mysql_connect()
            conn = _local.conn
        with conn.cursor() as cur:
            cur.execute(query, args)
            upper = query.lstrip().upper()
            if upper.startswith(("INSERT", "UPDATE", "DELETE")):
                return cur.lastrowid
            rows = cur.fetchall()
        return (rows[0] if rows else None) if one else rows

    conn = _sqlite_get()
    cur = conn.cursor()
    cur.execute(_translate(query), [_sqlite_coerce(a) for a in args])
    upper = _translate(query).lstrip().upper()
    if upper.startswith(("INSERT", "UPDATE", "DELETE")):
        conn.commit()
        rv = cur.lastrowid
        cur.close()
        return rv
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def execute_db(query, args=None):
    """Ejecuta una sentencia de escritura y devuelve el id insertado (o None)."""
    return query_db(query, args)


def _sqlite_coerce(value):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d %H:%M:%S") if isinstance(value, datetime) else value.isoformat()
    return value


# ---------------------------------------------------------------------------
# Esquema + seed embebidos para el fallback SQLite local
# ---------------------------------------------------------------------------
_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    clave_hash TEXT NOT NULL,
    telefono TEXT,
    rol TEXT NOT NULL CHECK (rol IN ('cliente','proveedor')),
    ciudad TEXT
);
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS servicios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proveedor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    categoria_id INTEGER NOT NULL REFERENCES categorias(id),
    titulo TEXT NOT NULL,
    descripcion TEXT,
    precio REAL NOT NULL DEFAULT 0,
    ubicacion TEXT
);
CREATE TABLE IF NOT EXISTS solicitudes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    servicio_id INTEGER NOT NULL REFERENCES servicios(id) ON DELETE CASCADE,
    estado TEXT NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente','aceptada','terminada','cancelada')),
    fecha TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now'))
);
CREATE TABLE IF NOT EXISTS calificaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solicitud_id INTEGER NOT NULL UNIQUE REFERENCES solicitudes(id) ON DELETE CASCADE,
    puntaje INTEGER NOT NULL,
    comentario TEXT
);
"""

_SEED_CATEGORIAS = [
    "Electricidad", "Gasfitería", "Cómputo y Redes",
    "Aire Acondicionado", "Electrodomésticos",
]

_seeded = False


def _seed_categorias(conn):
    cur = conn.cursor()
    for nombre in _SEED_CATEGORIAS:
        cur.execute("SELECT 1 FROM categorias WHERE nombre = ?", (nombre,))
        if not cur.fetchone():
            cur.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
    conn.commit()
    cur.close()


def _ensure_sqlite_schema(conn):
    global _seeded
    if _seeded:
        return
    conn.executescript(_SQLITE_SCHEMA)
    _seed_categorias(conn)
    _seeded = True
