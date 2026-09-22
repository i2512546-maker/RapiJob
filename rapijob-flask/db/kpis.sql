-- ============================================================
-- RapiJob — Vistas de KPIs
-- Basado en: Documento Técnico RapiJob (sección 5)
-- Motor: PostgreSQL 16
--
-- SUPUESTOS DE ESQUEMA (ajustar nombres de columnas si difieren
-- en tu modelo real):
--   job_applications(status)                  -- 'applied' | 'accepted' | ...
--   job_assignments(status, assigned_at, completed_at, job_id, technician_id)
--   job_reviews(rating, is_validated, job_id, reviewer_id, reviewee_id)
--   payments(amount, status, payee_id, payer_id, created_at)
--   jobs(id, client_id, status, created_at, budget_max)
--   users(id, role, last_login_at)
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 KPIs DE TÉCNICO (7)
-- ------------------------------------------------------------

-- 1. Tasa de aceptación de aplicaciones
CREATE OR REPLACE VIEW v_tech_acceptance_rate AS
SELECT
    ja.technician_id,
    ROUND(
        COUNT(*) FILTER (WHERE ja.status = 'accepted')::numeric
        / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS acceptance_rate
FROM job_applications ja
GROUP BY ja.technician_id;

-- 2. Rating promedio
CREATE OR REPLACE VIEW v_tech_rating AS
SELECT
    jasg.technician_id,
    ROUND(AVG(jr.rating)::numeric, 2) AS avg_rating,
    COUNT(jr.rating) AS total_reviews
FROM job_reviews jr
JOIN job_assignments jasg ON jasg.job_id = jr.job_id
    AND jasg.technician_id = jr.reviewee_id
GROUP BY jasg.technician_id;

-- 3. Ingresos acumulados
CREATE OR REPLACE VIEW v_tech_earnings AS
SELECT
    p.payee_id AS technician_id,
    ROUND(SUM(p.amount)::numeric, 2) AS total_earnings,
    COUNT(*) AS completed_jobs
FROM payments p
WHERE p.status = 'succeeded'
GROUP BY p.payee_id;

-- 4. First-time fix (trabajos completados sin necesidad de validación adicional)
CREATE OR REPLACE VIEW v_tech_first_time_fix AS
SELECT
    jasg.technician_id,
    ROUND(
        COUNT(*) FILTER (WHERE jr.is_validated = false)::numeric
        / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS first_time_fix_rate
FROM job_assignments jasg
JOIN job_reviews jr ON jr.job_id = jasg.job_id
    AND jr.reviewee_id = jasg.technician_id
GROUP BY jasg.technician_id;

-- 5. Tasa de finalización
CREATE OR REPLACE VIEW v_tech_completion_rate AS
SELECT
    technician_id,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'in_progress')::numeric
        / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS completion_rate,
    COUNT(*) AS total_assignments
FROM job_assignments
GROUP BY technician_id;

-- 6. Tiempo de resolución promedio (en horas)
CREATE OR REPLACE VIEW v_tech_resolution_time AS
SELECT
    technician_id,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (completed_at - assigned_at)) / 3600)::numeric,
        2
    ) AS avg_resolution_hours
FROM job_assignments
WHERE completed_at IS NOT NULL
GROUP BY technician_id;

-- 7. Aplicaciones enviadas
CREATE OR REPLACE VIEW v_tech_applied AS
SELECT
    technician_id,
    COUNT(*) AS applications_sent,
    COUNT(*) FILTER (WHERE status = 'accepted') AS applications_accepted
FROM job_applications
GROUP BY technician_id;

-- Vista unificada de KPIs de técnico
CREATE OR REPLACE VIEW v_tech_metrics AS
SELECT
    u.id AS technician_id,
    u.email,
    COALESCE(ar.acceptance_rate, 0) AS acceptance_rate,
    COALESCE(r.avg_rating, 0) AS avg_rating,
    COALESCE(r.total_reviews, 0) AS total_reviews,
    COALESCE(e.total_earnings, 0) AS total_earnings,
    COALESCE(e.completed_jobs, 0) AS completed_jobs,
    COALESCE(ftf.first_time_fix_rate, 0) AS first_time_fix_rate,
    COALESCE(cr.completion_rate, 0) AS completion_rate,
    COALESCE(cr.total_assignments, 0) AS total_assignments,
    COALESCE(rt.avg_resolution_hours, 0) AS avg_resolution_hours,
    COALESCE(ap.applications_sent, 0) AS applications_sent,
    COALESCE(ap.applications_accepted, 0) AS applications_accepted
