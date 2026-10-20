-- ============================================================
--  RapiJob - Seed de Datos Simulados (MVP Huancayo / El Tambo / Chilca)
--  Objetivo: poblar KPIs de PLATAFORMA + reputación de técnicos.
--  Todas las PK son UUID válidas. Moneda de negocio: Soles (S/.).
--
--  CONTRASEÑA de todos los usuarios: password123
--  (el hash se regenera con scripts/seed-passwords.js si hace falta)
--  El seed DUPLICA el dataset del fallback SQLite de db.py.
-- ============================================================
SET session_replication_role = replica;
TRUNCATE TABLE payments, job_reviews, review_validations, job_assignments,
              job_applications, documents, notifications, jobs,
              technician_certifications, technician_specialties,
              certifications, specialties, profiles, users,
              platform_alert_rules, commission_rules
              RESTART IDENTITY CASCADE;
SET session_replication_role = origin;

-- ============================================================
-- UUID MASTER MAP
--   admin    : 0...001 | supervisor: 0...002
--   clientas : 0...010 (Rosa, El Tambo) / 0...011 (Carmen, Chilca)
--   técnicos : 0...020 Juan (Electricidad)
--              0...021 Carlos (Gasfitería)
--              0...022 Miguel (Cómputo)
--              0...023 Ana (Electrodomésticos)
--              0...024 Diana (Aire Acondicionado)
--              0...025 Pedro (Gasfitería + Cómputo)
--              0...026 Roberto (Electricidad + Electrodomésticos)
--   jobs     : 10010000-1xxx-4001-9001-0000000000xx  (j001..j010)
--   pays     : 20010000-1xxx-4001-9002-...             (p001..p005)
--   reviews  : 30010000-1xxx-4001-9003-...             (r001..r004)
--   vals     : 40010000-1xxx-4001-9004-...
--   docs     : 50010000-00xx-4001-9005-...
--   apps     : 60010000-1xxx-4001-9006-...             (ap001..ap014)
--   notif    : 70010000-1xxx-4001-9007-...
-- ============================================================

-- ------------------------------------------------------------
-- 1) USERS  (11)
-- ------------------------------------------------------------
DO $$
DECLARE
  ph TEXT := '$2b$12$abcdefghijklmnopqrstuuAbCdEfGhIjKlMnOpQrStUvWxYz01234567';
BEGIN
  INSERT INTO users (id,email,phone,password,role,status,verified,created_at) VALUES
    ('a0000000-0000-0000-0000-000000000001','admin@rapijob.com','+51900000001',ph,'admin','active',TRUE,now()-'60 days'::interval),
    ('a0000000-0000-0000-0000-000000000002','sup@rapijob.com','+51900000002',ph,'supervisor','active',TRUE,now()-'60 days'::interval),
    ('a0000000-0000-0000-0000-000000000010','rosa.cliente@rapijob.pe','+51964320010',ph,'client','active',TRUE,now()-'30 days'::interval),
    ('a0000000-0000-0000-0000-000000000011','carmen.cliente@rapijob.pe','+51964320011',ph,'client','active',TRUE,now()-'30 days'::interval),
    ('a0000000-0000-0000-0000-000000000020','juan.electrico@rapijob.pe','+51964320020',ph,'technician','active',TRUE,now()-'25 days'::interval),
    ('a0000000-0000-0000-0000-000000000021','carlos.gasfitero@rapijob.pe','+51964320021',ph,'technician','active',TRUE,now()-'20 days'::interval),
    ('a0000000-0000-0000-0000-000000000022','miguel.computo@rapijob.pe','+51964320022',ph,'technician','active',TRUE,now()-'18 days'::interval),
    ('a0000000-0000-0000-0000-000000000023','ana.electro@rapijob.pe','+51964320023',ph,'technician','active',TRUE,now()-'22 days'::interval),
    ('a0000000-0000-0000-0000-000000000024','diana.clima@rapijob.pe','+51964320024',ph,'technician','active',TRUE,now()-'16 days'::interval),
    ('a0000000-0000-0000-0000-000000000025','pedro.servicios@rapijob.pe','+51964320025',ph,'technician','active',TRUE,now()-'14 days'::interval),
    ('a0000000-0000-0000-0000-000000000026','roberto.electrico@rapijob.pe','+51964320026',ph,'technician','active',TRUE,now()-'12 days'::interval);
  RAISE NOTICE 'users inserted';
