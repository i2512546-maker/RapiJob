# Integración de KPIs - RapiJob

## Descripción General

Se ha integrado un sistema completo de KPIs (Key Performance Indicators) en la plataforma RapiJob que permite monitorear y analizar el desempeño de técnicos, clientes y la plataforma general.

## Archivos Creados

### 1. **rapijob-flask/db/kpis.sql**
Archivo SQL con todas las vistas de base de datos para calcular KPIs.

**Vistas incluidas:**
- **Técnico (7 KPIs):**
  - `v_tech_acceptance_rate`: Tasa de aceptación de aplicaciones
  - `v_tech_rating`: Rating promedio y total de reseñas
  - `v_tech_earnings`: Ingresos acumulados y trabajos completados
  - `v_tech_first_time_fix`: Tasa de trabajos sin necesidad de validación
  - `v_tech_completion_rate`: Tasa de finalización de asignaciones
  - `v_tech_resolution_time`: Tiempo promedio de resolución en horas
  - `v_tech_applied`: Aplicaciones enviadas y aceptadas
  - `v_tech_metrics`: Vista unificada de todos los KPIs de técnico

- **Cliente (4 KPIs):**
  - `v_client_metrics`: Vista unificada con todos los KPIs de cliente

- **Plataforma (3 niveles temporales):**
  - `v_platform_daily_metrics`: Métricas diarias
  - `v_platform_weekly_metrics`: Métricas semanales
  - `v_platform_monthly_metrics`: Métricas mensuales
  - `v_platform_summary`: Resumen de últimas semanas

**Métricas de plataforma incluidas:**
- Trabajos creados por período
- Tasa de finalización
- Tasa de cancelación
- GMV (Gross Merchandise Value)
- Ingresos
- Take rate (% de ingresos vs GMV)
- Tiempo promedio de matching
- Usuarios activos diarios/semanales/mensuales

### 2. **backend/app/routes/kpis.py**
Archivo con todos los endpoints API para acceder a los KPIs.

**Endpoints disponibles:**

#### KPIs de Técnico
- `GET /api/kpi/technician/{technician_id}` - Obtener KPIs de un técnico específico
- `GET /api/kpi/technicians` - Listar KPIs de todos los técnicos (admin/supervisor)
  - Parámetros:
    - `skip`: Número de registros a saltar (default: 0)
    - `limit`: Número de registros a retornar (default: 10, máx: 100)
    - `sort_by`: Campo para ordenamiento (avg_rating, acceptance_rate, total_earnings, completion_rate)
    - `order`: ASC o DESC (default: DESC)

#### KPIs de Cliente
- `GET /api/kpi/client/{client_id}` - Obtener KPIs de un cliente específico
- `GET /api/kpi/clients` - Listar KPIs de todos los clientes (admin/supervisor)
  - Parámetros:
    - `skip`: Número de registros a saltar (default: 0)
    - `limit`: Número de registros a retornar (default: 10, máx: 100)
    - `sort_by`: Campo para ordenamiento (jobs_published, jobs_completed, total_spent)
    - `order`: ASC o DESC (default: DESC)

#### KPIs de Plataforma
- `GET /api/kpi/platform/summary` - Resumen de métricas (admin/supervisor)
  - Parámetros:
    - `days`: Número de días a incluir (1-90, default: 7)
- `GET /api/kpi/platform/weekly` - Métricas semanales (admin/supervisor)
  - Parámetros:
    - `weeks`: Número de semanas a retornar (1-52, default: 4)
- `POST /api/kpi/platform/snapshot` - Refrescar vistas materializadas (admin)

### 3. **backend/app/schemas/schemas.py** (actualizado)
Se agregaron nuevos schemas Pydantic para las respuestas de KPI:

- `TechKPIResponse`: Respuesta de KPI individual de técnico
- `TechKPIListResponse`: Lista de KPIs de técnicos
- `ClientKPIResponse`: Respuesta de KPI individual de cliente
- `ClientKPIListResponse`: Lista de KPIs de clientes
- `PlatformMetricsResponse`: Respuesta de métricas de plataforma
- `PlatformSummaryResponse`: Resumen con agregados de plataforma

### 4. **backend/main.py** (actualizado)
Se actualizó para incluir el router de KPIs:
- Importación del módulo `kpis`
- Inclusión del router: `app.include_router(kpis.router)`

## KPIs de Técnico Explicados