FROM users u
LEFT JOIN v_tech_acceptance_rate ar ON ar.technician_id = u.id
LEFT JOIN v_tech_rating r ON r.technician_id = u.id
LEFT JOIN v_tech_earnings e ON e.technician_id = u.id
LEFT JOIN v_tech_first_time_fix ftf ON ftf.technician_id = u.id
LEFT JOIN v_tech_completion_rate cr ON cr.technician_id = u.id
LEFT JOIN v_tech_resolution_time rt ON rt.technician_id = u.id
LEFT JOIN v_tech_applied ap ON ap.technician_id = u.id
WHERE u.role = 'technician';

-- ------------------------------------------------------------
-- 5.2 KPIs DE CLIENTE (4)
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_client_metrics AS
SELECT
    j.client_id,
    u.email,
    COUNT(DISTINCT j.id) AS jobs_published,
    COUNT(DISTINCT j.id) FILTER (WHERE j.status = 'completed') AS jobs_completed,
    COUNT(DISTINCT j.id) FILTER (WHERE j.status = 'cancelled') AS jobs_cancelled,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (jasg.assigned_at - j.created_at)) / 3600)
        FILTER (WHERE jasg.assigned_at IS NOT NULL)::numeric,
        2
    ) AS avg_hiring_time_hours,
    ROUND(AVG(jr.rating) FILTER (WHERE jr.reviewer_id = j.client_id)::numeric, 2) AS avg_rating_given,
    ROUND(
        SUM(p.amount) FILTER (WHERE p.status = 'succeeded' AND p.payer_id = j.client_id)::numeric,
        2
    ) AS total_spent
FROM jobs j
LEFT JOIN users u ON u.id = j.client_id
LEFT JOIN job_assignments jasg ON jasg.job_id = j.id
LEFT JOIN job_reviews jr ON jr.job_id = j.id
LEFT JOIN payments p ON p.job_id = j.id
GROUP BY j.client_id, u.email;

-- ------------------------------------------------------------
-- 5.3 KPIs DE PLATAFORMA (vistas diarias/semanales)
-- ------------------------------------------------------------

-- Vista diaria de métricas de plataforma
CREATE OR REPLACE VIEW v_platform_daily_metrics AS
SELECT
    DATE(j.created_at) AS metric_date,
    COUNT(DISTINCT j.id) AS jobs_created,
    ROUND(
        COUNT(DISTINCT j.id) FILTER (WHERE j.status = 'completed')::numeric
        / NULLIF(COUNT(DISTINCT j.id), 0) * 100,
        2
    ) AS completion_rate,
    ROUND(
        COUNT(DISTINCT j.id) FILTER (WHERE j.status = 'cancelled')::numeric
        / NULLIF(COUNT(DISTINCT j.id), 0) * 100,
        2
    ) AS cancel_rate,
    ROUND(SUM(j.budget_max)::numeric, 2) AS gmv,
    ROUND(SUM(p.amount) FILTER (WHERE p.status = 'succeeded')::numeric, 2) AS revenue,
    ROUND(
        (SUM(p.amount) FILTER (WHERE p.status = 'succeeded')::numeric
         / NULLIF(SUM(j.budget_max), 0) * 100),
        2
    ) AS take_rate,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (jasg.assigned_at - j.created_at)) / 3600)
        FILTER (WHERE jasg.assigned_at IS NOT NULL)::numeric,
        2
    ) AS avg_match_hours,
    COUNT(DISTINCT u.id) FILTER (
        WHERE DATE(u.last_login_at) = DATE(j.created_at)
    ) AS daily_active_users
FROM jobs j
LEFT JOIN job_assignments jasg ON jasg.job_id = j.id
LEFT JOIN payments p ON p.job_id = j.id
LEFT JOIN users u ON TRUE
GROUP BY DATE(j.created_at);

