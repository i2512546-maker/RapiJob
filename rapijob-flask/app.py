import os
from datetime import date
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from db import query_db, execute_db

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
app.jinja_env.globals["now"] = date.today()

# Distritos de la zona de cobertura (MVP: Huancayo, El Tambo, Chilca)
DISTRITOS = {
    "Huancayo": {"lat": -12.0691, "lng": -75.2116},
    "El Tambo": {"lat": -12.0482, "lng": -75.2048},
    "Chilca": {"lat": -12.0832, "lng": -75.1910},
}
METODOS_PAGO = {"yape": "Yape", "plin": "Plin", "cash": "Efectivo al finalizar"}


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
            "SELECT u.*, p.first_name, p.last_name, p.avatar_url "
            "FROM users u LEFT JOIN profiles p ON p.user_id = u.id "
            "WHERE u.id = %s::uuid",
            [session["user_id"]], one=True
        )


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = query_db(
            "SELECT * FROM users WHERE email = %s AND status = 'active'",
            [email], one=True
        )
        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["id"])
            session["role"] = user["role"]
            flash(f"Bienvenido, {user['email']}", "success")
            return redirect(url_for("dashboard"))
        flash("Credenciales inválidas", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "client")
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()

        existing = query_db("SELECT id FROM users WHERE email = %s", [email], one=True)
        if existing:
            flash("El email ya está registrado", "danger")
            return render_template("register.html")

        pw_hash = generate_password_hash(password)
        result = query_db(
            "INSERT INTO users (email, password, role) VALUES (%s, %s, %s) RETURNING id",
            [email, pw_hash, role], one=True
        )
        user_id = str(result["id"])
        execute_db(
            "INSERT INTO profiles (user_id, first_name, last_name) VALUES (%s::uuid, %s, %s)",
            [user_id, first_name, last_name]
        )
        flash("Registro exitoso. Inicia sesión.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


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

    if role == "technician":
        assignments = query_db(
            "SELECT ja.*, j.title, j.status as job_status "
            "FROM job_assignments ja "
            "JOIN jobs j ON j.id = ja.job_id "
            "WHERE ja.technician_id = %s::uuid "
            "ORDER BY ja.assigned_at DESC LIMIT 10",
            [user_id]
        )
        return render_template("dashboard.html", assignments=assignments, role=role)

    elif role == "client":
        jobs = query_db(
            "SELECT j.*, s.name as specialty_name "
            "FROM jobs j LEFT JOIN specialties s ON s.id = j.specialty_id "
            "WHERE j.client_id = %s::uuid ORDER BY j.created_at DESC LIMIT 10",
            [user_id]
        )
        categorias = query_db("SELECT id, name, description FROM specialties ORDER BY name")
        return render_template("dashboard.html", jobs=jobs, role=role, categorias=categorias)

    else:
        recent_jobs = query_db(
            "SELECT j.*, u.email as client_email "
            "FROM jobs j JOIN users u ON u.id = j.client_id "
            "ORDER BY j.created_at DESC LIMIT 10"
        )
        tech_count = query_db("SELECT COUNT(*) as c FROM users WHERE role = 'technician'", one=True)
        client_count = query_db("SELECT COUNT(*) as c FROM users WHERE role = 'client'", one=True)
        return render_template(
            "dashboard.html", recent_jobs=recent_jobs,
            tech_count=tech_count, client_count=client_count, role=role
        )


# ---------------------------------------------------------------------------
# Technicians
# ---------------------------------------------------------------------------
@app.route("/technicians")
@login_required
def technicians():
    search = request.args.get("q", "")
    spec = request.args.get("specialty", "")
    query = """
        SELECT u.id, p.first_name, p.last_name, u.email
        FROM users u
        JOIN profiles p ON p.user_id = u.id
        WHERE u.role = 'technician' AND u.status = 'active'
    """
    params = []
    if search:
        query += " AND (p.first_name ILIKE %s OR p.last_name ILIKE %s OR u.email ILIKE %s)"
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    if spec:
        query += """
            AND u.id IN (
                SELECT ts.technician_id FROM technician_specialties ts
                JOIN specialties s ON s.id = ts.specialty_id
                WHERE s.name ILIKE %s
            )
        """
        params.append(f"%{spec}%")
    query += " ORDER BY p.first_name, p.last_name"
    techs = query_db(query, params)
    specialties = query_db("SELECT name FROM specialties ORDER BY name")
    return render_template("technicians.html", technicians=techs, specialties=specialties,
                           search=search, selected_spec=spec)


@app.route("/technician/<user_id>")
@login_required
def technician_detail(user_id):
    tech = query_db(
        "SELECT u.*, p.first_name, p.last_name, p.avatar_url, p.bio, p.hourly_rate "
        "FROM users u JOIN profiles p ON p.user_id = u.id WHERE u.id = %s::uuid",
        [user_id], one=True
    )
    if not tech:
        flash("Técnico no encontrado", "danger")
        return redirect(url_for("technicians"))

    specs = query_db(
        "SELECT s.name FROM specialties s "
        "JOIN technician_specialties ts ON ts.specialty_id = s.id "
        "WHERE ts.technician_id = %s::uuid",
        [user_id]
    )
    certs = query_db(
        "SELECT c.name, tc.issued_at, tc.expires_at, tc.validation_status "
        "FROM certifications c "
        "JOIN technician_certifications tc ON tc.certification_id = c.id "
        "WHERE tc.technician_id = %s::uuid",
        [user_id]
    )
    reviews = query_db(
        "SELECT jr.rating, jr.comment, jr.created_at, j.title "
        "FROM job_reviews jr JOIN jobs j ON j.id = jr.job_id "
        "WHERE jr.reviewee_id = %s::uuid ORDER BY jr.created_at DESC LIMIT 10",
        [user_id]
    )
    return render_template("technician_detail.html", tech=tech,
                           specialties=specs, certifications=certs, reviews=reviews)


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
@app.route("/jobs")
@login_required
def jobs():
    status = request.args.get("status", "")
    query = """
        SELECT j.*, u.email as client_email, s.name as specialty_name,
               p.first_name || ' ' || p.last_name as client_name
        FROM jobs j
        JOIN users u ON u.id = j.client_id
        LEFT JOIN profiles p ON p.user_id = u.id
        LEFT JOIN specialties s ON s.id = j.specialty_id
        WHERE 1=1
    """
    params = []
    if status:
        query += " AND j.status = %s"
        params.append(status)
    if session["role"] == "client":
        query += " AND j.client_id = %s::uuid"
        params.append(session["user_id"])
    if session["role"] == "technician":
        query += " ORDER BY CASE WHEN j.status = 'open' THEN 0 ELSE 1 END, j.created_at DESC LIMIT 50"
    else:
        query += " ORDER BY j.created_at DESC LIMIT 50"
    job_list = query_db(query, params)
    return render_template("jobs.html", jobs=job_list, selected_status=status)


@app.route("/jobs/new", methods=["GET", "POST"])
@login_required
@role_required("client", "admin")
def job_new():
    specialties = query_db("SELECT id, name, description FROM specialties ORDER BY name")
    selected_specialty = request.args.get("specialty_id", "")
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        specialty_id = request.form.get("specialty_id", "").strip()
        district = request.form.get("district", "").strip()
        address = request.form.get("address", "").strip()
        urgency = request.form.get("urgency", "normal")

        errors = []
        if not title or len(title) < 5:
            errors.append("Por favor escribe un título breve del problema (mín. 5 caracteres).")
        if not description:
            errors.append("Describe el problema para que el técnico pueda cotizarlo.")
        if not specialty_id:
            errors.append("Selecciona la categoría de servicio.")
        if district not in DISTRITOS:
            errors.append("Selecciona tu distrito: Huancayo, El Tambo o Chilca.")
        if urgency not in ("low", "normal", "high", "urgent"):
            urgency = "normal"

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "job_form.html", specialties=specialties,
                selected_specialty=specialty_id, form=request.form
            )

        coord = DISTRITOS[district]
        label = f"{address if address else 'Sin dirección específica'}, {district}"
        execute_db(
            """INSERT INTO jobs (client_id, title, description, specialty_id,
               budget_min, budget_max, location_lat, location_lng, location_label,
               is_remote, urgency, status)
               VALUES (%s::uuid, %s, %s, %s::uuid, %s, %s, %s, %s, %s, %s, %s, 'open')""",
            [session["user_id"], title, description, specialty_id,
             0, 0, coord["lat"], coord["lng"], label, 0, urgency]
        )
        flash("¡Tu solicitud fue publicada! Los técnicos enviarán sus cotizaciones.", "success")
        return redirect(url_for("jobs"))
    return render_template(
        "job_form.html", specialties=specialties,
        selected_specialty=selected_specialty, form={}
    )


