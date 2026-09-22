# Ejemplos de Uso de KPIs - RapiJob

Esta guía contiene ejemplos prácticos de cómo usar los endpoints de KPI en RapiJob.

## Requisitos

- Servidor backend de RapiJob corriendo en `http://localhost:8000`
- Token JWT válido (obtenido después de login)
- Permisos de admin/supervisor para acceder a listas

## Setup

```bash
# Guardar el token en una variable (después de login)
export TOKEN="your_jwt_token_here"

# O en Windows PowerShell:
$env:TOKEN = "your_jwt_token_here"
```

## Ejemplos de Requests

### 1. Obtener KPIs de un Técnico Específico

```bash
# Bash/Linux/Mac
curl -X GET "http://localhost:8000/api/kpi/technician/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq .

# PowerShell (Windows)
$headers = @{
    "Authorization" = "Bearer $env:TOKEN"
    "Content-Type" = "application/json"
}
Invoke-RestMethod -Uri "http://localhost:8000/api/kpi/technician/550e8400-e29b-41d4-a716-446655440000" `
  -Headers $headers `
  -Method Get | ConvertTo-Json
```

**Respuesta esperada:**
```json
{
  "technician_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "acceptance_rate": 85.50,
  "avg_rating": 4.75,
  "total_reviews": 24,
  "total_earnings": 15500.00,
  "completed_jobs": 23,
  "first_time_fix_rate": 91.67,
  "completion_rate": 95.83,
  "total_assignments": 24,
  "avg_resolution_hours": 4.5,
  "applications_sent": 50,
  "applications_accepted": 30
}
```

### 2. Listar Técnicos Ordenados por Rating

```bash
# Obtener top 20 técnicos por rating
curl -X GET "http://localhost:8000/api/kpi/technicians?sort_by=avg_rating&order=DESC&limit=20" \
  -H "Authorization: Bearer $TOKEN" | jq '.data[] | {email, avg_rating, total_reviews, total_earnings}'

# Obtener técnicos ordenados por ingresos
curl -X GET "http://localhost:8000/api/kpi/technicians?sort_by=total_earnings&order=DESC&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq '.data[] | {email, total_earnings, completed_jobs}'
```

### 3. Listar Clientes por Gasto Total

```bash
# Obtener top 10 clientes por gasto
curl -X GET "http://localhost:8000/api/kpi/clients?sort_by=total_spent&order=DESC&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq '.data[] | {email, total_spent, jobs_published, jobs_completed}'
```

### 4. Obtener Resumen de Plataforma (últimos 7 días)

```bash
curl -X GET "http://localhost:8000/api/kpi/platform/summary?days=7" \
  -H "Authorization: Bearer $TOKEN" | jq '.summary, .total_jobs_7d, .total_revenue_7d'

# Respuesta esperada:
{
  "summary": [
    {
      "period_date": "2026-09-22T10:30:45.123456",
      "jobs_created": 45,
      "completion_rate": 87.5,
      "cancel_rate": 5.2,
      "gmv": 12500.00,
      "revenue": 1875.00,
      "take_rate": 15.0,
      "avg_match_hours": 2.3,
      "active_users": 125
    },
    ...
  ],
  "total_jobs_7d": 315,
  "avg_completion_rate_7d": 86.42,
  "total_revenue_7d": 13125.50,
  "avg_take_rate_7d": 15.25
}
```

### 5. Obtener Métricas Semanales (últimas 12 semanas)

```bash
curl -X GET "http://localhost:8000/api/kpi/platform/weekly?weeks=12" \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {period_date, jobs_created, revenue, take_rate}'
```

### 6. Refrescar Snapshots de Plataforma

```bash
# Solo disponible para admins
curl -X POST "http://localhost:8000/api/kpi/platform/snapshot" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Respuesta esperada:
{
  "status": "success",
  "message": "Métricas de plataforma actualizadas",
  "timestamp": "2026-09-22T10:30:45.123456"
}
```

## Scripts de Ejemplo

### Python

```python
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
TOKEN = "your_jwt_token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# 1. Obtener KPI de un técnico
tech_id = "550e8400-e29b-41d4-a716-446655440000"
response = requests.get(f"{BASE_URL}/api/kpi/technician/{tech_id}", headers=HEADERS)
tech_kpi = response.json()

print(f"Técnico: {tech_kpi['email']}")
print(f"Rating: {tech_kpi['avg_rating']}/5.0 ({tech_kpi['total_reviews']} reseñas)")
print(f"Ingresos: ${tech_kpi['total_earnings']:,.2f}")
print(f"Tasa de aceptación: {tech_kpi['acceptance_rate']}%")
print(f"Tasa de finalización: {tech_kpi['completion_rate']}%")

# 2. Listar top técnicos
response = requests.get(
    f"{BASE_URL}/api/kpi/technicians",
    params={"sort_by": "avg_rating", "order": "DESC", "limit": 10},
    headers=HEADERS
)
data = response.json()

print(f"\nTop {len(data['data'])} Técnicos:")
for i, tech in enumerate(data['data'], 1):
    print(f"{i}. {tech['email']} - Rating: {tech['avg_rating']}/5.0")

# 3. Obtener resumen de plataforma
response = requests.get(
    f"{BASE_URL}/api/kpi/platform/summary",
    params={"days": 30},
    headers=HEADERS
)
summary = response.json()

print(f"\nResumen últimos 30 días:")
print(f"Trabajos creados: {summary['total_jobs_7d']}")
print(f"Ingresos: ${summary['total_revenue_7d']:,.2f}")
print(f"Take rate promedio: {summary['avg_take_rate_7d']}%")
```

