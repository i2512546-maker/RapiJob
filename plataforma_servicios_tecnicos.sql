-- Plataforma de Contratación de Servicios Técnicos
-- Base de datos para gestionar clientes, técnicos, servicios y contratos

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS plataforma_servicios_tecnicos;
USE plataforma_servicios_tecnicos;

-- =====================================================
-- TABLA: Usuarios (Clientes y Técnicos)
-- =====================================================
CREATE TABLE usuarios (
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    tipo_usuario ENUM('cliente', 'tecnico') NOT NULL,
    documento_identidad VARCHAR(20) UNIQUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('activo', 'inactivo', 'suspendido') DEFAULT 'activo',
    contraseña_hash VARCHAR(255) NOT NULL,
    fotografia_url VARCHAR(255),
    INDEX idx_email (email),
    INDEX idx_tipo_usuario (tipo_usuario)
);

-- =====================================================
-- TABLA: Perfiles Técnicos
-- =====================================================
CREATE TABLE perfiles_tecnicos (
    id_perfil INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT NOT NULL UNIQUE,
    experiencia_años INT,
    calificacion_promedio DECIMAL(3, 2) DEFAULT 0.00,
    numero_trabajos_completados INT DEFAULT 0,
    biografias TEXT,
    tarifa_base DECIMAL(10, 2) NOT NULL,
    disponible BOOLEAN DEFAULT TRUE,
    zona_servicio VARCHAR(255),
    certificaciones TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    INDEX idx_calificacion (calificacion_promedio),
    INDEX idx_tarifa (tarifa_base)
);

-- =====================================================
-- TABLA: Categorías de Servicios
-- =====================================================
CREATE TABLE categorias_servicios (
    id_categoria INT PRIMARY KEY AUTO_INCREMENT,
    nombre_categoria VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    icono_url VARCHAR(255),
    estado ENUM('activa', 'inactiva') DEFAULT 'activa'
);

-- =====================================================
-- TABLA: Servicios
-- =====================================================
CREATE TABLE servicios (
    id_servicio INT PRIMARY KEY AUTO_INCREMENT,
    id_categoria INT NOT NULL,
    nombre_servicio VARCHAR(150) NOT NULL,
    descripcion TEXT,
    duracion_estimada_minutos INT,
    precio_base DECIMAL(10, 2) NOT NULL,
    estado ENUM('disponible', 'no_disponible') DEFAULT 'disponible',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_categoria) REFERENCES categorias_servicios(id_categoria),
    INDEX idx_categoria (id_categoria),
    INDEX idx_precio (precio_base)
);

-- =====================================================
-- TABLA: Especializaciones de Técnicos
-- =====================================================
CREATE TABLE especializaciones_tecnicos (
    id_especializacion INT PRIMARY KEY AUTO_INCREMENT,
    id_tecnico INT NOT NULL,
    id_servicio INT NOT NULL,
    nivel_experiencia ENUM('junior', 'intermedio', 'senior') DEFAULT 'junior',
    certificado BOOLEAN DEFAULT FALSE,
    fecha_obtencion DATE,
    UNIQUE KEY unique_tecnico_servicio (id_tecnico, id_servicio),
    FOREIGN KEY (id_tecnico) REFERENCES perfiles_tecnicos(id_usuario),
    FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio) ON DELETE CASCADE
);

-- =====================================================
-- TABLA: Disponibilidad de Técnicos
-- =====================================================
CREATE TABLE disponibilidad_tecnicos (
    id_disponibilidad INT PRIMARY KEY AUTO_INCREMENT,
    id_tecnico INT NOT NULL,
    dia_semana ENUM('lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'),
    hora_inicio TIME,
    hora_fin TIME,
    disponible BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (id_tecnico) REFERENCES perfiles_tecnicos(id_usuario) ON DELETE CASCADE,
    INDEX idx_tecnico_dia (id_tecnico, dia_semana)
);

-- =====================================================
-- TABLA: Órdenes de Trabajo / Contratos
-- =====================================================
CREATE TABLE ordenes_trabajo (
    id_orden INT PRIMARY KEY AUTO_INCREMENT,
    id_cliente INT NOT NULL,
    id_tecnico INT,
    id_servicio INT NOT NULL,
    fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_programada DATETIME NOT NULL,
    fecha_completada DATETIME,
    ubicacion_servicio VARCHAR(255) NOT NULL,
    descripcion_problema TEXT,
    notas_adicionales TEXT,
    estado_orden ENUM('pendiente', 'aceptada', 'en_progreso', 'completada', 'cancelada') DEFAULT 'pendiente',
    precio_final DECIMAL(10, 2),
    metodo_pago ENUM('efectivo', 'tarjeta', 'transferencia', 'billetera_digital') DEFAULT 'efectivo',
    fecha_pago DATETIME,
    FOREIGN KEY (id_cliente) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_tecnico) REFERENCES perfiles_tecnicos(id_usuario) ON DELETE SET NULL,
    FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio),
    INDEX idx_cliente (id_cliente),
    INDEX idx_tecnico (id_tecnico),
    INDEX idx_estado (estado_orden),
    INDEX idx_fecha_programada (fecha_programada)
);