@app.route("/job/<job_id>")
@login_required
def job_detail(job_id):
    job = query_db(
        "SELECT j.*, u.email as client_email, s.name as specialty_name "
        "FROM jobs j JOIN users u ON u.id = j.client_id "
        "LEFT JOIN specialties s ON s.id = j.specialty_id "
        "WHERE j.id = %s::uuid",
        [job_id], one=True
    )
    if not job:
        flash("Trabajo no encontrado", "danger")
        return redirect(url_for("jobs"))

    applications = query_db(
        """SELECT ja.*, u.email, p.first_name, p.last_name, p.hourly_rate
           FROM job_applications ja
           JOIN users u ON u.id = ja.technician_id
           LEFT JOIN profiles p ON p.user_id = u.id
           WHERE ja.job_id = %s::uuid ORDER BY ja.proposed_price ASC, ja.created_at DESC""",
        [job_id]
    )

    assignment_tech = None
    if job.get("assigned_to"):
        assignment_tech = query_db(
            "SELECT u.email, p.first_name, p.last_name "
            "FROM users u LEFT JOIN profiles p ON p.user_id = u.id "
            "WHERE u.id = %s::uuid",
            [str(job["assigned_to"])], one=True
        )

    review = query_db(
        "SELECT * FROM job_reviews WHERE job_id = %s::uuid", [job_id], one=True
    )

    payment = query_db(
        "SELECT * FROM payments WHERE job_id = %s::uuid ORDER BY created_at DESC LIMIT 1",
        [job_id], one=True
    )

    is_owner = session["role"] == "client" and str(job["client_id"]) == str(session["user_id"])
    return render_template("job_detail.html", job=job, applications=applications,
                           assignment=assignment_tech, review=review, payment=payment,
                           is_owner=is_owner, metodos_pago=METODOS_PAGO)


