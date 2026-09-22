-- ============================================================
--  RapiJob - Platform DB (PostgreSQL)
--  Schema completo propuesto en DESIGN.md
--  Ejecutar: psql $DATABASE_URL -f db/schema.sql
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 1. USERS (auth + roles)
-- ============================================================
CREATE TABLE users (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email        TEXT UNIQUE NOT NULL,
    phone        TEXT UNIQUE,
    password     TEXT NOT NULL,                 -- bcrypt hash
    role         TEXT NOT NULL CHECK (role IN ('client','technician','admin','supervisor')),
    status       TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','inactive')),
    verified     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_email   ON users(email);
CREATE INDEX idx_users_role    ON users(role);

-- ============================================================
-- 2. PROFILES (datos extendidos)
--  NOTA: lat/lng en NUMERIC para evitar dependencia PostGIS en MVP.
--        En prod se recomienda GEOGRAPHY + índice GIST.
-- ============================================================
CREATE TABLE profiles (
    user_id            UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    first_name         TEXT NOT NULL,
    last_name          TEXT NOT NULL,
    bio                TEXT,
    avatar_url         TEXT,
    location_lat       NUMERIC(9,6),
    location_lng       NUMERIC(9,6),
    location_label     TEXT,
    service_radius_km  NUMERIC(6,2) DEFAULT 30,
    hourly_rate        NUMERIC(10,2),
    verified_at        TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_profiles_label ON profiles(location_label);

-- ============================================================
-- 3. SPECIALTIES (extensible: IT, mantenimiento, electricidad...)
-- ============================================================
CREATE TABLE specialties (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    description TEXT,
    icon_url    TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_specialties_name ON specialties(name);

-- ============================================================
-- 4. TECHNICIAN_SPECIALTIES (muchos-a-muchos)
-- ============================================================
CREATE TABLE technician_specialties (
    technician_id   UUID REFERENCES users(id) ON DELETE CASCADE,
    specialty_id    UUID REFERENCES specialties(id) ON DELETE CASCADE,
    experience_years NUMERIC(4,1),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (technician_id, specialty_id)
);
CREATE INDEX idx_ts_technician ON technician_specialties(technician_id);
CREATE INDEX idx_ts_specialty  ON technician_specialties(specialty_id);

-- ============================================================
-- 5. CERTIFICATIONS (catálogo)
-- ============================================================
CREATE TABLE certifications (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    issuing_body TEXT,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_certifications_name ON certifications(name);

-- ============================================================
-- 6. TECHNICIAN_CERTIFICATIONS (certificados + workflow validación)
-- ============================================================
CREATE TABLE technician_certifications (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    technician_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    certification_id UUID NOT NULL REFERENCES certifications(id) ON DELETE CASCADE,
    document_url     TEXT NOT NULL,
    issued_at        DATE,
    expires_at       DATE,
    validation_status TEXT NOT NULL DEFAULT 'pending'
                          CHECK (validation_status IN ('pending','valid','rejected')),
    validated_by     UUID REFERENCES users(id),
    validated_at     TIMESTAMPTZ,
    rejection_reason TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_tc_technician   ON technician_certifications(technician_id);
CREATE INDEX idx_tc_cert         ON technician_certifications(certification_id);
CREATE INDEX idx_tc_validation   ON technician_certifications(validation_status);
CREATE INDEX idx_tc_expires      ON technician_certifications(expires_at);

-- ============================================================
-- 7. JOBS (trabajos publicados por clientes)
-- ============================================================
CREATE TABLE jobs (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id          UUID NOT NULL REFERENCES users(id),
    title              TEXT NOT NULL,
    description        TEXT NOT NULL,
    specialty_id       UUID NOT NULL REFERENCES specialties(id),
    budget_min         NUMERIC(10,2),
    budget_max         NUMERIC(10,2),
    location_lat       NUMERIC(9,6),
    location_lng       NUMERIC(9,6),
    location_label     TEXT,
    is_remote          BOOLEAN NOT NULL DEFAULT FALSE,
    urgency            TEXT NOT NULL DEFAULT 'normal'
                          CHECK (urgency IN ('low','normal','high','urgent')),
    status             TEXT NOT NULL DEFAULT 'open'
                          CHECK (status IN ('open','in_progress','completed','cancelled')),
    deadline_at        TIMESTAMPTZ,
    assigned_to        UUID REFERENCES users(id),
    completed_at       TIMESTAMPTZ,
    cancelled_at       TIMESTAMPTZ,
    cancellation_reason TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_jobs_client    ON jobs(client_id);
CREATE INDEX idx_jobs_specialty ON jobs(specialty_id);
CREATE INDEX idx_jobs_status    ON jobs(status);
CREATE INDEX idx_jobs_created   ON jobs(created_at DESC);

-- ============================================================
-- 8. JOB_APPLICATIONS (postulaciones de técnicos)
-- ============================================================
CREATE TABLE job_applications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID NOT NULL REFERENCES jobs(id),
    technician_id   UUID NOT NULL REFERENCES users(id),
    cover_letter    TEXT,
    proposed_price  NUMERIC(10,2),
    status          TEXT NOT NULL DEFAULT 'applied'
                        CHECK (status IN ('applied','accepted','rejected','withdrawn')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ja_job        ON job_applications(job_id);
CREATE INDEX idx_ja_technician ON job_applications(technician_id);
CREATE INDEX idx_ja_status     ON job_applications(status);
CREATE UNIQUE INDEX uq_ja_job_tech ON job_applications(job_id, technician_id);

-- ============================================================
-- 9. JOB_ASSIGNMENTS (historial de asignaciones)
-- ============================================================
CREATE TABLE job_assignments (
    job_id            UUID NOT NULL REFERENCES jobs(id),
    technician_id     UUID NOT NULL REFERENCES users(id),
    assigned_by       UUID REFERENCES users(id),
    assigned_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    accepted_at       TIMESTAMPTZ,
    rejected_at       TIMESTAMPTZ,
    rejection_reason  TEXT,
    PRIMARY KEY (job_id, technician_id, assigned_at)
);
CREATE INDEX idx_assignment_job        ON job_assignments(job_id);
CREATE INDEX idx_assignment_technician ON job_assignments(technician_id);

-- ============================================================
-- 10. JOB_REVIEWS (reseñas 1-5 estrellas)
-- ============================================================
CREATE TABLE job_reviews (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id        UUID NOT NULL REFERENCES jobs(id),
    reviewer_id   UUID NOT NULL REFERENCES users(id),
    reviewee_id   UUID NOT NULL REFERENCES users(id),
    rating        INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment       TEXT,
    is_anonymous  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_review_job      ON job_reviews(job_id);
CREATE INDEX idx_review_reviewee ON job_reviews(reviewee_id);
CREATE INDEX idx_review_rating   ON job_reviews(rating);
CREATE UNIQUE INDEX uq_review_job ON job_reviews(job_id);

-- ============================================================
-- 11. REVIEW_VALIDATIONS (validación de calidad por supervisor)
-- ============================================================
CREATE TABLE review_validations (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id        UUID NOT NULL REFERENCES jobs(id),
    supervisor_id UUID NOT NULL REFERENCES users(id),
    status        TEXT NOT NULL CHECK (status IN ('approved','rejected','needs_revision')),
    score         NUMERIC(4,2),
    notes         TEXT,
    evidence_url  TEXT,
    validated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_rv_job        ON review_validations(job_id);
CREATE INDEX idx_rv_supervisor ON review_validations(supervisor_id);
CREATE INDEX idx_rv_status     ON review_validations(status);

-- ============================================================
-- 12. PAYMENTS (pagos)
-- ============================================================
CREATE TABLE payments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID NOT NULL REFERENCES jobs(id),
    payer_id        UUID NOT NULL REFERENCES users(id),
    payee_id        UUID NOT NULL REFERENCES users(id),
    amount          NUMERIC(10,2) NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'PEN',
    method          TEXT NOT NULL CHECK (method IN ('yape','plin','cash','card','transfer','wallet')),
    status          TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','succeeded','failed','refunded')),
    provider_txn_id TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_payments_job   ON payments(job_id);
CREATE INDEX idx_payments_payer  ON payments(payer_id);
CREATE INDEX idx_payments_payee  ON payments(payee_id);
CREATE INDEX idx_payments_status ON payments(status);

-- ============================================================
-- 13. DOCUMENTS (anexos: fotos, evidencias)
-- ============================================================
CREATE TABLE documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID REFERENCES jobs(id) ON DELETE CASCADE,
    uploader_id     UUID NOT NULL REFERENCES users(id),
    type            TEXT NOT NULL
                        CHECK (type IN ('contract','work_photo','evidence','cert','other')),
    url             TEXT NOT NULL,
    file_name       TEXT NOT NULL,
    file_size_bytes BIGINT,
    mime_type       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_documents_job      ON documents(job_id);
CREATE INDEX idx_documents_uploader ON documents(uploader_id);
CREATE INDEX idx_documents_type     ON documents(type);

-- ============================================================
-- 14. NOTIFICATIONS
-- ============================================================
CREATE TABLE notifications (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id),
    title         TEXT NOT NULL,
    message       TEXT NOT NULL,
    type          TEXT NOT NULL
                      CHECK (type IN ('job_applied','job_assigned','job_completed','review_added','payment','system')),
    read          BOOLEAN NOT NULL DEFAULT FALSE,
    reference_id  UUID,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_notifications_user   ON notifications(user_id);
CREATE INDEX idx_notifications_read   ON notifications(read);
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);

-- ============================================================
-- 15. COMMISSION RULES (config para revenue/take-rate)
-- ============================================================
CREATE TABLE commission_rules (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    specialty_id UUID REFERENCES specialties(id),
    rate_pct     NUMERIC(5,2) NOT NULL DEFAULT 15.00,      -- 15%
    min_amount   NUMERIC(10,2) NOT NULL DEFAULT 0,
    active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_commission_specialty ON commission_rules(specialty_id);
