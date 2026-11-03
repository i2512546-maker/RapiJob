# RapiJob

Plataforma web para conectar clientes con técnicos de computadoras, laptops, software y redes.

## Funciones
- Registro e inicio de sesión con contraseña protegida y token JWT.
- Roles de cliente y técnico.
- Catálogo público de servicios y precios referenciales.
- Precios expresados en soles peruanos (PEN).
- Solicitud de citas en horarios disponibles.
- Panel de solicitudes del cliente.
- Panel del técnico para aceptar y cancelar solicitudes.
- No se procesan pagos ni se solicitan datos bancarios. El precio publicado es orientativo; el técnico confirma el importe final después de revisar el problema.

## Tecnología
- Backend: FastAPI + SQLAlchemy.
- Base de datos: MySQL 8 (Docker) o SQLite para desarrollo.
- Frontend: HTML, CSS y JavaScript servido por FastAPI.
- Autenticación: JWT y contraseñas con bcrypt.

## Ejecutar localmente con Docker
Requiere Docker Desktop y Docker Compose.

```bash
docker compose up --build
```

Abrir:
- Web: http://localhost:8000
- API: http://localhost:8000/docs
- Estado: http://localhost:8000/health

El backend crea las tablas desde los modelos al iniciar y agrega servicios referenciales y horarios iniciales cuando la base está vacía. No importes el antiguo archivo SQL de demostración sobre una base ya existente: su estructura anterior no coincide completamente con los modelos actuales.

Para detener:
```bash
docker compose down
```

Los datos de MySQL se conservan en el volumen `mysql_data`. Para reiniciar la base desde cero (esto elimina los datos):
```bash
docker compose down -v
docker compose up --build
```

## Ejecutar el backend sin Docker
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Por defecto se usa SQLite en `backend/rapijob.db`. Para MySQL, configura `DATABASE_URL` en el entorno. En producción define una `SECRET_KEY` larga y aleatoria y una base de datos persistente.

## API principal
- `POST /api/auth/registro`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/servicios/`
- `GET /api/servicios/{id}`
- `GET /api/admin/slots-citas/`
- `POST /api/ordenes/`
- `GET /api/ordenes/`
- `PATCH /api/ordenes/{id}/aceptar`
- `PATCH /api/ordenes/{id}/cancelar`

## Importante sobre precios
Los importes del catálogo son referencias iniciales para Perú, no cotizaciones garantizadas ni pagos realizados. El técnico debe confirmar el precio final según el diagnóstico, repuestos y complejidad del trabajo.

## Rama de mantenimiento
Los cambios de corrección se trabajan en `fix/rapijob-full-stack` para poder revisarlos antes de integrarlos en `main`.

## Portal ampliado y mapa de técnicos

La página incluye categorías de servicios, un directorio con perfiles de demostración y filtros por ciudad, especialidad, disponibilidad y distancia. Los perfiles y reseñas de muestra son ficticios y no representan técnicos registrados.

### Activar Google Maps

1. Crea una clave de navegador en Google Cloud y habilita **Maps JavaScript API** y **Geocoding API**.
2. Restringe la clave por los dominios de tu sitio (por ejemplo, `rapijob-2.onrender.com`) y por las APIs anteriores.
3. En Render, abre el servicio `rapijob-api`, entra a **Environment** y agrega `GOOGLE_MAPS_API_KEY` con esa clave.
4. Guarda los cambios y vuelve a desplegar.

La clave se entrega al navegador porque Google Maps JavaScript la necesita; por eso debe tener restricciones por dominio y API. No uses una clave de servidor sin restricciones en esta variable.

### Alcance actual

- El catálogo y las solicitudes utilizan la API FastAPI existente.
- El directorio de técnicos, reseñas, ubicaciones y marcadores visibles en el mapa son datos demostrativos.
- La selección de ubicación y la geolocalización requieren que Google Maps esté configurado y que el usuario otorgue permiso.
- El sistema todavía no incluye carga persistente de fotografías, verificación administrativa de técnicos, chat/seguimiento en tiempo real ni integración con Supabase. Estas funciones requieren ampliar el backend y configurar servicios externos.