@app.route("/job/<job_id>/apply", methods=["POST"])
@login_required
@role_required("technician")
def job_apply(job_id):
    job = query_db(
        "SELECT * FROM jobs WHERE id = %s::uuid AND status = 'open'",
        [job_id], one=True
    )
    if not job:
        flash("Este trabajo ya no acepta cotizaciones.", "warning")
        return redirect(url_for("job_detail", job_id=job_id))

    existing = query_db(
        "SELECT id FROM job_applications WHERE job_id = %s::uuid AND technician_id = %s::uuid",
        [job_id, session["user_id"]], one=True
    )
    if existing:
        flash("Ya enviaste tu cotización para este trabajo.", "warning")
        return redirect(url_for("job_detail", job_id=job_id))

    try:
        price = float(request.form.get("proposed_price", ""))
    except (TypeError, ValueError):
        price = 0
    cover_letter = request.form.get("cover_letter", "").strip()

    if price <= 0:
        flash("Ingresa un precio en Soles (S/.) mayor a 0 para tu cotización.", "danger")
        return redirect(url_for("job_detail", job_id=job_id))
    if not cover_letter:
        flash("Escribe un breve mensaje al cliente con tu propuesta.", "danger")
        return redirect(url_for("job_detail", job_id=job_id))

    execute_db(
        "INSERT INTO job_applications (job_id, technician_id, cover_letter, proposed_price) "
        "VALUES (%s::uuid, %s::uuid, %s, %s)",
        [job_id, session["user_id"], cover_letter, price]
    )
    execute_db(
        "INSERT INTO notifications (user_id, title, message, type, reference_id) "
        "VALUES (%s::uuid, %s, %s, %s, %s::uuid)",
        [str(job["client_id"]), "Cotización recibida",
         f"Un técnico te envió una cotización para: {job['title']}",
         "job_applied", job_id]
    )
    flash("¡Cotización enviada!", "success")
    return redirect(url_for("job_detail", job_id=job_id))