-- =====================================================
-- TABLA: Pagos
-- =====================================================
CREATE TABLE pagos (
    id_pago INT PRIMARY KEY AUTO_INCREMENT,
    id_orden INT NOT NULL UNIQUE,
    monto DECIMAL(10, 2) NOT NULL,
    metodo_pago ENUM('efectivo', 'tarjeta_credito', 'tarjeta_debito', 'transferencia', 'billetera_digital', 'criptomoneda') DEFAULT 'efectivo',
    estado_pago ENUM('pendiente', 'procesando', 'completado', 'rechazado', 'reembolsado') DEFAULT 'pendiente',
    numero_transaccion VARCHAR(100),
    referencia_banco VARCHAR(100),
    fecha_pago TIMESTAMP,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_orden) REFERENCES ordenes_trabajo(id_orden) ON DELETE CASCADE,
    INDEX idx_estado_pago (estado_pago),
    INDEX idx_fecha_pago (fecha_pago)
);

-- =====================================================
-- TABLA: Reseñas y Calificaciones
-- =====================================================
CREATE TABLE resenas_calificaciones (
    id_resena INT PRIMARY KEY AUTO_INCREMENT,
    id_orden INT NOT NULL UNIQUE,
    id_cliente INT NOT NULL,
    id_tecnico INT NOT NULL,
    calificacion_servicio INT CHECK (calificacion_servicio >= 1 AND calificacion_servicio <= 5),
    calificacion_tecnico INT CHECK (calificacion_tecnico >= 1 AND calificacion_tecnico <= 5),
    comentario TEXT,
    fecha_resena TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    respuesta_tecnico TEXT,
    fecha_respuesta DATETIME,
    FOREIGN KEY (id_orden) REFERENCES ordenes_trabajo(id_orden) ON DELETE CASCADE,
    FOREIGN KEY (id_cliente) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_tecnico) REFERENCES perfiles_tecnicos(id_usuario) ON DELETE CASCADE,
    INDEX idx_cliente (id_cliente),
    INDEX idx_tecnico (id_tecnico),
    INDEX idx_calificacion_servicio (calificacion_servicio)
);

-- =====================================================
-- TABLA: Historial de Transacciones
-- =====================================================
CREATE TABLE historial_transacciones (
    id_transaccion INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    id_orden INT,
    tipo_transaccion ENUM('pago', 'reembolso', 'deposito', 'retiro') NOT NULL,
    monto DECIMAL(10, 2) NOT NULL,
    saldo_anterior DECIMAL(10, 2),
    saldo_nuevo DECIMAL(10, 2),
    descripcion TEXT,
    fecha_transaccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_orden) REFERENCES ordenes_trabajo(id_orden) ON DELETE SET NULL,
    INDEX idx_usuario (id_usuario),
    INDEX idx_fecha (fecha_transaccion)
);

-- =====================================================
-- TABLA: Mensajes y Comunicación
-- =====================================================
CREATE TABLE mensajes (
    id_mensaje INT PRIMARY KEY AUTO_INCREMENT,
    id_remitente INT NOT NULL,
    id_destinatario INT NOT NULL,
    id_orden INT,
    contenido TEXT NOT NULL,
    fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    leido BOOLEAN DEFAULT FALSE,
    fecha_lectura DATETIME,
    tipo_mensaje ENUM('texto', 'imagen', 'documento', 'notificacion') DEFAULT 'texto',
    FOREIGN KEY (id_remitente) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_destinatario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_orden) REFERENCES ordenes_trabajo(id_orden) ON DELETE SET NULL,
    INDEX idx_destinatario (id_destinatario),
    INDEX idx_leido (leido),
    INDEX idx_fecha (fecha_envio)
);

-- =====================================================
-- TABLA: Quejas y Soporte
-- =====================================================
CREATE TABLE quejas_soporte (
    id_queja INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    id_orden INT,
    tipo_queja ENUM('calidad_servicio', 'comportamiento', 'precio', 'otro') NOT NULL,
    descripcion TEXT NOT NULL,
    estado_queja ENUM('abierta', 'en_revision', 'resuelta', 'rechazada') DEFAULT 'abierta',
    prioridad ENUM('baja', 'media', 'alta', 'critica') DEFAULT 'media',
    fecha_queja TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_resolucion DATETIME,
    resolucion_descripcion TEXT,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_orden) REFERENCES ordenes_trabajo(id_orden) ON DELETE SET NULL,
    INDEX idx_estado (estado_queja),
    INDEX idx_prioridad (prioridad)
);

