# Backend RapiJob

## Instalación

### Opción 1: Instalación local

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### Opción 2: Con Docker

```bash
docker-compose up -d
```

## Configuración

1. Copiar `.env.example` a `.env`
2. Actualizar valores según tu entorno
3. Asegurar que MySQL está corriendo

## Ejecutar servidor

### Local
```bash
python main.py
```

O con uvicorn:
```bash
uvicorn main:app --reload --port 8000
```

### Docker
```bash
docker-compose up
```

## Documentación API

Una vez que el servidor esté corriendo:
- **Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints disponibles

### Autenticación
- `POST /api/auth/registro` - Registrar nuevo usuario
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Obtener usuario actual

### Servicios
- `GET /api/servicios/` - Listar servicios
- `GET /api/servicios/{id}` - Obtener servicio

### Órdenes
- `POST /api/ordenes/` - Crear orden
- `GET /api/ordenes/` - Listar órdenes del usuario
- `GET /api/ordenes/{id}` - Obtener orden específica
- `PATCH /api/ordenes/{id}/aceptar` - Aceptar orden (técnicos)

## Estructura del código

```
backend/
├── main.py              # Entrada principal
├── config.py            # Configuración
├── database.py          # Conexión a DB
├── requirements.txt     # Dependencias
├── Dockerfile          # Docker config
└── app/
    ├── models/         # Modelos SQLAlchemy
    ├── schemas/        # Schemas Pydantic
    ├── routes/         # Endpoints FastAPI
    └── middleware/     # Autenticación, etc
```