@app.route("/job/<job_id>/checkout", methods=["GET"])
@login_required
@role_required("client")
def job_checkout(job_id):
    job = query_db(
        "SELECT j.*, s.name as specialty_name "
        "FROM jobs j LEFT JOIN specialties s ON s.id = j.specialty_id "
        "WHERE j.id = %s::uuid",
        [job_id], one=True
    )
    if not job:
        flash("Trabajo no encontrado", "danger")
        return redirect(url_for("jobs"))
    if str(job["client_id"]) != str(session["user_id"]):
        flash("No tienes permiso para ver este trabajo.", "danger")
        return redirect(url_for("jobs"))
    if job["status"] != "open":
        flash("Este trabajo ya no está disponible.", "warning")
        return redirect(url_for("job_detail", job_id=job_id))

    app_id = request.args.get("app", "")
    cotizacion = None
    if app_id:
        cotizacion = query_db(
            """SELECT ja.*, u.email, p.first_name, p.last_name, p.location_label
               FROM job_applications ja
               JOIN users u ON u.id = ja.technician_id
               LEFT JOIN profiles p ON p.user_id = u.id
               WHERE ja.id = %s::uuid AND ja.job_id = %s::uuid AND ja.status = 'applied'""",
            [app_id, job_id], one=True
        )
    if not cotizacion:
        flash("Selecciona una cotización válida para continuar.", "warning")
        return redirect(url_for("job_detail", job_id=job_id))

    return render_template("checkout.html", job=job, cotizacion=cotizacion,
                           metodos_pago=METODOS_PAGO)