END $$;

-- ------------------------------------------------------------
-- 2) PROFILES (Huancayo / El Tambo / Chilca)
-- ------------------------------------------------------------
INSERT INTO profiles(user_id,first_name,last_name,bio,location_lat,location_lng,location_label,service_radius_km,hourly_rate,verified_at,created_at)
VALUES
 ('a0000000-0000-0000-0000-000000000010','Rosa','Huamán','Ama de casa en El Tambo, Huancayo',-12.0482,-75.2048,'El Tambo, Huancayo',20,0,now()-'25 days'::interval,now()-'30 days'::interval),
 ('a0000000-0000-0000-0000-000000000011','Carmen','Quispe','Vivo en Chilca, Huancayo. Necesito ayuda con mis artefactos',-12.0832,-75.1910,'Chilca, Huancayo',20,0,now()-'25 days'::interval,now()-'30 days'::interval),
 ('a0000000-0000-0000-0000-000000000020','Juan','Pérez','Electricista certificado. Instalaciones, cortocircuitos y cableado',-12.0490,-75.2060,'El Tambo, Huancayo',25,45.00,now()-'20 days'::interval,now()-'20 days'::interval),
 ('a0000000-0000-0000-0000-000000000021','Carlos','Ramos','Gasfitero maestro. Fugas, desatoros, termas y tuberías',-12.0691,-75.2116,'Huancayo Centro',20,40.00,now()-'15 days'::interval,now()-'15 days'::interval),
 ('a0000000-0000-0000-0000-000000000022','Miguel','Soto','Técnico en cómputo: formateo, limpieza, redes wifi',-12.0510,-75.2120,'El Tambo, Huancayo',30,35.00,now()-'12 days'::interval,now()-'12 days'::interval),
 ('a0000000-0000-0000-0000-000000000023','Ana','Flores','Especialista en electrodomésticos: lavadoras, refrigeradoras, microondas',-12.0810,-75.2030,'Chilca, Huancayo',25,50.00,now()-'15 days'::interval,now()-'15 days'::interval),
 ('a0000000-0000-0000-0000-000000000024','Diana','López','Técnica en aire acondicionado: instalación, mantenimiento y recarga de gas',-12.0700,-75.2100,'Huancayo Centro',30,60.00,now()-'10 days'::interval,now()-'10 days'::interval),
 ('a0000000-0000-0000-0000-000000000025','Pedro','Castro','Gasfitería y cómputo, atiendo El Tambo, Huancayo y Chilca',-12.0840,-75.1940,'Chilca, Huancayo',30,38.00,now()-'10 days'::interval,now()-'10 days'::interval),
 ('a0000000-0000-0000-0000-000000000026','Roberto','Jiménez','Electricidad y electrodomésticos. Más de 10 años de experiencia',-12.0680,-75.2080,'Huancayo Centro',25,42.00,now()-'8 days'::interval,now()-'8 days'::interval);

-- ------------------------------------------------------------
-- 3) SPECIALTIES (categorías del MVP)
-- ------------------------------------------------------------
INSERT INTO specialties(id,name,description)
VALUES
 ('b0000000-0000-0000-0000-000000000001','Cómputo','Mantenimiento y reparación de PC/laptops, formateo y redes wifi'),
 ('b0000000-0000-0000-0000-000000000002','Electricidad','Instalaciones eléctricas, cortocircuitos, cableado y tableros'),
 ('b0000000-0000-0000-0000-000000000003','Gasfitería','Fugas de agua, desatoros, grifería, termas y tuberías'),
 ('b0000000-0000-0000-0000-000000000004','Aire Acondicionado','Instalación, mantenimiento y recarga de gas de climatización'),
 ('b0000000-0000-0000-0000-000000000005','Electrodomésticos','Reparación de lavadoras, refrigeradoras, microondas y artefactos');