-- Vista semanal de métricas de plataforma
CREATE OR REPLACE VIEW v_platform_weekly_metrics AS
SELECT
    DATE_TRUNC('week', j.created_at)::DATE AS week_start,
    COUNT(DISTINCT j.id) AS jobs_created,
    ROUND(
        COUNT(DISTINCT j.id) FILTER (WHERE j.status = 'completed')::numeric
        / NULLIF(COUNT(DISTINCT j.id), 0) * 100,
        2
    ) AS completion_rate,
    ROUND(
        COUNT(DISTINCT j.id) FILTER (WHERE j.status = 'cancelled')::numeric
        / NULLIF(COUNT(DISTINCT j.id), 0) * 100,
        2
    ) AS cancel_rate,
    ROUND(SUM(j.budget_max)::numeric, 2) AS gmv,
    ROUND(SUM(p.amount) FILTER (WHERE p.status = 'succeeded')::numeric, 2) AS revenue,
    ROUND(
        (SUM(p.amount) FILTER (WHERE p.status = 'succeeded')::numeric
         / NULLIF(SUM(j.budget_max), 0) * 100),
        2
    ) AS take_rate,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (jasg.assigned_at - j.created_at)) / 3600)
        FILTER (WHERE jasg.assigned_at IS NOT NULL)::numeric,
        2
    ) AS avg_match_hours,
    COUNT(DISTINCT u.id) FILTER (
        WHERE DATE_TRUNC('week', u.last_login_at) = DATE_TRUNC('week', j.created_at)
    ) AS weekly_active_users
FROM jobs j
LEFT JOIN job_assignments jasg ON jasg.job_id = j.id
LEFT JOIN payments p ON p.job_id = j.id
LEFT JOIN users u ON TRUE
GROUP BY DATE_TRUNC('week', j.created_at);

-- Vista mensual de métricas de plataforma
CREATE OR REPLACE VIEW v_platform_monthly_metrics AS
SELECT
    DATE_TRUNC('month', j.created_at)::DATE AS month_start,
    COUNT(DISTINCT j.id) AS jobs_created,
    ROUND(
        COUNT(DISTINCT j.id) FILTER (WHERE j.status = 'completed')::numeric
        / NULLIF(COUNT(DISTINCT j.id), 0) * 100,
        2
    ) AS completion_rate,
    ROUND(
        COUNT(DISTINCT j.id) FILTER (WHERE j.status = 'cancelled')::numeric
        / NULLIF(COUNT(DISTINCT j.id), 0) * 100,
        2
    ) AS cancel_rate,
    ROUND(SUM(j.budget_max)::numeric, 2) AS gmv,
    ROUND(SUM(p.amount) FILTER (WHERE p.status = 'succeeded')::numeric, 2) AS revenue,
    ROUND(
        (SUM(p.amount) FILTER (WHERE p.status = 'succeeded')::numeric
         / NULLIF(SUM(j.budget_max), 0) * 100),
        2
    ) AS take_rate,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (jasg.assigned_at - j.created_at)) / 3600)
        FILTER (WHERE jasg.assigned_at IS NOT NULL)::numeric,
        2
    ) AS avg_match_hours,
    COUNT(DISTINCT u.id) FILTER (
        WHERE DATE_TRUNC('month', u.last_login_at) = DATE_TRUNC('month', j.created_at)
    ) AS monthly_active_users
FROM jobs j
LEFT JOIN job_assignments jasg ON jasg.job_id = j.id
LEFT JOIN payments p ON p.job_id = j.id
LEFT JOIN users u ON TRUE
GROUP BY DATE_TRUNC('month', j.created_at);

-- Vista consolidada de platform KPIs (última semana)
CREATE OR REPLACE VIEW v_platform_summary AS
SELECT
    'weekly' AS period_type,
    week_start AS period_date,
    jobs_created,
    completion_rate,
    cancel_rate,
    gmv,
    revenue,
    take_rate,
    avg_match_hours,
    weekly_active_users AS active_users
FROM v_platform_weekly_metrics
ORDER BY week_start DESC
LIMIT 12;
