-- RapiJob - Esquema MySQL (Alwaysdata)
-- 5 tablas: usuarios, categorias, servicios, solicitudes, calificaciones
-- Ejecutar sobre la base de datos ya creada en el panel de Alwaysdata.

SET NAMES utf8mb4;

-- ---------------------------------------------------------------
-- usuarios
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(120)        NOT NULL,
    email       VARCHAR(190)        NOT NULL UNIQUE,
    clave_hash  VARCHAR(255)        NOT NULL,
    telefono    VARCHAR(30),
    rol         ENUM('cliente','proveedor') NOT NULL,
    ciudad      VARCHAR(120)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------
-- categorias
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categorias (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    nombre  VARCHAR(120) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------
-- servicios (ofrecidos por un proveedor)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS servicios (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    proveedor_id  INT NOT NULL,
    categoria_id  INT NOT NULL,
    titulo        VARCHAR(150)   NOT NULL,
    descripcion   TEXT,
    precio        DECIMAL(8,2)   NOT NULL DEFAULT 0.00,
    ubicacion     VARCHAR(150),
    CONSTRAINT fk_servicios_proveedor
        FOREIGN KEY (proveedor_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    CONSTRAINT fk_servicios_categoria
        FOREIGN KEY (categoria_id) REFERENCES categorias(id),
    INDEX idx_servicios_categoria (categoria_id),
    INDEX idx_servicios_ubicacion (ubicacion),
    INDEX idx_servicios_precio (precio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------
-- solicitudes (un cliente solicita un servicio)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS solicitudes (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id   INT NOT NULL,
    servicio_id  INT NOT NULL,
    estado       ENUM('pendiente','aceptada','terminada','cancelada')
                 NOT NULL DEFAULT 'pendiente',
    fecha        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_solicitudes_cliente
        FOREIGN KEY (cliente_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    CONSTRAINT fk_solicitudes_servicio
        FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE CASCADE,
    INDEX idx_solicitudes_estado (estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------
-- calificaciones (una por solicitud terminada)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS calificaciones (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    solicitud_id  INT NOT NULL UNIQUE,
    puntaje       TINYINT NOT NULL,
    comentario    TEXT,
    CONSTRAINT fk_calificaciones_solicitud
        FOREIGN KEY (solicitud_id) REFERENCES solicitudes(id) ON DELETE CASCADE,
    CONSTRAINT chk_calificaciones_puntaje CHECK (puntaje BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