-- ------------------------------------------------------------
-- 4) TECHNICIAN_SPECIALTIES
-- ------------------------------------------------------------
INSERT INTO technician_specialties(technician_id,specialty_id,experience_years)
VALUES
 ('a0000000-0000-0000-0000-000000000020','b0000000-0000-0000-0000-000000000002',8),
 ('a0000000-0000-0000-0000-000000000021','b0000000-0000-0000-0000-000000000003',10),
 ('a0000000-0000-0000-0000-000000000022','b0000000-0000-0000-0000-000000000001',6),
 ('a0000000-0000-0000-0000-000000000023','b0000000-0000-0000-0000-000000000005',9),
 ('a0000000-0000-0000-0000-000000000024','b0000000-0000-0000-0000-000000000004',7),
 ('a0000000-0000-0000-0000-000000000025','b0000000-0000-0000-0000-000000000003',5),
 ('a0000000-0000-0000-0000-000000000025','b0000000-0000-0000-0000-000000000001',3),
 ('a0000000-0000-0000-0000-000000000026','b0000000-0000-0000-0000-000000000002',6),
 ('a0000000-0000-0000-0000-000000000026','b0000000-0000-0000-0000-000000000005',4);

-- ------------------------------------------------------------
-- 5) CERTIFICATIONS (Perú)
-- ------------------------------------------------------------
INSERT INTO certifications(id,name,issuing_body)
VALUES
 ('c0000000-0000-0000-0000-000000000001','Electricista Básico','SENATI'),
 ('c0000000-0000-0000-0000-000000000002','Gasfitero Maestro','SENATI'),
 ('c0000000-0000-0000-0000-000000000003','Técnico en Computación CCNA','Cisco'),
 ('c0000000-0000-0000-0000-000000000004','Reparación de Electrodomésticos','CETPRO Huancayo'),
 ('c0000000-0000-0000-0000-000000000005','Instalación y Mantenimiento de Aire Acondicionado','SENATI');

-- ------------------------------------------------------------
-- 6) TECHNICIAN_CERTIFICATIONS (todas válidas)
-- ------------------------------------------------------------
INSERT INTO technician_certifications
  (id,technician_id,certification_id,document_url,issued_at,expires_at,validation_status,validated_by,validated_at)
VALUES
 ('d0000000-0000-0000-0000-000000000001','a0000000-0000-0000-0000-000000000020',
  'c0000000-0000-0000-0000-000000000001','https://docs.rapijob.pe/juan_electrico.pdf','2023-03-01','2026-03-01','valid','a0000000-0000-0000-0000-000000000001',now()-'10 days'::interval),
 ('d0000000-0000-0000-0000-000000000002','a0000000-0000-0000-0000-000000000021',
  'c0000000-0000-0000-0000-000000000002','https://docs.rapijob.pe/carlos_gasfitero.pdf','2022-06-01','2027-06-01','valid','a0000000-0000-0000-0000-000000000001',now()-'10 days'::interval),
 ('d0000000-0000-0000-0000-000000000003','a0000000-0000-0000-0000-000000000022',
  'c0000000-0000-0000-0000-000000000003','https://docs.rapijob.pe/miguel_ccna.pdf','2023-09-01','2026-09-01','valid','a0000000-0000-0000-0000-000000000001',now()-'10 days'::interval),
 ('d0000000-0000-0000-0000-000000000004','a0000000-0000-0000-0000-000000000023',
  'c0000000-0000-0000-0000-000000000004','https://docs.rapijob.pe/ana_electro.pdf','2024-01-01','2028-01-01','valid','a0000000-0000-0000-0000-000000000001',now()-'10 days'::interval),
 ('d0000000-0000-0000-0000-000000000005','a0000000-0000-0000-0000-000000000024',
  'c0000000-0000-0000-0000-000000000005','https://docs.rapijob.pe/diana_hvac.pdf','2023-05-01','2027-05-01','valid','a0000000-0000-0000-0000-000000000001',now()-'10 days'::interval),
 ('d0000000-0000-0000-0000-000000000006','a0000000-0000-0000-0000-000000000025',
  'c0000000-0000-0000-0000-000000000002','https://docs.rapijob.pe/pedro_gas.pdf','2023-11-01','2028-11-01','valid','a0000000-0000-0000-0000-000000000001',now()-'10 days'::interval),
 ('d0000000-0000-0000-0000-000000000007','a0000000-0000-0000-0000-000000000026',
  'c0000000-0000-0000-0000-000000000001','https://docs.rapijob.pe/roberto_electro.pdf','2022-08-01','2026-08-01','valid','a0000000-0000-0000-0000-000000000001',now()-'10 days'::interval);