@app.route("/job/<job_id>/pay", methods=["POST"])
@login_required
@role_required("client")
def job_pay(job_id):
    job = query_db("SELECT * FROM jobs WHERE id = %s::uuid", [job_id], one=True)
    if not job:
        flash("Trabajo no encontrado", "danger")
        return redirect(url_for("jobs"))
    if str(job["client_id"]) != str(session["user_id"]):
        flash("No tienes permiso para confirmar este trabajo.", "danger")
        return redirect(url_for("jobs"))
    if job["status"] != "open":
        flash("Este trabajo ya no está disponible.", "warning")
        return redirect(url_for("job_detail", job_id=job_id))

    app_id = request.form.get("app_id", "")
    method = request.form.get("method", "")
    phone = request.form.get("phone", "").strip()

    if method not in METODOS_PAGO:
        flash("Método de pago inválido.", "danger")
        return redirect(url_for("job_detail", job_id=job_id))
    if method in ("yape", "plin") and (len(phone) < 9 or not phone.isdigit()):
        flash("Ingresa un número de celular válido para Yape/Plin.", "danger")
        return redirect(url_for("job_detail", job_id=job_id))

    cotizacion = query_db(
        """SELECT ja.*, u.email FROM job_applications ja
           JOIN users u ON u.id = ja.technician_id
           WHERE ja.id = %s::uuid AND ja.job_id = %s::uuid AND ja.status = 'applied'""",
        [app_id, job_id], one=True
    )
    if not cotizacion or not cotizacion.get("proposed_price"):
        flash("Cotización no válida o sin precio.", "danger")
        return redirect(url_for("job_detail", job_id=job_id))

    tech_id = str(cotizacion["technician_id"])
    amount = float(cotizacion["proposed_price"])
    status_pago = "succeeded" if method != "cash" else "pending"
    medio = "Yape (simulado)" if method == "yape" else "Plin (simulado)" if method == "plin" else "Efectivo al finalizar"

    execute_db(
        "UPDATE job_applications SET status = 'rejected' WHERE job_id = %s::uuid AND status = 'applied' AND technician_id != %s::uuid",
        [job_id, tech_id]
    )
    execute_db(
        "UPDATE job_applications SET status = 'accepted' WHERE job_id = %s::uuid AND technician_id = %s::uuid",
        [job_id, tech_id]
    )
    execute_db(
        "INSERT INTO job_assignments (job_id, technician_id, assigned_by, accepted_at) "
        "VALUES (%s::uuid, %s::uuid, %s::uuid, NOW())",
        [job_id, tech_id, session["user_id"]]
    )
    execute_db(
        "UPDATE jobs SET assigned_to = %s::uuid, status = 'in_progress' WHERE id = %s::uuid",
        [tech_id, job_id]
    )
    execute_db(
        "INSERT INTO payments (job_id, payer_id, payee_id, amount, currency, method, status, provider_txn_id) "
        "VALUES (%s::uuid, %s::uuid, %s::uuid, %s, 'PEN', %s, %s, %s)",
        [job_id, session["user_id"], tech_id, amount, method, status_pago, method.upper() + "-MOCK-001"]
    )
    execute_db(
        "INSERT INTO notifications (user_id, title, message, type, reference_id) "
        "VALUES (%s::uuid, %s, %s, %s, %s::uuid)",
        [tech_id, "¡Servicio confirmado!", f"Te contrataron para: {job['title']} ({medio}).",
         "job_assigned", job_id]
    )

    flash(f"¡Pago confirmado con {medio}! El técnico ya fue notificado.", "success")
    return redirect(url_for("job_detail", job_id=job_id))


@app.route("/job/<job_id>/assign/<tech_id>", methods=["POST"])
@login_required
@role_required("client", "admin")
def job_assign(job_id, tech_id):
    job = query_db("SELECT * FROM jobs WHERE id = %s::uuid", [job_id], one=True)
    if not job:
        flash("Trabajo no encontrado", "danger")
        return redirect(url_for("jobs"))
    if session["role"] == "client" and str(job["client_id"]) != str(session["user_id"]):
        flash("No tienes permiso para asignar este trabajo.", "danger")
        return redirect(url_for("job_detail", job_id=job_id))
    execute_db(
        "UPDATE job_applications SET status = 'rejected' WHERE job_id = %s::uuid AND status = 'applied' "
        "AND technician_id != %s::uuid",
        [job_id, tech_id]
    )
    execute_db(
        "UPDATE job_applications SET status = 'accepted' WHERE job_id = %s::uuid AND technician_id = %s::uuid",
        [job_id, tech_id]
    )
    execute_db(
        "INSERT INTO job_assignments (job_id, technician_id, assigned_by, accepted_at) "
        "VALUES (%s::uuid, %s::uuid, %s::uuid, NOW())",
        [job_id, tech_id, session["user_id"]]
    )
    execute_db(
        "UPDATE jobs SET assigned_to = %s::uuid, status = 'in_progress' WHERE id = %s::uuid",
        [tech_id, job_id]
    )
    flash("Técnico asignado", "success")
    return redirect(url_for("job_detail", job_id=job_id))


