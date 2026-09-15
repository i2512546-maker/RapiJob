# RapiJob - Plataforma de Contratación de Servicios Técnicos

Base de datos SQL completa para una plataforma de contratación de servicios técnicos.

## Descripción

**RapiJob** es un sistema integral de gestión para conectar técnicos con clientes que necesitan servicios tecnológicos de forma rápida y eficiente.

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

## Instalación Rápida

### Con Docker (Recomendado)
```bash
docker-compose up -d
```

Esto inicia:
- MySQL en puerto 3306
- FastAPI en puerto 8000

Acceder a la documentación: http://localhost:8000/docs

### Local
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Estructura del Proyecto

```
rapijob/
├── database/
│   └── plataforma_servicios_tecnicos.sql
├── backend/                    # API FastAPI
│   ├── app/
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── routes/            # Endpoints
│   │   └── middleware/        # Auth, RBAC
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Stack Tecnológico (Beta)

- **Backend**: FastAPI + Python 3.11
- **Base de Datos**: MySQL 8.0
- **ORM**: SQLAlchemy
- **Validación**: Pydantic
- **Autenticación**: JWT + bcrypt
- **Containerización**: Docker

## API Endpoints Base

**Autenticación:**
- `POST /api/auth/registro` - Registrar
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Perfil actual

**Servicios:**
- `GET /api/servicios/` - Listar todos
- `GET /api/servicios/{id}` - Obtener uno

**Órdenes:**
- `POST /api/ordenes/` - Crear (clientes)
- `GET /api/ordenes/` - Mis órdenes
- `PATCH /api/ordenes/{id}/aceptar` - Aceptar (técnicos)

## Versión

v1.0 - Versión inicial completa

## Autor

Desarrollo - 2026