-- ------------------------------------------------------------
-- 7) COMMISSION RULES (default 15%)
-- ------------------------------------------------------------
INSERT INTO commission_rules (id,specialty_id,rate_pct,min_amount,active)
VALUES
 ('e0000000-0000-0000-0000-000000000001',NULL,15.00,0,TRUE);

-- ------------------------------------------------------------
-- 8) JOBS  (j001..j010)  — presupuestos en S/., coords Huancayo
--    4 open / 1 in_progress / 4 completed / 0 cancelled
-- ------------------------------------------------------------
INSERT INTO jobs
  (id,client_id,title,description,specialty_id,budget_min,budget_max,
   location_lat,location_lng,location_label,is_remote,urgency,status,
   deadline_at,assigned_to,completed_at,cancelled_at,cancellation_reason,created_at)
VALUES
 ('10010000-1001-4001-9001-000000000001','a0000000-0000-0000-0000-000000000010','Cortocircuito en toma de corriente','Enchufe que chispea en la sala, quiero que lo revisen pronto',
  'b0000000-0000-0000-0000-000000000002',50,80,-12.0482,-75.2048,'Jr. Huancavelica 234, El Tambo',FALSE,'high','open',
  NULL,NULL,NULL,NULL,NULL,now()-'1 hour'::interval),
 ('10010000-1002-4001-9001-000000000002','a0000000-0000-0000-0000-000000000011','Lavadora no centrifuga','La lavadora deja la ropa mojada, no centrifuga desde la semana pasada',
  'b0000000-0000-0000-0000-000000000005',60,120,-12.0832,-75.1910,'Av. Los Andes 150, Chilca',FALSE,'normal','open',
  NULL,NULL,NULL,NULL,NULL,now()-'2 hours'::interval),
 ('10010000-1003-4001-9001-000000000003','a0000000-0000-0000-0000-000000000010','Fuga de agua en la cocina','Se moja todo el piso de la cocina, gotea debajo del lavadero',
  'b0000000-0000-0000-0000-000000000003',40,90,-12.0482,-75.2048,'Jr. Puno 450, El Tambo',FALSE,'urgent','open',
  NULL,NULL,NULL,NULL,NULL,now()-'3 hours'::interval),
 ('10010000-1004-4001-9001-000000000004','a0000000-0000-0000-0000-000000000011','Formateo y limpieza de laptop','Laptop muy lenta, necesita formateo y antivirus',
  'b0000000-0000-0000-0000-000000000001',60,100,-12.0832,-75.1910,'Jr. Cajamarca 88, Chilca',FALSE,'normal','completed',
  NULL,'a0000000-0000-0000-0000-000000000022',now()-'3 days'::interval,NULL,NULL,now()-'4 days'::interval),
 ('10010000-1005-4001-9001-000000000005','a0000000-0000-0000-0000-000000000010','Aire acondicionado no enfría','El split suelta aire tibio, creo que le falta gas',
  'b0000000-0000-0000-0000-000000000004',90,180,-12.0700,-75.2100,'Av. Giráldez 700, Huancayo',FALSE,'high','completed',
  NULL,'a0000000-0000-0000-0000-000000000024',now()-'6 days'::interval,NULL,NULL,now()-'7 days'::interval),
 ('10010000-1006-4001-9001-000000000006','a0000000-0000-0000-0000-000000000011','Cambio de llave del baño','La llave del baño gotea y no cierra bien',
  'b0000000-0000-0000-0000-000000000003',45,80,-12.0832,-75.1910,'Jr. Sucre 320, Chilca',FALSE,'low','completed',
  NULL,'a0000000-0000-0000-0000-000000000021',now()-'5 days'::interval,NULL,NULL,now()-'6 days'::interval),
 ('10010000-1007-4001-9001-000000000007','a0000000-0000-0000-0000-000000000010','Refrigeradora no congela','El congelador ya no congela, la comida se malogra',
  'b0000000-0000-0000-0000-000000000005',100,200,-12.0691,-75.2116,'Jr. Amazonas 210, Huancayo',FALSE,'urgent','completed',
  NULL,'a0000000-0000-0000-0000-000000000023',now()-'4 days'::interval,NULL,NULL,now()-'5 days'::interval),
 ('10010000-1008-4001-9001-000000000008','a0000000-0000-0000-0000-000000000011','Instalar spot LED en sala','Quiero que cambien mi luz del techo por 4 spots LED',
  'b0000000-0000-0000-0000-000000000002',60,120,-12.0482,-75.2048,'Urb. San Carlos Mz B Lt 12, El Tambo',FALSE,'normal','in_progress',
  NULL,'a0000000-0000-0000-0000-000000000020',NULL,NULL,NULL,now()-'1 day'::interval),
 ('10010000-1009-4001-9001-000000000009','a0000000-0000-0000-0000-000000000010','PC no enciende, posible fuente dañada','La computadora de escritorio no prende, quizá la fuente',
  'b0000000-0000-0000-0000-000000000001',70,130,-12.0482,-75.2048,'Jr. Huancayo 120, El Tambo',FALSE,'normal','open',
  NULL,NULL,NULL,NULL,NULL,now()-'5 hours'::interval),
 ('10010000-1010-4001-9001-000000000010','a0000000-0000-0000-0000-000000000011','Mantenimiento de split de dormitorio','Limpieza y mantenimiento general del aire acondicionado',
  'b0000000-0000-0000-0000-000000000004',80,150,-12.0832,-75.1910,'Av. Mariscal Castilla 980, Chilca',FALSE,'normal','open',
  NULL,NULL,NULL,NULL,NULL,now()-'6 hours'::interval);

