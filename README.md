# Plataforma de Contratación de Servicios Técnicos

Base de datos SQL completa para una plataforma de contratación de servicios técnicos.

## Descripción

Sistema integral de gestión para conectar técnicos con clientes que necesitan servicios tecnológicos.

## Características

- **Gestión de Usuarios**: Clientes y técnicos con perfiles personalizados
- **Catálogo de Servicios**: Categorías y servicios configurables
- **Órdenes de Trabajo**: Sistema completo de contratos y seguimiento
- **Pagos**: Múltiples métodos de pago y gestión de transacciones
- **Reseñas y Calificaciones**: Sistema de retroalimentación y KPIs
- **Disponibilidad**: Gestión de horarios y zonas de servicio
- **Auditoría**: Trazabilidad completa de operaciones

## Tablas Principales

- `usuarios`: Registro de clientes y técnicos
- `perfiles_tecnicos`: Información profesional de técnicos
- `servicios`: Catálogo de servicios disponibles
- `ordenes_trabajo`: Contratos y solicitudes de servicio
- `pagos`: Registro de transacciones
- `resenas_calificaciones`: Sistema de puntuación y comentarios
- `disponibilidad_tecnicos`: Horarios de trabajo
- `auditoria_logs`: Trazabilidad de cambios

## Instalación

1. Importar el archivo SQL en MySQL
2. Crear la base de datos ejecutando el script completo
3. Los datos iniciales se cargan automáticamente

```sql
mysql -u root -p < plataforma_servicios_tecnicos.sql
```

## Estructura de Archivo

```
plataforma_servicios_tecnicos.sql
├── Creación de base de datos
├── Definición de tablas
├── Inserts de datos iniciales
├── Vistas útiles
└── Índices y relaciones
```

## Versión

v1.0 - Versión inicial completa

## Autor

Desarrollo - 2026
