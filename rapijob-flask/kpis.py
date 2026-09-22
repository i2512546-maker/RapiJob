"""
RapiJob — Rutas de KPIs (Blueprint de Flask)

Endpoints (sección 7 del documento técnico):
    GET  /kpis              -> Panel de métricas según rol del usuario (HTML, Jinja2)
    GET  /api/kpis          -> API en formato JSON de los KPIs
    POST /api/kpi/snapshot  -> Calcular / refrescar KPIs de la plataforma

Adaptado a la estructura real de la app Flask:
- Persistencia con db.py (query_db / execute_db, doble motor Postgres/SQLite).
- Autenticación por sesión: `session["role"]` / `session["user_id"]`, con los
  decoradores `login_required` y `role_required(*roles)` definidos en `app.py`.
- Se registra al final de `app.py` con `app.register_blueprint(kpis_bp)`
  (import diferido para evitar import circular: app.py -> kpis -> app.py).

Ajustes respecto al snippet original:
- `mv_platform_metrics` usa la columna `wk` (no `week`).
- `kpi_snapshots` usa (entity_type, entity_id, metric_name, metric_value,
  period_start, period_end); no existen columnas `value` ni `created_at`.
- En SQLite no hay vistas materializadas: el REFRESH se omite (is_postgres()).
- `v_client_metrics` solo existe en PostgreSQL (db/kpis.sql); para el fallback
  SQLite se agregó la misma vista en db.py.
"""

from datetime import timedelta

from flask import Blueprint, render_template, jsonify, session

from db import query_db, execute_db, is_postgres

# El Blueprint se define ANTES de importar los decoradores de app.py para que
# el import circular (app.py -> kpis.py -> app.py) se resuelva sin error:
# cuando app.py llega al registro al final, `kpis_bp` ya existe en el módulo.
kpis_bp = Blueprint("kpis", __name__)

from app import login_required, role_required  # noqa: E402


# ------------------------------------------------------------
# GET /kpis — Panel de métricas (según rol del usuario logueado)
# ------------------------------------------------------------
@kpis_bp.route("/kpis", methods=["GET"])
@login_required
def kpis_dashboard():
    role = session["role"]
    user_id = session["user_id"]

    if role == "technician":
        metrics = query_db(
            "SELECT * FROM v_tech_metrics WHERE technician_id = %s::uuid",
            [user_id], one=True
        )
        return render_template("kpis/technician.html", metrics=metrics)

    if role == "client":
        metrics = query_db(
            "SELECT * FROM v_client_metrics WHERE client_id = %s::uuid",
            [user_id], one=True
        )
        return render_template("kpis/client.html", metrics=metrics)

    # admin / supervisor: panel completo de la plataforma (últimas 12 semanas)
    weeks = query_db("SELECT * FROM mv_platform_metrics ORDER BY wk DESC LIMIT 12")
    return render_template("kpis/platform.html", weeks=weeks)


# ------------------------------------------------------------
# GET /api/kpis — versión JSON del mismo panel
# ------------------------------------------------------------
@kpis_bp.route("/api/kpis", methods=["GET"])
@login_required
def api_kpis():
    role = session["role"]
    user_id = session["user_id"]

    if role == "technician":
        row = query_db(
            "SELECT * FROM v_tech_metrics WHERE technician_id = %s::uuid",
            [user_id], one=True
        )
        return jsonify(dict(row) if row else {})

    if role == "client":
        row = query_db(
            "SELECT * FROM v_client_metrics WHERE client_id = %s::uuid",
            [user_id], one=True
        )
        return jsonify(dict(row) if row else {})

    rows = query_db("SELECT * FROM mv_platform_metrics ORDER BY wk DESC LIMIT 12")
    return jsonify([dict(r) for r in rows])


# ------------------------------------------------------------
# POST /api/kpi/snapshot — recalcula los KPIs de plataforma
# (solo admin/supervisor) y guarda un snapshot en kpi_snapshots
# ------------------------------------------------------------
@kpis_bp.route("/api/kpi/snapshot", methods=["POST"])
@login_required
@role_required("admin", "supervisor")
def api_kpi_snapshot():
    try:
        # 1. Refrescar la vista materializada (solo PostgreSQL)
        if is_postgres():
            execute_db("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_platform_metrics")

        # 2. Tomar la semana más reciente y guardarla como snapshot histórico
        latest = query_db(
            "SELECT * FROM mv_platform_metrics ORDER BY wk DESC LIMIT 1", one=True
        )
        if latest:
            wk = latest["wk"]
            existing = query_db(
                "SELECT id FROM kpi_snapshots "
                "WHERE entity_type = 'platform' AND period_start = %s",
                [wk], one=True
            )
            if not existing:
                period_end = wk + timedelta(days=6)
                for metric_name, value in latest.items():
                    if metric_name == "wk":
                        continue
                    execute_db(
                        "INSERT INTO kpi_snapshots "
                        "(entity_type, entity_id, metric_name, metric_value, period_start, period_end) "
                        "VALUES ('platform', NULL, %s, %s, %s, %s)",
                        [metric_name, float(value), wk, period_end]
                    )
        return jsonify(dict(latest) if latest else {}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500