-- ------------------------------------------------------------
-- 9) JOB_APPLICATIONS — cotizaciones con precio en S/.
-- ------------------------------------------------------------
INSERT INTO job_applications (id,job_id,technician_id,proposed_price,cover_letter,status,created_at,updated_at)
VALUES
 ('60010000-1001-4001-9006-000000000001','10010000-1001-4001-9001-000000000001','a0000000-0000-0000-0000-000000000020',65.00,'Puedo ir mañana temprano a revisar el cortocircuito','applied',now(),now()),
 ('60010000-1002-4001-9006-000000000002','10010000-1001-4001-9001-000000000001','a0000000-0000-0000-0000-000000000026',70.00,'Electricista colegiado, reviso toma e instalación completa','applied',now(),now()),
 ('60010000-1003-4001-9006-000000000003','10010000-1002-4001-9001-000000000002','a0000000-0000-0000-0000-000000000023',85.00,'Reviso el motor de centrifugado en el momento','applied',now()-'1 day'::interval,now()),
 ('60010000-1004-4001-9006-000000000004','10010000-1002-4001-9001-000000000002','a0000000-0000-0000-0000-000000000026',100.00,'Especialista en lavadoras, diagnóstico sin costo','applied',now()-'1 day'::interval,now()),
 ('60010000-1005-4001-9006-000000000005','10010000-1003-4001-9001-000000000003','a0000000-0000-0000-0000-000000000021',55.00,'Listo para hoy mismo, llevo repuestos de empaque','applied',now(),now()),
 ('60010000-1006-4001-9006-000000000006','10010000-1003-4001-9001-000000000003','a0000000-0000-0000-0000-000000000025',60.00,'Atiendo urgencias, llego en 30 minutos','applied',now(),now()),
 ('60010000-1007-4001-9006-000000000007','10010000-1004-4001-9001-000000000004','a0000000-0000-0000-0000-000000000022',80.00,'Formateo + instalación de programas básicos','accepted',now()-'4 days'::interval,now()-'4 days'::interval),
 ('60010000-1008-4001-9006-000000000008','10010000-1005-4001-9001-000000000005','a0000000-0000-0000-0000-000000000024',150.00,'Carga de gas y limpieza de filtros incluida','accepted',now()-'7 days'::interval,now()-'7 days'::interval),
 ('60010000-1009-4001-9006-000000000009','10010000-1006-4001-9001-000000000006','a0000000-0000-0000-0000-000000000021',70.00,'Cambio de llave, incluye empaquetaduras','accepted',now()-'6 days'::interval,now()-'6 days'::interval),
 ('60010000-1010-4001-9006-000000000010','10010000-1007-4001-9001-000000000007','a0000000-0000-0000-0000-000000000023',180.00,'Reparación de compresor con garantía de 30 días','accepted',now()-'5 days'::interval,now()-'5 days'::interval),
 ('60010000-1011-4001-9006-000000000011','10010000-1008-4001-9001-000000000008','a0000000-0000-0000-0000-000000000020',90.00,'Instalación de 4 spots LED incluido material','accepted',now()-'1 day'::interval,now()-'1 day'::interval),
 ('60010000-1012-4001-9006-000000000012','10010000-1009-4001-9001-000000000009','a0000000-0000-0000-0000-000000000022',95.00,'Reviso la fuente y dejo la PC operativa','applied',now(),now()),
 ('60010000-1013-4001-9006-000000000013','10010000-1009-4001-9001-000000000009','a0000000-0000-0000-0000-000000000025',110.00,'Técnico en cómputo, vengo con fuente de repuesto','applied',now(),now()),
 ('60010000-1014-4001-9006-000000000014','10010000-1010-4001-9001-000000000010','a0000000-0000-0000-0000-000000000024',130.00,'Mantenimiento premium con limpieza de evaporadora','applied',now(),now());