-- =====================================================
-- TABLA: Promociones y Cupones
-- =====================================================
CREATE TABLE promociones_cupones (
    id_promocion INT PRIMARY KEY AUTO_INCREMENT,
    codigo_cupon VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT,
    tipo_descuento ENUM('porcentaje', 'monto_fijo') NOT NULL,
    valor_descuento DECIMAL(10, 2) NOT NULL,
    cantidad_usos INT DEFAULT 0,
    cantidad_usos_maxima INT,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    INDEX idx_codigo (codigo_cupon),
    INDEX idx_fecha_fin (fecha_fin)
);

-- =====================================================
-- TABLA: Auditoría y Logs
-- =====================================================
CREATE TABLE auditoria_logs (
    id_log INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT,
    accion VARCHAR(100) NOT NULL,
    tabla_afectada VARCHAR(50),
    registro_id INT,
    valores_anteriores JSON,
    valores_nuevos JSON,
    fecha_accion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
    INDEX idx_fecha (fecha_accion),
    INDEX idx_usuario (id_usuario)
);

-- =====================================================
-- INSERTS DE DATOS INICIALES
-- =====================================================

-- Categorías de servicios
INSERT INTO categorias_servicios (nombre_categoria, descripcion) VALUES
('Reparación de Computadoras', 'Servicios de reparación y mantenimiento de computadoras de escritorio y portátiles'),
('Instalación de Redes', 'Instalación y configuración de redes, WiFi y sistemas de cableado'),
('Soporte de Software', 'Instalación, configuración y soporte de aplicaciones y sistemas operativos'),
('Servicio Técnico de Telefonía', 'Reparación y configuración de teléfonos móviles y sistemas telefónicos'),
('Seguridad Informática', 'Consultoría y servicios de seguridad, antivirus y protección de datos'),
('Mantenimiento Preventivo', 'Limpieza, actualización y chequeo de equipos informáticos');

-- Servicios
INSERT INTO servicios (id_categoria, nombre_servicio, descripcion, duracion_estimada_minutos, precio_base) VALUES
(1, 'Reparación de Pantalla LCD', 'Cambio de pantalla dañada o defectuosa en computadoras portátiles', 60, 150.00),
(1, 'Cambio de Disco Duro', 'Instalación de disco duro nuevo o SSD', 45, 120.00),
(1, 'Limpieza Interna de PC', 'Limpieza profunda de componentes internos y disipadores', 60, 80.00),
(2, 'Instalación de WiFi', 'Instalación y configuración de red inalámbrica', 90, 200.00),
(2, 'Cableado de Red', 'Instalación de cableado y conexiones de red', 120, 300.00),
(3, 'Instalación de Windows', 'Instalación completa de sistema operativo Windows', 90, 100.00),
(3, 'Instalación de Antivirus', 'Instalación y configuración de software de protección', 30, 60.00),
(4, 'Reparación de Smartphone', 'Diagnóstico y reparación de teléfonos móviles', 45, 180.00),
(5, 'Análisis de Seguridad', 'Escaneo y análisis de vulnerabilidades en sistemas', 120, 250.00);

-- =====================================================
-- VISTAS ÚTILES
-- =====================================================

-- Vista de Técnicos Disponibles
CREATE VIEW v_tecnicos_disponibles AS
SELECT 
    u.id_usuario,
    u.nombre,
    u.apellido,
    u.email,
    pt.calificacion_promedio,
    pt.numero_trabajos_completados,
    pt.tarifa_base,
    pt.zona_servicio
FROM usuarios u
INNER JOIN perfiles_tecnicos pt ON u.id_usuario = pt.id_usuario
WHERE u.estado = 'activo' 
  AND pt.disponible = TRUE
ORDER BY pt.calificacion_promedio DESC;

-- Vista de Órdenes Pendientes
CREATE VIEW v_ordenes_pendientes AS
SELECT 
    ot.id_orden,
    u_cliente.nombre AS nombre_cliente,
    u_cliente.email AS email_cliente,
    s.nombre_servicio,
    ot.fecha_programada,
    ot.ubicacion_servicio,
    ot.estado_orden
FROM ordenes_trabajo ot
INNER JOIN usuarios u_cliente ON ot.id_cliente = u_cliente.id_usuario
INNER JOIN servicios s ON ot.id_servicio = s.id_servicio
WHERE ot.estado_orden IN ('pendiente', 'aceptada')
ORDER BY ot.fecha_programada ASC;

-- Vista de Ingresos Mensuales
CREATE VIEW v_ingresos_mensuales AS
SELECT 
    YEAR(p.fecha_pago) AS año,
    MONTH(p.fecha_pago) AS mes,
    COUNT(p.id_pago) AS cantidad_pagos,
    SUM(p.monto) AS ingreso_total,
    AVG(p.monto) AS ingreso_promedio
FROM pagos p
WHERE p.estado_pago = 'completado'
GROUP BY YEAR(p.fecha_pago), MONTH(p.fecha_pago)
ORDER BY año DESC, mes DESC;