@app.route("/job/<job_id>/complete", methods=["POST"])
@login_required
def job_complete(job_id):
    job = query_db("SELECT * FROM jobs WHERE id = %s::uuid", [job_id], one=True)
    if not job:
        flash("Trabajo no encontrado", "danger")
        return redirect(url_for("jobs"))
    if session["role"] == "client" and str(job["client_id"]) != str(session["user_id"]):
        flash("Solo la dueña del trabajo puede finalizarlo.", "danger")
        return redirect(url_for("job_detail", job_id=job_id))
    if session["role"] not in ("client", "admin"):
        flash("No tienes permiso para finalizar el trabajo.", "danger")
        return redirect(url_for("job_detail", job_id=job_id))
    if job["status"] != "in_progress":
        flash("El trabajo no está en progreso.", "warning")
        return redirect(url_for("job_detail", job_id=job_id))

    execute_db(
        "UPDATE jobs SET status = 'completed', completed_at = NOW() WHERE id = %s::uuid",
        [job_id]
    )
    # Efectivo: el pago se confirma al finalizar el servicio
    if job.get("assigned_to"):
        execute_db(
            "UPDATE payments SET status = 'succeeded', updated_at = NOW() "
            "WHERE job_id = %s::uuid AND method = 'cash' AND status = 'pending'",
            [job_id]
        )
        execute_db(
            "INSERT INTO notifications (user_id, title, message, type, reference_id) "
            "VALUES (%s::uuid, %s, %s, %s, %s::uuid)",
            [str(job["assigned_to"]), "¡Trabajo finalizado!",
             f"Confirmaron la finalización de: {job['title']}", "job_completed", job_id]
        )
    flash("Servicio finalizado. Recuerda calificar al técnico.", "success")
    return redirect(url_for("job_detail", job_id=job_id))


@app.route("/job/<job_id>/cancel", methods=["POST"])
@login_required
def job_cancel(job_id):
    job = query_db("SELECT * FROM jobs WHERE id = %s::uuid", [job_id], one=True)
    if not job:
        flash("Trabajo no encontrado", "danger")
        return redirect(url_for("jobs"))
    if session["role"] == "client" and str(job["client_id"]) != str(session["user_id"]):
        flash("No tienes permiso para cancelar este trabajo.", "danger")
        return redirect(url_for("job_detail", job_id=job_id))
    if session["role"] not in ("client", "admin"):
        flash("No tienes permiso para cancelar el trabajo.", "danger")
        return redirect(url_for("job_detail", job_id=job_id))
    if job["status"] == "completed":
        flash("No se puede cancelar un trabajo finalizado.", "warning")
        return redirect(url_for("job_detail", job_id=job_id))

    reason = request.form.get("reason", "").strip()
    execute_db(
        "UPDATE jobs SET status = 'cancelled', cancelled_at = NOW(), cancellation_reason = %s WHERE id = %s::uuid",
        [reason or "Solicitud cancelada por el cliente", job_id]
    )
    flash("Trabajo cancelado.", "info")
    return redirect(url_for("job_detail", job_id=job_id))