### JavaScript/Node.js

```javascript
const BASE_URL = "http://localhost:8000";
const TOKEN = "your_jwt_token";
const headers = { "Authorization": `Bearer ${TOKEN}` };

// 1. Obtener KPI de técnico
async function getTechnicianKPI(technicianId) {
  const response = await fetch(
    `${BASE_URL}/api/kpi/technician/${technicianId}`,
    { headers }
  );
  return response.json();
}

// 2. Listar técnicos ordenados
async function listTechnicians(sortBy = "avg_rating", limit = 10) {
  const params = new URLSearchParams({
    sort_by: sortBy,
    order: "DESC",
    limit: limit
  });
  
  const response = await fetch(
    `${BASE_URL}/api/kpi/technicians?${params}`,
    { headers }
  );
  return response.json();
}

// 3. Obtener resumen de plataforma
async function getPlatformSummary(days = 7) {
  const response = await fetch(
    `${BASE_URL}/api/kpi/platform/summary?days=${days}`,
    { headers }
  );
  return response.json();
}

// Uso:
(async () => {
  // Obtener top técnicos
  const topTechs = await listTechnicians("avg_rating", 5);
  console.log("Top 5 técnicos:", topTechs.data.map(t => ({
    email: t.email,
    rating: t.avg_rating,
    reviews: t.total_reviews
  })));
  
  // Obtener resumen de plataforma
  const summary = await getPlatformSummary(7);
  console.log("Resumen 7 días:", {
    jobsCreated: summary.total_jobs_7d,
    revenue: summary.total_revenue_7d,
    takeRate: summary.avg_take_rate_7d
  });
})();
```

## Casos de Uso Comunes

### 1. Dashboard de Administración

```bash
# Obtener datos para dashboard en 3 requests

# Resumen de plataforma
curl -s "http://localhost:8000/api/kpi/platform/summary?days=7" \
  -H "Authorization: Bearer $TOKEN" > platform_summary.json

# Top 10 técnicos
curl -s "http://localhost:8000/api/kpi/technicians?sort_by=avg_rating&limit=10" \
  -H "Authorization: Bearer $TOKEN" > top_technicians.json

# Top 10 clientes
curl -s "http://localhost:8000/api/kpi/clients?sort_by=total_spent&limit=10" \
  -H "Authorization: Bearer $TOKEN" > top_clients.json

# Procesarlos con jq
jq '.total_revenue_7d, .avg_completion_rate_7d' platform_summary.json
```

### 2. Reporte de Técnico

```bash
# Generar reporte de un técnico específico
TECH_ID="550e8400-e29b-41d4-a716-446655440000"

curl -s "http://localhost:8000/api/kpi/technician/$TECH_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '{
    email,
    rating: .avg_rating,
    reviews: .total_reviews,
    earnings: .total_earnings,
    completion_rate: .completion_rate,
    avgResolutionHours: .avg_resolution_hours,
    acceptanceRate: .acceptance_rate
  }'
```

### 3. Monitoreo de KPI en Tiempo Real

```bash
#!/bin/bash
# Script para monitorear KPIs cada 5 minutos

while true; do
  echo "=== $(date) ==="
  
  # Obtener resumen de plataforma (últimas 24 horas)
  curl -s "http://localhost:8000/api/kpi/platform/summary?days=1" \
    -H "Authorization: Bearer $TOKEN" | jq '{
      jobs: .total_jobs_7d,
      revenue: .total_revenue_7d,
      completion_rate: .avg_completion_rate_7d
    }'
  
  echo ""
  sleep 300  # Esperar 5 minutos
done
```

## Interpretación de Métricas

### Para Técnicos:
- **Rating > 4.5**: Excelente desempeño
- **Acceptance Rate > 80%**: Selectivo pero disponible
- **Completion Rate > 90%**: Muy confiable
- **First-time Fix > 90%**: Trabajo de alta calidad

### Para Clientes:
- **Jobs Completed / Published > 80%**: Cliente satisfecho, menos cancelaciones
- **Avg Rating Given > 4.0**: Técnicos de buena calidad
- **Low Avg Hiring Time**: Buena descripción de trabajos

### Para Plataforma:
- **Completion Rate > 85%**: Plataforma saludable
- **Take Rate 12-20%**: Rango óptimo
- **Avg Match Hours < 4**: Buen matching algoritmo
- **Revenue Growth MoM > 10%**: Crecimiento positivo

## Troubleshooting

### Error: "Token inválido"
- Genera un nuevo token haciendo login
- Verifica que no haya expirado

### Error: "No tiene permisos"
- Solo admin/supervisor pueden ver listas
- Verifica tu rol en el sistema

### Error: "Vista no encontrada"
- Ejecuta el script `setup_kpis.sh` o `setup_kpis.bat`
- Verifica que estés conectado a la base de datos correcta

## Performance

Para grandes volúmenes de datos:
- Usa paginación (default: 10, máx: 100 por request)
- Limita el rango de días (máx: 90)
- Considera almacenar en caché los resultados
- Ejecuta reportes en horarios de bajo uso
