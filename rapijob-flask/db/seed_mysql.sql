-- RapiJob - Seed MySQL (Alwaysdata)
-- Categorías de ejemplo. Idempotente (INSERT IGNORE por nombre único).

SET NAMES utf8mb4;

INSERT IGNORE INTO categorias (nombre) VALUES
    ('Electricidad'),
    ('Gasfitería'),
    ('Cómputo y Redes'),
    ('Aire Acondicionado'),
    ('Electrodomésticos');