@app.route("/job/<job_id>/review", methods=["POST"])
@login_required
def job_review(job_id):
    job = query_db("SELECT * FROM jobs WHERE id = %s::uuid", [job_id], one=True)
    if not job or job["status"] != "completed":
        flash("Solo puedes calificar un servicio finalizado.", "warning")
        return redirect(url_for("job_detail", job_id=job_id))
    if session["role"] == "client" and str(job["client_id"]) != str(session["user_id"]):
        flash("Solo la dueña del trabajo puede calificar.", "danger")
        return redirect(url_for("job_detail", job_id=job_id))
    if not job.get("assigned_to"):
        flash("No hay técnico asignado para calificar.", "warning")
        return redirect(url_for("job_detail", job_id=job_id))

    try:
        rating = int(request.form.get("rating", 0))
    except (TypeError, ValueError):
        rating = 0
    if rating < 1 or rating > 5:
        flash("La calificación debe estar entre 1 y 5 estrellas.", "danger")
        return redirect(url_for("job_detail", job_id=job_id))

    existing = query_db(
        "SELECT id FROM job_reviews WHERE job_id = %s::uuid", [job_id], one=True
    )
    if existing:
        flash("Ya calificaste este servicio.", "warning")
        return redirect(url_for("job_detail", job_id=job_id))

    execute_db(
        """INSERT INTO job_reviews (job_id, reviewer_id, reviewee_id, rating, comment)
           VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s)""",
        [job_id, session["user_id"], str(job["assigned_to"]),
         rating, request.form.get("comment", "").strip()]
    )
    execute_db(
        "INSERT INTO notifications (user_id, title, message, type, reference_id) "
        "VALUES (%s::uuid, %s, %s, %s, %s::uuid)",
        [str(job["assigned_to"]), "¡Nueva reseña!",
         f"Te calificaron {rating}★ en: {job['title']}", "review_added", job_id]
    )
    flash("¡Gracias por calificar el servicio!", "success")
    return redirect(url_for("job_detail", job_id=job_id))


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------
@app.route("/clients")
@login_required
@role_required("admin", "technician")
def clients():
    search = request.args.get("q", "")
    query = """
        SELECT u.id, p.first_name, p.last_name, u.email,
               COUNT(j.id) as total_jobs,
               SUM(CASE WHEN j.status = 'completed' THEN 1 ELSE 0 END) as completed_jobs
        FROM users u
        JOIN profiles p ON p.user_id = u.id
        LEFT JOIN jobs j ON j.client_id = u.id
        WHERE u.role = 'client' AND u.status = 'active'
    """
    params = []
    if search:
        query += " AND (p.first_name ILIKE %s OR p.last_name ILIKE %s OR u.email ILIKE %s)"
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    query += " GROUP BY u.id, p.first_name, p.last_name, u.email ORDER BY total_jobs DESC"
    client_list = query_db(query, params)
    return render_template("clients.html", clients=client_list, search=search)


# ---------------------------------------------------------------------------
# Specialties
# ---------------------------------------------------------------------------
@app.route("/specialties")
@login_required
def specialties():
    specs = query_db(
        """SELECT s.*, COUNT(ts.technician_id) as tech_count
           FROM specialties s
           LEFT JOIN technician_specialties ts ON ts.specialty_id = s.id
           GROUP BY s.id ORDER BY s.name"""
    )
    return render_template("specialties.html", specialties=specs)


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
@app.route("/notifications")
@login_required
def notifications():
    notes = query_db(
        "SELECT * FROM notifications WHERE user_id = %s::uuid ORDER BY created_at DESC LIMIT 50",
        [session["user_id"]]
    )
    execute_db(
        "UPDATE notifications SET read = true WHERE user_id = %s::uuid AND read = false",
        [session["user_id"]]
    )
    return render_template("notifications.html", notifications=notes)


# ---------------------------------------------------------------------------
# Admin: Users
# ---------------------------------------------------------------------------
@app.route("/admin/users")
@login_required
@role_required("admin")
def admin_users():
    users = query_db(
        "SELECT u.*, p.first_name, p.last_name FROM users u "
        "LEFT JOIN profiles p ON p.user_id = u.id ORDER BY u.created_at DESC"
    )
    return render_template("admin_users.html", users=users)


@app.route("/admin/user/<user_id>/toggle", methods=["POST"])
@login_required
@role_required("admin")
def admin_toggle_user(user_id):
    execute_db(
        "UPDATE users SET status = CASE WHEN status = 'active' THEN 'inactive' ELSE 'active' END "
        "WHERE id = %s::uuid",
        [user_id]
    )
    flash("Usuario actualizado", "success")
    return redirect(url_for("admin_users"))


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