-- ------------------------------------------------------------
-- 10) JOB_ASSIGNMENTS (los 5 aceptados del dataset)
-- ------------------------------------------------------------
INSERT INTO job_assignments (job_id,technician_id,assigned_by,assigned_at,accepted_at)
VALUES
 ('10010000-1004-4001-9001-000000000004','a0000000-0000-0000-0000-000000000022','a0000000-0000-0000-0000-000000000011',now()-'4 days'::interval,now()-'4 days'::interval),
 ('10010000-1005-4001-9001-000000000005','a0000000-0000-0000-0000-000000000024','a0000000-0000-0000-0000-000000000010',now()-'7 days'::interval,now()-'7 days'::interval),
 ('10010000-1006-4001-9001-000000000006','a0000000-0000-0000-0000-000000000021','a0000000-0000-0000-0000-000000000011',now()-'6 days'::interval,now()-'6 days'::interval),
 ('10010000-1007-4001-9001-000000000007','a0000000-0000-0000-0000-000000000023','a0000000-0000-0000-0000-000000000010',now()-'5 days'::interval,now()-'5 days'::interval),
 ('10010000-1008-4001-9001-000000000008','a0000000-0000-0000-0000-000000000020','a0000000-0000-0000-0000-000000000011',now()-'1 day'::interval,now()-'1 day'::interval);

