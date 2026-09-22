"""
RapiJob - Capa de base de datos con doble motor.

- PostgreSQL: se usa cuando `psycopg2` está disponible y la base responde
  (despliegue en Docker / servidor real).
- SQLite: fallback automático (cero dependencias) para desarrollo local.
  Al primer acceso crea `rapijob.db` con el esquema y los datos semilla del MVP.

Todas las consultas de app.py se traducen de forma transparente entre motores.
"""
import os
import re
import sqlite3
import threading
from datetime import datetime, date

from config import Config

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    _HAS_PSYCOPG2 = True
except Exception:
    _HAS_PSYCOPG2 = False

ENGINE = None
_sqlite_path = None
_local = threading.local()
_seeded = False


def _detect_engine():
    global ENGINE, _sqlite_path
    if ENGINE:
        return
    url = (Config.DATABASE_URL or "").lower().strip()
    if url.startswith("sqlite"):
        name = url.split("://", 1)[-1] or "rapijob.db"
        _sqlite_path = name
        ENGINE = "sqlite"
        return
    if _HAS_PSYCOPG2:
        try:
            conn = psycopg2.connect(Config.DATABASE_URL, connect_timeout=4)
            conn.close()
            ENGINE = "postgres"
            return
        except Exception:
            pass
    ENGINE = "sqlite"
    _sqlite_path = os.environ.get("SQLITE_PATH", "rapijob.db")


# ---------------------------------------------------------------------------
# Coerciones y helpers SQL
# ---------------------------------------------------------------------------
def _now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _coerce(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return value


def sql_epoch_hours(col_after, col_before):
    """Fragmento SQL portable de horas transcurridas entre dos columnas."""
    _detect_engine()
    if ENGINE == "postgres":
        return f"EXTRACT(EPOCH FROM ({col_after} - {col_before}))/3600"
    return f"((julianday({col_after}) - julianday({col_before})) * 24)"


def is_postgres():
    _detect_engine()
    return ENGINE == "postgres"


# ---------------------------------------------------------------------------
# Conexiones
# ---------------------------------------------------------------------------
def _pg_connect():
    return psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)


def _translate(query):
    q = re.sub(r"%s::uuid", "?", query)
    q = q.replace("%s", "?")
    q = re.sub(r"\bILIKE\b", "LIKE", q, flags=re.IGNORECASE)
    return q


def _sqlite_connect(path):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = _row_factory
    conn.execute("PRAGMA foreign_keys=ON")
    conn.create_function("now", 0, _now_str)
    return conn


_DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}$")
_D_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _row_factory(cursor, row):
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


def _sqlite_get():
    if not hasattr(_local, "conn"):
        _local.conn = _sqlite_connect(_sqlite_path)
        _init_sqlite(_local.conn)
    return _local.conn


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------
def get_db():
    _detect_engine()
    if ENGINE == "postgres":
        return _pg_connect()
    return _sqlite_get()


def query_db(query, args=None, one=False):
    _detect_engine()
    args = [a for a in (args or [])]
    if ENGINE == "sqlite":
        conn = _sqlite_get()
        cur = conn.cursor()
        q = _translate(query)
        a = [_coerce(x) for x in args]
        try:
            cur.execute(q, a)
        except sqlite3.Error:
            conn.rollback()
            raise
        upper = q.lstrip().upper()
        if upper.startswith("SELECT") or upper.startswith("WITH") or "RETURNING" in upper:
            rows = cur.fetchall()
            conn.commit()
            if one:
                return dict(rows[0]) if rows else None
            return [dict(r) for r in rows]
        conn.commit()
        return cur.rowcount

    conn = _pg_connect()
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        upper = query.strip().upper()
        if upper.startswith("SELECT") or upper.startswith("WITH") or "RETURNING" in upper:
            rv = cur.fetchall()
            conn.commit()
            return dict(rv[0]) if rv and one else [dict(r) for r in rv]
        conn.commit()
        return cur.rowcount
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_db(query, args=None):
    return query_db(query, args)


# ---------------------------------------------------------------------------
# Esquema y semilla SQLite (solo desarrollo local)
# ---------------------------------------------------------------------------
SQLITE_UUID = ("lower(hex(randomblob(4))||'-'||hex(randomblob(2))"
               "||'-4000-'||'8000-'||hex(randomblob(6)))")
SQLITE_TS = "strftime('%Y-%m-%d %H:%M:%S','now')"

