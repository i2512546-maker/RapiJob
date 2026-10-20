import os
from datetime import datetime, timedelta, date
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, g
)
import bcrypt
from config import Config
from db import query_db, execute_db, get_db, is_mysql

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
app.jinja_env.globals["now"] = date.today()


# ---------------------------------------------------------------------------
# Contraseñas (bcrypt)
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, clave_hash: str) -> bool:
    if not clave_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), clave_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesión", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get("role") not in roles:
                flash("No tienes permiso", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return decorated
    return decorator


@app.before_request
def load_user():
    g.user = None
    if "user_id" in session:
        g.user = query_db(
            "SELECT * FROM usuarios WHERE id = %s",
            [session["user_id"]], one=True
        )


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return redirect(url_for("jobs"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = query_db(
            "SELECT * FROM usuarios WHERE email = %s",
            [email], one=True
        )
        if user and verify_password(password, user["clave_hash"]):
            session["user_id"] = user["id"]
            session["role"] = user["rol"]
            flash(f"Bienvenido, {user['nombre']}", "success")
            return redirect(url_for("dashboard"))
        flash("Credenciales inválidas", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        telefono = request.form.get("telefono", "").strip()
        rol = request.form.get("rol", "cliente").strip()
        ciudad = request.form.get("ciudad", "").strip()

        errors = []
        if not nombre:
            errors.append("Escribe tu nombre.")
        if not email or "@" not in email:
            errors.append("Escribe un email válido.")
        if len(password) < 6:
            errors.append("La contraseña debe tener al menos 6 caracteres.")
        if rol not in ("cliente", "proveedor"):
            rol = "cliente"

        existing = query_db("SELECT id FROM usuarios WHERE email = %s", [email], one=True)
        if existing:
            errors.append("El email ya está registrado.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html", form=request.form)

        user_id = query_db(
            "INSERT INTO usuarios (nombre, email, clave_hash, telefono, rol, ciudad) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            [nombre, email, hash_password(password), telefono or None, rol, ciudad or None]
        )
        session["user_id"] = user_id
        session["role"] = rol
        flash("Registro exitoso.", "success")
        return redirect(url_for("dashboard"))
    return render_template("register.html", form={})


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    role = session["role"]
    user_id = session["user_id"]

    if role == "proveedor":
        stats = query_db(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN s.estado = 'terminada' THEN 1 ELSE 0 END) as terminadas, "
            "SUM(CASE WHEN s.estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes "
            "FROM solicitudes s JOIN servicios se ON se.id = s.servicio_id "
            "WHERE se.proveedor_id = %s",
            [user_id], one=True
        )
        servicios = query_db(
            "SELECT se.*, c.nombre as categoria FROM servicios se "
            "JOIN categorias c ON c.id = se.categoria_id "
            "WHERE se.proveedor_id = %s ORDER BY se.id DESC",
            [user_id]
        )
        solicitudes = query_db(
            "SELECT s.*, se.titulo as servicio_titulo, u.nombre as cliente_nombre "
            "FROM solicitudes s "
            "JOIN servicios se ON se.id = s.servicio_id "
            "JOIN usuarios u ON u.id = s.cliente_id "
            "WHERE se.proveedor_id = %s ORDER BY s.fecha DESC LIMIT 10",
            [user_id]
        )
        return render_template("dashboard.html", stats=stats, servicios=servicios,
                               solicitudes=solicitudes, role=role)

    elif role == "cliente":
        stats = query_db(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN estado = 'terminada' THEN 1 ELSE 0 END) as terminadas, "
            "SUM(CASE WHEN estado = 'cancelada' THEN 1 ELSE 0 END) as canceladas "
            "FROM solicitudes WHERE cliente_id = %s",
            [user_id], one=True
        )
        solicitudes = query_db(
            "SELECT s.*, se.titulo as servicio_titulo, se.precio, se.ubicacion, "
            "u.nombre as proveedor_nombre "
            "FROM solicitudes s "
            "JOIN servicios se ON se.id = s.servicio_id "
            "JOIN usuarios u ON u.id = se.proveedor_id "
            "WHERE s.cliente_id = %s ORDER BY s.fecha DESC LIMIT 10",
            [user_id]
        )
        categorias = query_db("SELECT id, nombre FROM categorias ORDER BY nombre")
        return render_template("dashboard.html", stats=stats, solicitudes=solicitudes,
                               role=role, categorias=categorias)

    else:
        stats = query_db(
            "SELECT "
            "(SELECT COUNT(*) FROM usuarios WHERE rol = 'proveedor') as proveedores, "
            "(SELECT COUNT(*) FROM usuarios WHERE rol = 'cliente') as clientes, "
            "(SELECT COUNT(*) FROM servicios) as servicios, "
            "(SELECT COUNT(*) FROM solicitudes) as solicitudes", one=True
        )
        recientes = query_db(
            "SELECT s.*, se.titulo as servicio_titulo, u.nombre as cliente_nombre "
            "FROM solicitudes s JOIN servicios se ON se.id = s.servicio_id "
            "JOIN usuarios u ON u.id = s.cliente_id ORDER BY s.fecha DESC LIMIT 10"
        )
        return render_template("dashboard.html", stats=stats, recientes=recientes, role=role)


# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
@app.route("/kpis")
@login_required
def kpis():
    role = session["role"]
    user_id = session["user_id"]
    period = request.args.get("period", "30d")
    days = int(period.replace("d", "")) if "d" in period else 30
    since = date.today() - timedelta(days=days)

    if role == "proveedor":
        metrics = query_db(
            "SELECT COUNT(*) as total_solicitudes, "
            "SUM(CASE WHEN s.estado = 'terminada' THEN 1 ELSE 0 END) as terminadas, "
            "SUM(CASE WHEN s.estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes, "
            "COALESCE(AVG(c.puntaje), 0) as avg_rating, "
            "COUNT(c.id) as total_calificaciones "
            "FROM servicios se "
            "LEFT JOIN solicitudes s ON s.servicio_id = se.id AND s.fecha >= %s "
            "LEFT JOIN calificaciones c ON c.solicitud_id = s.id "
            "WHERE se.proveedor_id = %s",
            [since, user_id], one=True
        )
        return render_template("kpis.html", metrics=metrics, period=period, role=role)

    elif role == "cliente":
        stats = query_db(
            "SELECT COUNT(*) as total_solicitudes, "
            "SUM(CASE WHEN estado = 'terminada' THEN 1 ELSE 0 END) as terminadas, "
            "SUM(CASE WHEN estado = 'cancelada' THEN 1 ELSE 0 END) as canceladas "
            "FROM solicitudes WHERE cliente_id = %s AND fecha >= %s",
            [user_id, since], one=True
        )
        return render_template("kpis.html", stats=stats, period=period, role=role)

    else:
        stats = query_db(
            "SELECT "
            "(SELECT COUNT(*) FROM usuarios WHERE rol = 'proveedor') as proveedores, "
            "(SELECT COUNT(*) FROM usuarios WHERE rol = 'cliente') as clientes, "
            "(SELECT COUNT(*) FROM servicios) as servicios, "
            "(SELECT COUNT(*) FROM solicitudes) as solicitudes, "
            "(SELECT COUNT(*) FROM solicitudes WHERE estado = 'terminada') as terminadas, "
            "(SELECT COUNT(*) FROM solicitudes WHERE estado = 'cancelada') as canceladas, "
            "(SELECT COALESCE(AVG(puntaje), 0) FROM calificaciones) as avg_rating", one=True
        )
        return render_template("kpis.html", stats=stats, period=period, role=role)


@app.route("/api/kpis")
@login_required
def api_kpis():
    role = request.args.get("role", session["role"])
    entity_id = request.args.get("entity_id", session["user_id"])
    period = request.args.get("period", "30d")
    days = int(period.replace("d", "")) if "d" in period else 30
    since = date.today() - timedelta(days=days)

    if role == "proveedor":
        metrics = query_db(
            "SELECT COUNT(*) as total_solicitudes, "
            "SUM(CASE WHEN s.estado = 'terminada' THEN 1 ELSE 0 END) as terminadas, "
            "COALESCE(AVG(c.puntaje), 0) as avg_rating "
            "FROM servicios se "
            "LEFT JOIN solicitudes s ON s.servicio_id = se.id AND s.fecha >= %s "
            "LEFT JOIN calificaciones c ON c.solicitud_id = s.id "
            "WHERE se.proveedor_id = %s",
            [since, entity_id], one=True
        )
    elif role in ("platform", "admin"):
        metrics = query_db(
            "SELECT "
            "(SELECT COUNT(*) FROM usuarios) as usuarios, "
            "(SELECT COUNT(*) FROM servicios) as servicios, "
            "(SELECT COUNT(*) FROM solicitudes) as solicitudes, "
            "(SELECT COUNT(*) FROM solicitudes WHERE estado = 'terminada') as terminadas, "
            "(SELECT COALESCE(AVG(puntaje), 0) FROM calificaciones) as avg_rating", one=True
        )
    else:
        return jsonify({"error": "unknown role"}), 400

    return jsonify({"metrics": dict(metrics) if metrics else None})


# ---------------------------------------------------------------------------
# Proveedores (ex-técnicos)
# ---------------------------------------------------------------------------
@app.route("/proveedores")
@app.route("/technicians")
def technicians():
    search = request.args.get("q", "")
    cat = request.args.get("categoria", request.args.get("specialty", ""))
    query = """
        SELECT u.id, u.nombre, u.email, u.ciudad,
               COUNT(DISTINCT se.id) as servicios_count,
               COALESCE(AVG(c.puntaje), 0) as rating_avg
        FROM usuarios u
        LEFT JOIN servicios se ON se.proveedor_id = u.id
        LEFT JOIN solicitudes s ON s.servicio_id = se.id
        LEFT JOIN calificaciones c ON c.solicitud_id = s.id
        WHERE u.rol = 'proveedor'
    """
    params = []
    if search:
        query += " AND (u.nombre LIKE %s OR u.email LIKE %s OR u.ciudad LIKE %s)"
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    if cat:
        query += """
            AND u.id IN (
                SELECT se2.proveedor_id FROM servicios se2
                JOIN categorias ca ON ca.id = se2.categoria_id
                WHERE ca.nombre LIKE %s
            )
        """
        params.append(f"%{cat}%")
    query += " GROUP BY u.id, u.nombre, u.email, u.ciudad ORDER BY rating_avg DESC, servicios_count DESC"
    techs = query_db(query, params)
    categorias = query_db("SELECT nombre FROM categorias ORDER BY nombre")
    return render_template("technicians.html", technicians=techs, specialties=categorias,
                           search=search, selected_spec=cat)


@app.route("/technician/<user_id>")
@app.route("/proveedor/<user_id>")
def technician_detail(user_id):
    tech = query_db(
        "SELECT * FROM usuarios WHERE id = %s AND rol = 'proveedor'",
        [user_id], one=True
    )
    if not tech:
        flash("Proveedor no encontrado", "danger")
        return redirect(url_for("technicians"))

    servicios = query_db(
        "SELECT se.*, c.nombre as categoria FROM servicios se "
        "JOIN categorias c ON c.id = se.categoria_id "
        "WHERE se.proveedor_id = %s ORDER BY se.id DESC",
        [user_id]
    )
    rating = query_db(
        "SELECT COALESCE(AVG(c.puntaje), 0) as avg_rating, COUNT(*) as total "
        "FROM calificaciones c "
        "JOIN solicitudes s ON s.id = c.solicitud_id "
        "JOIN servicios se ON se.id = s.servicio_id "
        "WHERE se.proveedor_id = %s",
        [user_id], one=True
    )
    reviews = query_db(
        "SELECT c.puntaje, c.comentario, s.fecha, se.titulo "
        "FROM calificaciones c "
        "JOIN solicitudes s ON s.id = c.solicitud_id "
        "JOIN servicios se ON se.id = s.servicio_id "
        "WHERE se.proveedor_id = %s ORDER BY c.id DESC LIMIT 10",
        [user_id]
    )
    return render_template("technician_detail.html", tech=tech, servicios=servicios,
                           rating=rating, reviews=reviews)


# ---------------------------------------------------------------------------
# Servicios (buscador) + Solicitudes
# ---------------------------------------------------------------------------
@app.route("/jobs")
@app.route("/servicios")
def jobs():
    categoria = request.args.get("categoria", "")
    ubicacion = request.args.get("ubicacion", "").strip()
    try:
        precio_max = float(request.args.get("precio_max", ""))
    except (TypeError, ValueError):
        precio_max = None

    query = """
        SELECT se.*, c.nombre as categoria, u.nombre as proveedor_nombre, u.ciudad,
               COALESCE(AVG(cal.puntaje), 0) as rating_avg
        FROM servicios se
        JOIN categorias c ON c.id = se.categoria_id
        JOIN usuarios u ON u.id = se.proveedor_id
        LEFT JOIN solicitudes so ON so.servicio_id = se.id
        LEFT JOIN calificaciones cal ON cal.solicitud_id = so.id
        WHERE 1=1
    """
    params = []
    if categoria:
        query += " AND c.nombre = %s"
        params.append(categoria)
    if ubicacion:
        query += " AND se.ubicacion LIKE %s"
        params.append(f"%{ubicacion}%")
    if precio_max is not None:
        query += " AND se.precio <= %s"
        params.append(precio_max)
    query += " GROUP BY se.id, c.nombre, u.nombre, u.ciudad ORDER BY se.id DESC LIMIT 50"
    servicio_list = query_db(query, params)
    categorias = query_db("SELECT nombre FROM categorias ORDER BY nombre")
    return render_template("jobs.html", servicios=servicio_list, categorias=categorias,
                           selected_categoria=categoria, ubicacion=ubicacion,
                           precio_max=request.args.get("precio_max", ""))


@app.route("/jobs/new", methods=["GET", "POST"])
@login_required
@role_required("proveedor", "admin")
def job_new():
    categorias = query_db("SELECT id, nombre FROM categorias ORDER BY nombre")
    selected_categoria = request.args.get("categoria_id", "")
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        categoria_id = request.form.get("categoria_id", "").strip()
        ubicacion = request.form.get("ubicacion", "").strip()
        try:
            precio = float(request.form.get("precio", "0"))
        except (TypeError, ValueError):
            precio = -1

        errors = []
        if not titulo or len(titulo) < 5:
            errors.append("Escribe un título de al menos 5 caracteres.")
        if not descripcion:
            errors.append("Describe el servicio que ofreces.")
        if not categoria_id:
            errors.append("Selecciona una categoría.")
        if not ubicacion:
            errors.append("Indica tu ubicación (distrito o ciudad).")
        if precio < 0:
            errors.append("Ingresa un precio válido en Soles.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("job_form.html", categorias=categorias,
                                   selected_categoria=categoria_id, form=request.form)

        execute_db(
            "INSERT INTO servicios (proveedor_id, categoria_id, titulo, descripcion, precio, ubicacion) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            [session["user_id"], categoria_id, titulo, descripcion, precio, ubicacion]
        )
        flash("¡Servicio publicado! Ya puedes recibir solicitudes.", "success")
        return redirect(url_for("jobs"))
    return render_template("job_form.html", categorias=categorias,
                           selected_categoria=selected_categoria, form={})


@app.route("/job/<job_id>")
@app.route("/servicio/<job_id>")
@login_required
def job_detail(job_id):
    servicio = query_db(
        "SELECT se.*, c.nombre as categoria, u.nombre as proveedor_nombre, "
        "u.ciudad as proveedor_ciudad, u.email as proveedor_email "
        "FROM servicios se JOIN categorias c ON c.id = se.categoria_id "
        "JOIN usuarios u ON u.id = se.proveedor_id WHERE se.id = %s",
        [job_id], one=True
    )
    if not servicio:
        flash("Servicio no encontrado", "danger")
        return redirect(url_for("jobs"))

    rating = query_db(
        "SELECT COALESCE(AVG(c.puntaje), 0) as avg_rating, COUNT(*) as total "
        "FROM calificaciones c JOIN solicitudes s ON s.id = c.solicitud_id "
        "WHERE s.servicio_id = %s",
        [job_id], one=True
    )
    solicitudes = []
    if str(servicio["proveedor_id"]) == str(session["user_id"]) or session["role"] == "admin":
        solicitudes = query_db(
            "SELECT s.*, u.nombre as cliente_nombre, u.email as cliente_email, "
            "cl.puntaje, cl.comentario "
            "FROM solicitudes s JOIN usuarios u ON u.id = s.cliente_id "
            "LEFT JOIN calificaciones cl ON cl.solicitud_id = s.id "
            "WHERE s.servicio_id = %s ORDER BY s.fecha DESC",
            [job_id]
        )
    return render_template("job_detail.html", servicio=servicio, rating=rating,
                           solicitudes=solicitudes)


# ---------------------------------------------------------------------------
# Solicitudes (crear y cambiar estado)
# ---------------------------------------------------------------------------
ESTADOS = ("pendiente", "aceptada", "terminada", "cancelada")


@app.route("/job/<job_id>/solicitar", methods=["POST"])
@app.route("/servicio/<job_id>/solicitar", methods=["POST"])
@login_required
@role_required("cliente", "admin")
def solicitud_new(job_id):
    servicio = query_db("SELECT * FROM servicios WHERE id = %s", [job_id], one=True)
    if not servicio:
        flash("Servicio no encontrado", "danger")
        return redirect(url_for("jobs"))
    if str(servicio["proveedor_id"]) == str(session["user_id"]):
        flash("No puedes solicitar tu propio servicio.", "warning")
        return redirect(url_for("job_detail", job_id=job_id))

    existing = query_db(
        "SELECT id FROM solicitudes WHERE cliente_id = %s AND servicio_id = %s "
        "AND estado IN ('pendiente','aceptada')",
        [session["user_id"], job_id], one=True
    )
    if existing:
        flash("Ya tienes una solicitud activa para este servicio.", "warning")
        return redirect(url_for("job_detail", job_id=job_id))

    execute_db(
        "INSERT INTO solicitudes (cliente_id, servicio_id) VALUES (%s, %s)",
        [session["user_id"], job_id]
    )
    flash("Solicitud enviada. El proveedor la revisará pronto.", "success")
    return redirect(url_for("dashboard"))


@app.route("/solicitud/<int:solicitud_id>/estado", methods=["POST"])
@login_required
def solicitud_estado(solicitud_id):
    sol = query_db(
        "SELECT s.*, se.proveedor_id FROM solicitudes s "
        "JOIN servicios se ON se.id = s.servicio_id WHERE s.id = %s",
        [solicitud_id], one=True
    )
    if not sol:
        flash("Solicitud no encontrada", "danger")
        return redirect(url_for("dashboard"))

    es_cliente = str(sol["cliente_id"]) == str(session["user_id"])
    es_proveedor = str(sol["proveedor_id"]) == str(session["user_id"])
    es_admin = session["role"] == "admin"
    if not (es_cliente or es_proveedor or es_admin):
        flash("No tienes permiso sobre esta solicitud.", "danger")
        return redirect(url_for("dashboard"))

    nuevo = request.form.get("estado", "").strip()
    if nuevo not in ESTADOS:
        flash("Estado inválido.", "danger")
        return redirect(url_for("dashboard"))

    actual = sol["estado"]
    if actual in ("terminada", "cancelada"):
        flash("Esta solicitud ya está cerrada.", "warning")
        return redirect(url_for("dashboard"))
    if nuevo == "terminada" and not (es_cliente or es_admin):
        flash("Solo el cliente puede marcar la solicitud como terminada.", "danger")
        return redirect(url_for("dashboard"))

    execute_db("UPDATE solicitudes SET estado = %s WHERE id = %s", [nuevo, solicitud_id])
    flash(f"Solicitud marcada como {nuevo}.", "success")
    return redirect(request.form.get("next") or url_for("dashboard"))


@app.route("/solicitud/<int:solicitud_id>/calificar", methods=["POST"])
@login_required
@role_required("cliente")
def solicitud_calificar(solicitud_id):
    sol = query_db(
        "SELECT s.*, se.proveedor_id FROM solicitudes s "
        "JOIN servicios se ON se.id = s.servicio_id WHERE s.id = %s",
        [solicitud_id], one=True
    )
    if not sol or str(sol["cliente_id"]) != str(session["user_id"]):
        flash("Solicitud no encontrada.", "danger")
        return redirect(url_for("dashboard"))
    if sol["estado"] != "terminada":
        flash("Solo puedes calificar una solicitud terminada.", "warning")
        return redirect(url_for("dashboard"))

    try:
        puntaje = int(request.form.get("puntaje", 0))
    except (TypeError, ValueError):
        puntaje = 0
    if puntaje < 1 or puntaje > 5:
        flash("El puntaje debe estar entre 1 y 5.", "danger")
        return redirect(url_for("dashboard"))

    existing = query_db(
        "SELECT id FROM calificaciones WHERE solicitud_id = %s", [solicitud_id], one=True
    )
    if existing:
        flash("Ya calificaste esta solicitud.", "warning")
        return redirect(url_for("dashboard"))

    execute_db(
        "INSERT INTO calificaciones (solicitud_id, puntaje, comentario) VALUES (%s, %s, %s)",
        [solicitud_id, puntaje, request.form.get("comentario", "").strip() or None]
    )
    flash("¡Gracias por calificar el servicio!", "success")
    return redirect(url_for("dashboard"))


# ---------------------------------------------------------------------------
# Clientes (vista de admin)
# ---------------------------------------------------------------------------
@app.route("/clients")
@login_required
@role_required("admin")
def clients():
    search = request.args.get("q", "")
    query = """
        SELECT u.id, u.nombre, u.email, u.ciudad,
               COUNT(s.id) as total_solicitudes,
               SUM(CASE WHEN s.estado = 'terminada' THEN 1 ELSE 0 END) as terminadas
        FROM usuarios u
        LEFT JOIN solicitudes s ON s.cliente_id = u.id
        WHERE u.rol = 'cliente'
    """
    params = []
    if search:
        query += " AND (u.nombre LIKE %s OR u.email LIKE %s)"
        params += [f"%{search}%", f"%{search}%"]
    query += " GROUP BY u.id, u.nombre, u.email, u.ciudad ORDER BY total_solicitudes DESC"
    client_list = query_db(query, params)
    return render_template("clients.html", clients=client_list, search=search)


# ---------------------------------------------------------------------------
# Categorías
# ---------------------------------------------------------------------------
@app.route("/specialties")
@app.route("/categorias")
@login_required
def specialties():
    cats = query_db(
        "SELECT c.*, COUNT(se.id) as tech_count "
        "FROM categorias c LEFT JOIN servicios se ON se.categoria_id = c.id "
        "GROUP BY c.id, c.nombre ORDER BY c.nombre"
    )
    return render_template("specialties.html", specialties=cats)


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
@app.route("/admin/users")
@login_required
@role_required("admin")
def admin_users():
    users = query_db("SELECT * FROM usuarios ORDER BY id DESC")
    return render_template("admin_users.html", users=users)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.route("/health")
def health():
    try:
        query_db("SELECT 1", one=True)
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