-- ------------------------------------------------------------
-- 11) JOB_REVIEWS (r001..r004)
-- ------------------------------------------------------------
INSERT INTO job_reviews (id,job_id,reviewer_id,reviewee_id,rating,comment,created_at)
VALUES
 ('30010000-1001-4001-9003-000000000001','10010000-1004-4001-9001-000000000004','a0000000-0000-0000-0000-000000000011','a0000000-0000-0000-0000-000000000022',5,'Muy rápido y la laptop quedó como nueva',now()-'3 days'::interval),
 ('30010000-1002-4001-9003-000000000002','10010000-1005-4001-9001-000000000005','a0000000-0000-0000-0000-000000000010','a0000000-0000-0000-0000-000000000024',5,'Enfrió rápido, muy amable y puntual',now()-'6 days'::interval),
 ('30010000-1003-4001-9003-000000000003','10010000-1006-4001-9001-000000000006','a0000000-0000-0000-0000-000000000011','a0000000-0000-0000-0000-000000000021',4,'Buen trabajo, ya no gotea',now()-'5 days'::interval),
 ('30010000-1004-4001-9003-000000000004','10010000-1007-4001-9001-000000000007','a0000000-0000-0000-0000-000000000010','a0000000-0000-0000-0000-000000000023',5,'Excelente, la refrigeradora ya congela bien',now()-'4 days'::interval);

-- ------------------------------------------------------------
-- 12) REVIEW_VALIDATIONS (una por reseña)
-- ------------------------------------------------------------
INSERT INTO review_validations (id,job_id,supervisor_id,status,score,notes,validated_at)
VALUES
 ('40010000-1001-4001-9004-000000000001','10010000-1004-4001-9001-000000000004','a0000000-0000-0000-0000-000000000002','approved',9.0,'OK',now()-'2 days'::interval),
 ('40010000-1002-4001-9004-000000000002','10010000-1005-4001-9001-000000000005','a0000000-0000-0000-0000-000000000002','approved',9.5,'OK',now()-'5 days'::interval),
 ('40010000-1003-4001-9004-000000000003','10010000-1006-4001-9001-000000000006','a0000000-0000-0000-0000-000000000002','approved',8.5,'OK',now()-'4 days'::interval),
 ('40010000-1004-4001-9004-000000000004','10010000-1007-4001-9001-000000000007','a0000000-0000-0000-0000-000000000002','approved',9.8,'Excelente',now()-'3 days'::interval);

-- ------------------------------------------------------------
-- 13) PAYMENTS (p001..p005)  — Yape / Plin / Efectivo (S/.)
-- ------------------------------------------------------------
INSERT INTO payments (id,job_id,payer_id,payee_id,amount,currency,method,status,provider_txn_id,created_at,updated_at)
VALUES
 ('20010000-1001-4001-9002-000000000001','10010000-1004-4001-9001-000000000004','a0000000-0000-0000-0000-000000000011','a0000000-0000-0000-0000-000000000022',80.00,'PEN','plin','succeeded','txn_90000001',now()-'3 days'::interval,now()-'3 days'::interval),
 ('20010000-1002-4001-9002-000000000002','10010000-1005-4001-9001-000000000005','a0000000-0000-0000-0000-000000000010','a0000000-0000-0000-0000-000000000024',150.00,'PEN','yape','succeeded','txn_90000002',now()-'6 days'::interval,now()-'6 days'::interval),
 ('20010000-1003-4001-9002-000000000003','10010000-1006-4001-9001-000000000006','a0000000-0000-0000-0000-000000000011','a0000000-0000-0000-0000-000000000021',70.00,'PEN','cash','pending','txn_90000003',now()-'5 days'::interval,now()-'5 days'::interval),
 ('20010000-1004-4001-9002-000000000004','10010000-1007-4001-9001-000000000007','a0000000-0000-0000-0000-000000000010','a0000000-0000-0000-0000-000000000023',180.00,'PEN','yape','succeeded','txn_90000004',now()-'4 days'::interval,now()-'4 days'::interval),
 ('20010000-1005-4001-9002-000000000005','10010000-1008-4001-9001-000000000008','a0000000-0000-0000-0000-000000000011','a0000000-0000-0000-0000-000000000020',90.00,'PEN','plin','succeeded','txn_90000005',now()-'1 day'::interval,now()-'1 day'::interval);