_SQLITE_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY DEFAULT ({SQLITE_UUID}),
    email       TEXT UNIQUE NOT NULL,
    phone       TEXT UNIQUE,
    password    TEXT NOT NULL,
    role        TEXT NOT NULL CHECK (role IN ('client','technician','admin','supervisor')),
    status      TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','inactive')),
    verified    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT ({SQLITE_TS}),
    updated_at  TEXT NOT NULL DEFAULT ({SQLITE_TS})
);
CREATE TABLE IF NOT EXISTS profiles (
    user_id            TEXT PRIMARY KEY,
    first_name         TEXT NOT NULL,
    last_name          TEXT NOT NULL,
    bio                TEXT,
    avatar_url         TEXT,
    location_lat       REAL,
    location_lng       REAL,
    location_label     TEXT,
    service_radius_km  REAL DEFAULT 30,
    hourly_rate        REAL,
    verified_at        TEXT,
    created_at         TEXT NOT NULL DEFAULT ({SQLITE_TS}),
    updated_at         TEXT NOT NULL DEFAULT ({SQLITE_TS})
);
CREATE TABLE IF NOT EXISTS specialties (
    id          TEXT PRIMARY KEY DEFAULT ({SQLITE_UUID}),
    name        TEXT NOT NULL,
    description TEXT,
    icon_url    TEXT,
    created_at  TEXT NOT NULL DEFAULT ({SQLITE_TS}),
    updated_at  TEXT NOT NULL DEFAULT ({SQLITE_TS})
);
CREATE TABLE IF NOT EXISTS technician_specialties (
    technician_id    TEXT,
    specialty_id     TEXT,
    experience_years REAL,
    created_at       TEXT NOT NULL DEFAULT ({SQLITE_TS}),
    PRIMARY KEY (technician_id, specialty_id)
);
CREATE TABLE IF NOT EXISTS certifications (
    id           TEXT PRIMARY KEY DEFAULT ({SQLITE_UUID}),
    name         TEXT NOT NULL,
    issuing_body TEXT,
    description  TEXT,
    created_at   TEXT NOT NULL DEFAULT ({SQLITE_TS}),
    updated_at   TEXT NOT NULL DEFAULT ({SQLITE_TS})
);
CREATE TABLE IF NOT EXISTS technician_certifications (
    id                TEXT PRIMARY KEY DEFAULT ({SQLITE_UUID}),
    technician_id     TEXT NOT NULL,
    certification_id  TEXT NOT NULL,
    document_url      TEXT NOT NULL,
    issued_at         TEXT,
    expires_at        TEXT,
    validation_status TEXT NOT NULL DEFAULT 'pending'
                      CHECK (validation_status IN ('pending','valid','rejected')),
    validated_by      TEXT,
    validated_at      TEXT,
    rejection_reason  TEXT,
    created_at        TEXT NOT NULL DEFAULT ({SQLITE_TS}),
    updated_at        TEXT NOT NULL DEFAULT ({SQLITE_TS})
);
CREATE TABLE IF NOT EXISTS jobs (
    id                 TEXT PRIMARY KEY DEFAULT ({SQLITE_UUID}),
    client_id          TEXT NOT NULL,
    title              TEXT NOT NULL,
    description        TEXT NOT NULL,
    specialty_id       TEXT NOT NULL,
    budget_min         REAL,
    budget_max         REAL,
    location_lat       REAL,
    location_lng       REAL,
    location_label     TEXT,
    is_remote          INTEGER NOT NULL DEFAULT 0,
    urgency            TEXT NOT NULL DEFAULT 'normal'
                       CHECK (urgency IN ('low','normal','high','urgent')),
    status             TEXT NOT NULL DEFAULT 'open'
                       CHECK (status IN ('open','in_progress','completed','cancelled')),
    deadline_at        TEXT,
    assigned_to        TEXT,
    completed_at       TEXT,
    cancelled_at       TEXT,
    cancellation_reason TEXT,
    created_at         TEXT NOT NULL DEFAULT ({SQLITE_TS}),
    updated_at         TEXT NOT NULL DEFAULT ({SQLITE_TS})
);
CREATE TABLE IF NOT EXISTS job_applications (
    id              TEXT PRIMARY KEY DEFAULT ({SQLITE_UUID}),
    job_id          TEXT NOT NULL,
    technician_id   TEXT NOT NULL,
    cover_letter    TEXT,
    proposed_price  REAL,
    status          TEXT NOT NULL DEFAULT 'applied'
                    CHECK (status IN ('applied','accepted','rejected','withdrawn')),
    created_at      TEXT NOT NULL DEFAULT ({SQLITE_TS}),
    updated_at      TEXT NOT NULL DEFAULT ({SQLITE_TS})
);
CREATE TABLE IF NOT EXISTS job_assignments (
    job_id            TEXT NOT NULL,
    technician_id     TEXT NOT NULL,
    assigned_by       TEXT,
    assigned_at       TEXT NOT NULL DEFAULT ({SQLITE_TS}),
    accepted_at       TEXT,
    rejected_at       TEXT,
    rejection_reason  TEXT,
    PRIMARY KEY (job_id, technician_id, assigned_at)
);
CREATE TABLE IF NOT EXISTS job_reviews (
    id            TEXT PRIMARY KEY DEFAULT ({SQLITE_UUID}),
    job_id        TEXT NOT NULL,
    reviewer_id   TEXT NOT NULL,
    reviewee_id   TEXT NOT NULL,
    rating        INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment       TEXT,
    is_anonymous  INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT ({SQLITE_TS}),
    updated_at    TEXT NOT NULL DEFAULT ({SQLITE_TS})
);
CREATE TABLE IF NOT EXISTS review_validations (
    id            TEXT PRIMARY KEY DEFAULT ({SQLITE_UUID}),
    job_id        TEXT NOT NULL,
    supervisor_id TEXT NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('approved','rejected','needs_revision')),
    score         REAL,
    notes         TEXT,
    evidence_url  TEXT,
    validated_at  TEXT NOT NULL DEFAULT ({SQLITE_TS})
);
CREATE TABLE IF NOT EXISTS payments (
    id              TEXT PRIMARY KEY DEFAULT ({SQLITE_UUID}),
    job_id          TEXT NOT NULL,
    payer_id        TEXT NOT NULL,
    payee_id        TEXT NOT NULL,
    amount          REAL NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'PEN',
    method          TEXT NOT NULL CHECK (method IN ('yape','plin','cash','card','transfer','wallet')),
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','succeeded','failed','refunded')),
    provider_txn_id TEXT,
    created_at      TEXT NOT NULL DEFAULT ({SQLITE_TS}),
    updated_at      TEXT NOT NULL DEFAULT ({SQLITE_TS})
);
CREATE TABLE IF NOT EXISTS documents (
    id              TEXT PRIMARY KEY DEFAULT ({SQLITE_UUID}),
    job_id          TEXT,
    uploader_id     TEXT NOT NULL,
    type            TEXT NOT NULL CHECK (type IN ('contract','work_photo','evidence','cert','other')),
    url             TEXT NOT NULL,
    file_name       TEXT NOT NULL,
    file_size_bytes INTEGER,
    mime_type       TEXT,
    created_at      TEXT NOT NULL DEFAULT ({SQLITE_TS})
);
CREATE TABLE IF NOT EXISTS notifications (
    id           TEXT PRIMARY KEY DEFAULT ({SQLITE_UUID}),
    user_id      TEXT NOT NULL,
    title        TEXT NOT NULL,
    message      TEXT NOT NULL,
    type         TEXT NOT NULL CHECK (type IN ('job_applied','job_assigned','job_completed','review_added','payment','system')),
    read         INTEGER NOT NULL DEFAULT 0,
    reference_id TEXT,
    created_at   TEXT NOT NULL DEFAULT ({SQLITE_TS})
);
CREATE TABLE IF NOT EXISTS commission_rules (
    id           TEXT PRIMARY KEY DEFAULT ({SQLITE_UUID}),
    specialty_id TEXT,
    rate_pct     REAL NOT NULL DEFAULT 15.00,
    min_amount   REAL NOT NULL DEFAULT 0,
    active       INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT NOT NULL DEFAULT ({SQLITE_TS})
);