| KPI | Fórmula | Rango | Interpretación |
|-----|---------|-------|-----------------|
| **Acceptance Rate** | Aplicaciones aceptadas / Total aplicaciones * 100 | 0-100% | Qué tan selectivo es el técnico |
| **Avg Rating** | Promedio de todas las reseñas | 1-5 | Calidad del trabajo percibida |
| **Total Earnings** | Suma de pagos completados | $+ | Ingresos acumulados |
| **First-time Fix Rate** | Trabajos sin validación adicional / Total * 100 | 0-100% | Calidad en primera instancia |
| **Completion Rate** | Trabajos en progreso / Total asignaciones * 100 | 0-100% | Fiabilidad para completar |
| **Avg Resolution Time** | Promedio de (fecha_finalización - fecha_asignación) | horas | Rapidez en completar trabajos |
| **Applications Sent** | Total de aplicaciones enviadas | 0+ | Actividad en la plataforma |

## KPIs de Cliente Explicados

| KPI | Descripción |
|-----|-----------|
| **Jobs Published** | Total de trabajos publicados |
| **Jobs Completed** | Trabajos finalizados exitosamente |
| **Jobs Cancelled** | Trabajos cancelados |
| **Avg Hiring Time** | Tiempo promedio entre publicación y asignación (horas) |
| **Avg Rating Given** | Promedio de reseñas otorgadas a técnicos |
| **Total Spent** | Gasto total en la plataforma |

## KPIs de Plataforma Explicados

| Métrica | Descripción |
|---------|-----------|
| **Jobs Created** | Número de trabajos creados en el período |
| **Completion Rate** | % de trabajos completados exitosamente |
| **Cancel Rate** | % de trabajos cancelados |
| **GMV** | Valor bruto de transacciones (budget_max sumado) |
| **Revenue** | Ingresos reales (pagos completados) |
| **Take Rate** | % de Revenue vs GMV |
| **Avg Match Hours** | Tiempo promedio hasta asignación de técnico |
| **Active Users** | Usuarios con actividad en el período |

## Instalación

### 1. Crear las vistas en PostgreSQL

```bash
# Conectar a la base de datos
psql $DATABASE_URL

# Ejecutar el script de KPIs
\i rapijob-flask/db/kpis.sql
```

O durante el setup inicial:
```bash
psql $DATABASE_URL -f rapijob-flask/db/kpis.sql
```

### 2. Verificar que los archivos estén en lugar

- ✅ `backend/app/routes/kpis.py` - Rutas creadas
- ✅ `backend/app/schemas/schemas.py` - Schemas actualizados
- ✅ `backend/main.py` - Router incluido
- ✅ `rapijob-flask/db/kpis.sql` - Vistas SQL

### 3. Reiniciar el backend

```bash
# Desde el directorio backend/
python -m uvicorn main:app --reload
```

## Ejemplos de Uso

### Obtener KPIs de un técnico específico
```bash
curl -X GET "http://localhost:8000/api/kpi/technician/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Listar todos los técnicos ordenados por rating
```bash
curl -X GET "http://localhost:8000/api/kpi/technicians?sort_by=avg_rating&order=DESC&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Obtener resumen de plataforma (últimos 30 días)
```bash
curl -X GET "http://localhost:8000/api/kpi/platform/summary?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Obtener métricas semanales
```bash
curl -X GET "http://localhost:8000/api/kpi/platform/weekly?weeks=12" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Control de Acceso

- **Usuarios regulares (Cliente/Técnico):**
  - Pueden ver sus propias métricas
  - Acceso denegado a datos de otros usuarios

- **Supervisores/Admins:**
  - Acceso completo a todos los KPIs
  - Pueden ordenar y filtrar listas
  - Pueden refrescar snapshots

- **Técnicos específicos:**
  - Solo ven sus propios KPIs

## Consideraciones de Rendimiento

1. **Índices**: Las vistas se basan en tablas con índices apropiados para optimizar queries
2. **Caché**: Para plataforma de alto volumen, considerar materializar vistas
3. **Refresh**: El endpoint `POST /api/kpi/platform/snapshot` puede ejecutarse via cron
4. **Paginación**: Todos los endpoints de lista incluyen paginación (default: 10)

## Extensibilidad

Para agregar nuevos KPIs:

1. Crear nueva vista SQL en `kpis.sql`
2. Agregar schema Pydantic en `backend/app/schemas/schemas.py`
3. Agregar endpoint en `backend/app/routes/kpis.py`
4. Ejecutar script SQL nuevamente en la BD

## Troubleshooting

### "Vista no encontrada"
- Asegúrate de ejecutar el script kpis.sql en la BD
- Verifica que estés usando PostgreSQL 16+

### "No tiene permisos"
- Solo admin/supervisor pueden ver listas de KPIs
- Técnicos/clientes solo ven sus propios datos

### "Datos inconsistentes"
- Las vistas se actualizan en tiempo real
- Para reportes históricos, usar tabla `kpi_snapshots` (a implementar)

## Referencias

- Documento técnico: `ARQUITECTURA_PROFESIONAL.md` (sección 5)
- Esquema BD: `rapijob-flask/db/schema.sql`
- Rutas API: `backend/main.py`