-- ------------------------------------------------------------
-- 14) DOCUMENTS
-- ------------------------------------------------------------
INSERT INTO documents (id,job_id,uploader_id,type,url,file_name,file_size_bytes,mime_type,created_at)
VALUES
 ('50010000-0001-4001-9005-000000000001','10010000-1004-4001-9001-000000000004','a0000000-0000-0000-0000-000000000022','evidence','https://docs.rapijob.pe/j004_laptop.jpg','laptop.jpg',180000,'image/jpeg',now()-'3 days'::interval),
 ('50010000-0002-4001-9005-000000000002','10010000-1005-4001-9001-000000000005','a0000000-0000-0000-0000-000000000024','work_photo','https://docs.rapijob.pe/j005_split.jpg','split.jpg',240000,'image/jpeg',now()-'6 days'::interval),
 ('50010000-0003-4001-9005-000000000003','10010000-1007-4001-9001-000000000007','a0000000-0000-0000-0000-000000000023','evidence','https://docs.rapijob.pe/j007_refri.jpg','refri.jpg',210000,'image/jpeg',now()-'4 days'::interval);

-- ------------------------------------------------------------
-- 15) NOTIFICATIONS
-- ------------------------------------------------------------
INSERT INTO notifications (id,user_id,title,message,type,reference_id,created_at,"read")
VALUES
 ('70010000-1001-4001-9007-000000000001','a0000000-0000-0000-0000-000000000020','Nueva solicitud','Hay una persona esperando una cotización de Electricidad','job_applied','10010000-1001-4001-9001-000000000001',now(),FALSE),
 ('70010000-1002-4001-9007-000000000002','a0000000-0000-0000-0000-000000000010','Cotización recibida','Juan Pérez te envió una cotización por S/. 65.00','job_applied','10010000-1001-4001-9001-000000000001',now(),FALSE);

-- ------------------------------------------------------------
-- 16) KPI_SNAPSHOTS semanales iniciales (histórico)
-- ------------------------------------------------------------
REFRESH MATERIALIZED VIEW mv_platform_metrics;

INSERT INTO kpi_snapshots(entity_type,entity_id,metric_name,metric_value,period_start,period_end)
SELECT 'platform',NULL,'jobs_created_weekly',jobs_created,wk,wk+6
FROM   mv_platform_metrics;
INSERT INTO kpi_snapshots(entity_type,entity_id,metric_name,metric_value,period_start,period_end)
SELECT 'platform',NULL,'completion_rate',completion_rate,wk,wk+6
FROM   mv_platform_metrics;
INSERT INTO kpi_snapshots(entity_type,entity_id,metric_name,metric_value,period_start,period_end)
SELECT 'platform',NULL,'gmv',gmv,wk,wk+6
FROM   mv_platform_metrics;
INSERT INTO kpi_snapshots(entity_type,entity_id,metric_name,metric_value,period_start,period_end)
SELECT 'platform',NULL,'revenue',revenue,wk,wk+6
FROM   mv_platform_metrics;

INSERT INTO kpi_snapshots(entity_type,entity_id,metric_name,metric_value,period_start,period_end)
SELECT 'technician',u.id,'rating',tm.avg_rating,CURRENT_DATE-'6 days',CURRENT_DATE
FROM users u JOIN v_tech_metrics tm ON tm.technician_id=u.id WHERE u.role='technician';
INSERT INTO kpi_snapshots(entity_type,entity_id,metric_name,metric_value,period_start,period_end)
SELECT 'technician',u.id,'earnings',tm.total_earned,CURRENT_DATE-'6 days',CURRENT_DATE
FROM users u JOIN v_tech_metrics tm ON tm.technician_id=u.id WHERE u.role='technician';

\echo 'SEED COMPLETE: 11 users, 5 specialties, 10 jobs (4 open, 1 in_progress, 4 completed), 14 cotizaciones, 5 asignaciones, 4 reviews, 5 pagos Yape/Plin/Efectivo, KPIs listos.'