"""


def _init_sqlite(conn):
    global _seeded
    if _seeded:
        return
    existed = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
    cur = conn.cursor()
    cur.executescript(_SQLITE_SCHEMA)
    conn.commit()
    if not existed:
        _seed_sqlite(conn)
    _seeded = True


def _d(days=0, hours=0):
    return (datetime.now() - timedelta(days=days, hours=hours)).strftime("%Y-%m-%d %H:%M:%S")


from datetime import timedelta  # noqa: E402

PW_PLACEHOLDER = None


def _seed_sqlite(conn):
    from werkzeug.security import generate_password_hash
    pw = generate_password_hash("password123")
    c = conn.cursor()

    # --- Usuarios ---
    users = [
        ("a0000000-0000-0000-0000-000000000001", "admin@rapijob.com", "+51900000001", pw, "admin", True, 60),
        ("a0000000-0000-0000-0000-000000000002", "sup@rapijob.com", "+51900000002", pw, "supervisor", True, 60),
        ("a0000000-0000-0000-0000-000000000010", "rosa.cliente@rapijob.pe", "+51964320010", pw, "client", True, 30),
        ("a0000000-0000-0000-0000-000000000011", "carmen.cliente@rapijob.pe", "+51964320011", pw, "client", True, 30),
        ("a0000000-0000-0000-0000-000000000020", "juan.electrico@rapijob.pe", "+51964320020", pw, "technician", True, 25),
        ("a0000000-0000-0000-0000-000000000021", "carlos.gasfitero@rapijob.pe", "+51964320021", pw, "technician", True, 20),
        ("a0000000-0000-0000-0000-000000000022", "miguel.computo@rapijob.pe", "+51964320022", pw, "technician", True, 18),
        ("a0000000-0000-0000-0000-000000000023", "ana.electro@rapijob.pe", "+51964320023", pw, "technician", True, 22),
        ("a0000000-0000-0000-0000-000000000024", "diana.clima@rapijob.pe", "+51964320024", pw, "technician", True, 16),
        ("a0000000-0000-0000-0000-000000000025", "pedro.servicios@rapijob.pe", "+51964320025", pw, "technician", True, 14),
        ("a0000000-0000-0000-0000-000000000026", "roberto.electrico@rapijob.pe", "+51964320026", pw, "technician", True, 12),
    ]
    for u in users:
        c.execute(
            "INSERT INTO users (id, email, phone, password, role, verified, created_at) VALUES (?,?,?,?,?,?,?)",
            (u[0], u[1], u[2], u[3], u[4], u[5], _d(u[6])))

    # --- Perfiles (Huancayo, El Tambo, Chilca) ---
    profiles = [
        ("a0000000-0000-0000-0000-000000000010", "Rosa", "Huamán", "Ama de casa en El Tambo, Huancayo", -12.0482, -75.2048, "El Tambo, Huancayo", 20, 0, 25),
        ("a0000000-0000-0000-0000-000000000011", "Carmen", "Quispe", "Vivo en Chilca, Huancayo. Necesito ayuda con mis artefactos", -12.0832, -75.1910, "Chilca, Huancayo", 20, 0, 25),
        ("a0000000-0000-0000-0000-000000000020", "Juan", "Pérez", "Electricista certificado. Instalaciones, cortocircuitos y cableado", -12.0490, -75.2060, "El Tambo, Huancayo", 25, 45.00, 20),
        ("a0000000-0000-0000-0000-000000000021", "Carlos", "Ramos", "Gasfitero maestro. Fugas, desatoros, termas y tuberías", -12.0691, -75.2116, "Huancayo Centro", 20, 40.00, 15),
        ("a0000000-0000-0000-0000-000000000022", "Miguel", "Soto", "Técnico en cómputo: formateo, limpieza, redes wifi", -12.0510, -75.2120, "El Tambo, Huancayo", 30, 35.00, 12),
        ("a0000000-0000-0000-0000-000000000023", "Ana", "Flores", "Especialista en electrodomésticos: lavadoras, refrigeradoras, microondas", -12.0810, -75.2030, "Chilca, Huancayo", 25, 50.00, 15),
        ("a0000000-0000-0000-0000-000000000024", "Diana", "López", "Técnica en aire acondicionado: instalación, mantenimiento y recarga de gas", -12.0700, -75.2100, "Huancayo Centro", 30, 60.00, 10),
        ("a0000000-0000-0000-0000-000000000025", "Pedro", "Castro", "Gasfitería y cómputo, atiendo El Tambo, Huancayo y Chilca", -12.0840, -75.1940, "Chilca, Huancayo", 30, 38.00, 10),
        ("a0000000-0000-0000-0000-000000000026", "Roberto", "Jiménez", "Electricidad y electrodomésticos. Más de 10 años de experiencia", -12.0680, -75.2080, "Huancayo Centro", 25, 42.00, 8),
    ]
    for p in profiles:
        c.execute(
            "INSERT INTO profiles (user_id, first_name, last_name, bio, location_lat, location_lng, location_label, service_radius_km, hourly_rate, verified_at, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], _d(p[9]), _d(p[9])))

    # --- Especialidades ---
    specs = [
        ("b0000000-0000-0000-0000-000000000001", "Cómputo", "Mantenimiento y reparación de PC/laptops, formateo y redes wifi"),
        ("b0000000-0000-0000-0000-000000000002", "Electricidad", "Instalaciones eléctricas, cortocircuitos, cableado y tableros"),
        ("b0000000-0000-0000-0000-000000000003", "Gasfitería", "Fugas de agua, desatoros, grifería, termas y tuberías"),
        ("b0000000-0000-0000-0000-000000000004", "Aire Acondicionado", "Instalación, mantenimiento y recarga de gas de climatización"),
        ("b0000000-0000-0000-0000-000000000005", "Electrodomésticos", "Reparación de lavadoras, refrigeradoras, microondas y artefactos"),
    ]
    for s in specs:
        c.execute("INSERT INTO specialties (id, name, description) VALUES (?,?,?)", s)

    # --- Técnicos por especialidad ---
    tech_specs = [
        ("a0000000-0000-0000-0000-000000000020", "b0000000-0000-0000-0000-000000000002", 8),
        ("a0000000-0000-0000-0000-000000000021", "b0000000-0000-0000-0000-000000000003", 10),
        ("a0000000-0000-0000-0000-000000000022", "b0000000-0000-0000-0000-000000000001", 6),
        ("a0000000-0000-0000-0000-000000000023", "b0000000-0000-0000-0000-000000000005", 9),
        ("a0000000-0000-0000-0000-000000000024", "b0000000-0000-0000-0000-000000000004", 7),
        ("a0000000-0000-0000-0000-000000000025", "b0000000-0000-0000-0000-000000000003", 5),
        ("a0000000-0000-0000-0000-000000000025", "b0000000-0000-0000-0000-000000000001", 3),
        ("a0000000-0000-0000-0000-000000000026", "b0000000-0000-0000-0000-000000000002", 6),
        ("a0000000-0000-0000-0000-000000000026", "b0000000-0000-0000-0000-000000000005", 4),
    ]
    for ts in tech_specs:
        c.execute("INSERT INTO technician_specialties (technician_id, specialty_id, experience_years) VALUES (?,?,?)", ts)

    # --- Certificaciones ---
    certs = [
        ("c0000000-0000-0000-0000-000000000001", "Electricista Básico", "SENATI"),
        ("c0000000-0000-0000-0000-000000000002", "Gasfitero Maestro", "SENATI"),
        ("c0000000-0000-0000-0000-000000000003", "Técnico en Computación CCNA", "Cisco"),
        ("c0000000-0000-0000-0000-000000000004", "Reparación de Electrodomésticos", "CETPRO Huancayo"),
        ("c0000000-0000-0000-0000-000000000005", "Instalación y Mantenimiento de Aire Acondicionado", "SENATI"),
    ]
    for cr in certs:
        c.execute("INSERT INTO certifications (id, name, issuing_body) VALUES (?,?,?)", cr)

    tech_certs = [
        ("d0000000-0000-0000-0000-000000000001", "a0000000-0000-0000-0000-000000000020", "c0000000-0000-0000-0000-000000000001", "https://docs.rapijob.pe/juan_electrico.pdf", "2023-03-01", "2026-03-01"),
        ("d0000000-0000-0000-0000-000000000002", "a0000000-0000-0000-0000-000000000021", "c0000000-0000-0000-0000-000000000002", "https://docs.rapijob.pe/carlos_gasfitero.pdf", "2022-06-01", "2027-06-01"),
        ("d0000000-0000-0000-0000-000000000003", "a0000000-0000-0000-0000-000000000022", "c0000000-0000-0000-0000-000000000003", "https://docs.rapijob.pe/miguel_ccna.pdf", "2023-09-01", "2026-09-01"),
        ("d0000000-0000-0000-0000-000000000004", "a0000000-0000-0000-0000-000000000023", "c0000000-0000-0000-0000-000000000004", "https://docs.rapijob.pe/ana_electro.pdf", "2024-01-01", "2028-01-01"),
        ("d0000000-0000-0000-0000-000000000005", "a0000000-0000-0000-0000-000000000024", "c0000000-0000-0000-0000-000000000005", "https://docs.rapijob.pe/diana_hvac.pdf", "2023-05-01", "2027-05-01"),
        ("d0000000-0000-0000-0000-000000000006", "a0000000-0000-0000-0000-000000000025", "c0000000-0000-0000-0000-000000000002", "https://docs.rapijob.pe/pedro_gas.pdf", "2023-11-01", "2028-11-01"),
        ("d0000000-0000-0000-0000-000000000007", "a0000000-0000-0000-0000-000000000026", "c0000000-0000-0000-0000-000000000001", "https://docs.rapijob.pe/roberto_electro.pdf", "2022-08-01", "2026-08-01"),
    ]
    for tc in tech_certs:
        c.execute(
            "INSERT INTO technician_certifications (id, technician_id, certification_id, document_url, issued_at, expires_at, validation_status, validated_by, validated_at) "
            "VALUES (?,?,?,?,?,?,'valid','a0000000-0000-0000-0000-000000000001',?)",
            (tc[0], tc[1], tc[2], tc[3], tc[4], tc[5], _d(10)))

    # --- Comisiones ---
    c.execute("INSERT INTO commission_rules (id, specialty_id, rate_pct, min_amount, active) VALUES (?,NULL,15.00,0,1)",
              ("e0000000-0000-0000-0000-000000000001",))

    # --- Trabajos (S/. , Huancayo / El Tambo / Chilca) ---
    jobs = [
        ("10010000-1001-4001-9001-000000000001", "a0000000-0000-0000-0000-000000000010", "Cortocircuito en toma de corriente", "Enchufe que chispea en la sala, quiero que lo revisen pronto",
         "b0000000-0000-0000-0000-000000000002", 50, 80, -12.0482, -75.2048, "Jr. Huancavelica 234, El Tambo", "high", "open", None, None, None, 0),
        ("10010000-1002-4001-9001-000000000002", "a0000000-0000-0000-0000-000000000011", "Lavadora no centrifuga", "La lavadora deja la ropa mojada, no centrifuga desde la semana pasada",
         "b0000000-0000-0000-0000-000000000005", 60, 120, -12.0832, -75.1910, "Av. Los Andes 150, Chilca", "normal", "open", None, None, None, 1),
        ("10010000-1003-4001-9001-000000000003", "a0000000-0000-0000-0000-000000000010", "Fuga de agua en la cocina", "Se moja todo el piso de la cocina, gotea debajo del lavadero",
         "b0000000-0000-0000-0000-000000000003", 40, 90, -12.0482, -75.2048, "Jr. Puno 450, El Tambo", "urgent", "open", None, None, None, 0),
        ("10010000-1004-4001-9001-000000000004", "a0000000-0000-0000-0000-000000000011", "Formateo y limpieza de laptop", "Laptop muy lenta, necesita formateo y antivirus",
         "b0000000-0000-0000-0000-000000000001", 60, 100, -12.0832, -75.1910, "Jr. Cajamarca 88, Chilca", "normal", "completed", None, "a0000000-0000-0000-0000-000000000022", 3, 1),
        ("10010000-1005-4001-9001-000000000005", "a0000000-0000-0000-0000-000000000010", "Aire acondicionado no enfría", "El split suelta aire tibio, creo que le falta gas",
         "b0000000-0000-0000-0000-000000000004", 90, 180, -12.0700, -75.2100, "Av. Giráldez 700, Huancayo", "high", "completed", None, "a0000000-0000-0000-0000-000000000024", 6, 0),
        ("10010000-1006-4001-9001-000000000006", "a0000000-0000-0000-0000-000000000011", "Cambio de llave del baño", "La llave del baño gotea y no cierra bien",
         "b0000000-0000-0000-0000-000000000003", 45, 80, -12.0832, -75.1910, "Jr. Sucre 320, Chilca", "low", "completed", None, "a0000000-0000-0000-0000-000000000021", 5, 0),
        ("10010000-1007-4001-9001-000000000007", "a0000000-0000-0000-0000-000000000010", "Refrigeradora no congela", "El congelador ya no congela, la comida se malogra",
         "b0000000-0000-0000-0000-000000000005", 100, 200, -12.0691, -75.2116, "Jr. Amazonas 210, Huancayo", "urgent", "completed", None, "a0000000-0000-0000-0000-000000000023", 4, 0),
        ("10010000-1008-4001-9001-000000000008", "a0000000-0000-0000-0000-000000000011", "Instalar spot LED en sala", "Quiero que cambien mi luz del techo por 4 spots LED",
         "b0000000-0000-0000-0000-000000000002", 60, 120, -12.0482, -75.2048, "Urb. San Carlos Mz B Lt 12, El Tambo", "normal", "in_progress", None, "a0000000-0000-0000-0000-000000000020", 1, 0),
        ("10010000-1009-4001-9001-000000000009", "a0000000-0000-0000-0000-000000000010", "PC no enciende, posible fuente dañada", "La computadora de escritorio no prende, quizá la fuente",
         "b0000000-0000-0000-0000-000000000001", 70, 130, -12.0482, -75.2048, "Jr. Huancayo 120, El Tambo", "normal", "open", None, None, None, 0),
        ("10010000-1010-4001-9001-000000000010", "a0000000-0000-0000-0000-000000000011", "Mantenimiento de split de dormitorio", "Limpieza y mantenimiento general del aire acondicionado",
         "b0000000-0000-0000-0000-000000000004", 80, 150, -12.0832, -75.1910, "Av. Mariscal Castilla 980, Chilca", "normal", "open", None, None, None, 1),
    ]
    for j in jobs:
        c.execute(
            "INSERT INTO jobs (id, client_id, title, description, specialty_id, budget_min, budget_max, location_lat, location_lng, location_label, urgency, status, deadline_at, assigned_to, completed_at, is_remote, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (j[0], j[1], j[2], j[3], j[4], j[5], j[6], j[7], j[8], j[9], j[10], j[11], j[12], j[13], _d(j[14]) if j[14] else None, j[15], _d(0)))

    # --- Postulaciones / cotizaciones (con precio en S/.) ---
    apps = [
        ("60010000-1001-4001-9006-000000000001", "10010000-1001-4001-9001-000000000001", "a0000000-0000-0000-0000-000000000020", 65.00, "Puedo ir mañana temprano a revisar el cortocircuito", "applied", 0),
        ("60010000-1002-4001-9006-000000000002", "10010000-1001-4001-9001-000000000001", "a0000000-0000-0000-0000-000000000026", 70.00, "Electricista colegiado, reviso toma e instalación completa", "applied", 0),
        ("60010000-1003-4001-9006-000000000003", "10010000-1002-4001-9001-000000000002", "a0000000-0000-0000-0000-000000000023", 85.00, "Reviso el motor de centrifugado en el momento", "applied", 1),
        ("60010000-1004-4001-9006-000000000004", "10010000-1002-4001-9001-000000000002", "a0000000-0000-0000-0000-000000000026", 100.00, "Especialista en lavadoras, diagnóstico sin costo", "applied", 1),
        ("60010000-1005-4001-9006-000000000005", "10010000-1003-4001-9001-000000000003", "a0000000-0000-0000-0000-000000000021", 55.00, "Listo para hoy mismo, llevo repuestos de empaque", "applied", 0),
        ("60010000-1006-4001-9006-000000000006", "10010000-1003-4001-9001-000000000003", "a0000000-0000-0000-0000-000000000025", 60.00, "Atiendo urgencias, llego en 30 minutos", "applied", 0),
        ("60010000-1007-4001-9006-000000000007", "10010000-1004-4001-9001-000000000004", "a0000000-0000-0000-0000-000000000022", 80.00, "Formateo + instalación de programas básicos", "accepted", 4),
        ("60010000-1008-4001-9006-000000000008", "10010000-1005-4001-9001-000000000005", "a0000000-0000-0000-0000-000000000024", 150.00, "Carga de gas y limpieza de filtros incluida", "accepted", 6),
        ("60010000-1009-4001-9006-000000000009", "10010000-1006-4001-9001-000000000006", "a0000000-0000-0000-0000-000000000021", 70.00, "Cambio de llave, incluye empaquetaduras", "accepted", 5),
        ("60010000-1010-4001-9006-000000000010", "10010000-1007-4001-9001-000000000007", "a0000000-0000-0000-0000-000000000023", 180.00, "Reparación de compresor con garantía de 30 días", "accepted", 4),
        ("60010000-1011-4001-9006-000000000011", "10010000-1008-4001-9001-000000000008", "a0000000-0000-0000-0000-000000000020", 90.00, "Instalación de 4 spots LED incluido material", "accepted", 1),
        ("60010000-1012-4001-9006-000000000012", "10010000-1009-4001-9001-000000000009", "a0000000-0000-0000-0000-000000000022", 95.00, "Reviso la fuente y dejo la PC operativa", "applied", 0),
        ("60010000-1013-4001-9006-000000000013", "10010000-1009-4001-9001-000000000009", "a0000000-0000-0000-0000-000000000025", 110.00, "Técnico en cómputo, vengo con fuente de repuesto", "applied", 0),
        ("60010000-1014-4001-9006-000000000014", "10010000-1010-4001-9001-000000000010", "a0000000-0000-0000-0000-000000000024", 130.00, "Mantenimiento premium con limpieza de evaporadora", "applied", 1),
    ]
    for a in apps:
        c.execute(
            "INSERT INTO job_applications (id, job_id, technician_id, proposed_price, cover_letter, status, created_at) VALUES (?,?,?,?,?,?,?)",
            (a[0], a[1], a[2], a[3], a[4], a[5], _d(a[6])))

    # --- Asignaciones ---
    assigns = [
        ("10010000-1004-4001-9001-000000000004", "a0000000-0000-0000-0000-000000000022", "a0000000-0000-0000-0000-000000000011", 3),
        ("10010000-1005-4001-9001-000000000005", "a0000000-0000-0000-0000-000000000024", "a0000000-0000-0000-0000-000000000010", 6),
        ("10010000-1006-4001-9001-000000000006", "a0000000-0000-0000-0000-000000000021", "a0000000-0000-0000-0000-000000000011", 5),
        ("10010000-1007-4001-9001-000000000007", "a0000000-0000-0000-0000-000000000023", "a0000000-0000-0000-0000-000000000010", 4),
        ("10010000-1008-4001-9001-000000000008", "a0000000-0000-0000-0000-000000000020", "a0000000-0000-0000-0000-000000000011", 1),
    ]
    for asg in assigns:
        ct = _d(asg[3])
        c.execute(
            "INSERT INTO job_assignments (job_id, technician_id, assigned_by, assigned_at, accepted_at) VALUES (?,?,?,?,?)",
            (asg[0], asg[1], asg[2], ct, ct))

    # --- Reseñas ---
    reviews = [
        ("30010000-1001-4001-9003-000000000001", "10010000-1004-4001-9001-000000000004", "a0000000-0000-0000-0000-000000000011", "a0000000-0000-0000-0000-000000000022", 5, "Muy rápido y la laptop quedó como nueva", 3),
        ("30010000-1002-4001-9003-000000000002", "10010000-1005-4001-9001-000000000005", "a0000000-0000-0000-0000-000000000010", "a0000000-0000-0000-0000-000000000024", 5, "Enfrió rápido, muy amable y puntual", 6),
        ("30010000-1003-4001-9003-000000000003", "10010000-1006-4001-9001-000000000006", "a0000000-0000-0000-0000-000000000011", "a0000000-0000-0000-0000-000000000021", 4, "Buen trabajo, ya no gotea", 5),
        ("30010000-1004-4001-9003-000000000004", "10010000-1007-4001-9001-000000000007", "a0000000-0000-0000-0000-000000000010", "a0000000-0000-0000-0000-000000000023", 5, "Excelente, la refrigeradora ya congela bien", 4),
    ]
    for r in reviews:
        c.execute(
            "INSERT INTO job_reviews (id, job_id, reviewer_id, reviewee_id, rating, comment, created_at) VALUES (?,?,?,?,?,?,?)",
            (r[0], r[1], r[2], r[3], r[4], r[5], _d(r[6])))

    c.execute("INSERT INTO review_validations (id, job_id, supervisor_id, status, score, notes, validated_at) VALUES (?,?,?,?,?,?,?)",
              ("40010000-1001-4001-9004-000000000001", "10010000-1004-4001-9001-000000000004",
               "a0000000-0000-0000-0000-000000000002", "approved", 9.0, "OK", _d(2)))

    # --- Pagos (Yape / Plin / Efectivo) ---
    pays = [
        ("20010000-1001-4001-9002-000000000001", "10010000-1004-4001-9001-000000000004", "a0000000-0000-0000-0000-000000000011", "a0000000-0000-0000-0000-000000000022", 80.00, "plin", "succeeded", 3),
        ("20010000-1002-4001-9002-000000000002", "10010000-1005-4001-9001-000000000005", "a0000000-0000-0000-0000-000000000010", "a0000000-0000-0000-0000-000000000024", 150.00, "yape", "succeeded", 6),
        ("20010000-1003-4001-9002-000000000003", "10010000-1006-4001-9001-000000000006", "a0000000-0000-0000-0000-000000000011", "a0000000-0000-0000-0000-000000000021", 70.00, "cash", "pending", 5),
        ("20010000-1004-4001-9002-000000000004", "10010000-1007-4001-9001-000000000007", "a0000000-0000-0000-0000-000000000010", "a0000000-0000-0000-0000-000000000023", 180.00, "yape", "succeeded", 4),
        ("20010000-1005-4001-9002-000000000005", "10010000-1008-4001-9001-000000000008", "a0000000-0000-0000-0000-000000000011", "a0000000-0000-0000-0000-000000000020", 90.00, "plin", "succeeded", 1),
    ]
    for pay in pays:
        c.execute(
            "INSERT INTO payments (id, job_id, payer_id, payee_id, amount, currency, method, status, provider_txn_id, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (pay[0], pay[1], pay[2], pay[3], pay[4], "PEN", pay[5], pay[6], "txn_" + pay[0][-8:], _d(pay[7])))

    # --- Notificaciones ---
    notes = [
        ("70010000-1001-4001-9007-000000000001", "a0000000-0000-0000-0000-000000000020", "Nueva solicitud", "Hay una persona esperando una cotización de Electricidad", "job_applied", "10010000-1001-4001-9001-000000000001", 0),
        ("70010000-1002-4001-9007-000000000002", "a0000000-0000-0000-0000-000000000010", "Cotización recibida", "Juan Pérez te envió una cotización por S/. 65.00", "job_applied", "10010000-1001-4001-9001-000000000001", 0),
    ]
    for n in notes:
        c.execute(
            "INSERT INTO notifications (id, user_id, title, message, type, reference_id, read, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (n[0], n[1], n[2], n[3], n[4], n[5], n[6], _d(0)))

    conn.commit()

    c.execute("UPDATE notifications SET read = 1 WHERE read = 0 AND id = '70010000-1001-4001-9007-000000000001'")
    conn.commit()