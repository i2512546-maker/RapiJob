# KPI Quick Reference - RapiJob

## 📊 Estructura de KPIs

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA DE KPIs                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  TÉCNICOS (7 KPIs)                                   │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  📊 Tasa de Aceptación (%)                           │  │
│  │  ⭐ Rating Promedio (1-5)                            │  │
│  │  💰 Ingresos Totales ($)                             │  │
│  │  ✓ First-Time Fix (%)                                │  │
│  │  ⚡ Tasa de Finalización (%)                         │  │
│  │  ⏱️ Tiempo Resolución (horas)                         │  │
│  │  📝 Aplicaciones Enviadas (#)                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  CLIENTES (4 KPIs)                                   │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  📋 Trabajos Publicados (#)                          │  │
│  │  ✓ Trabajos Completados (#)                          │  │
│  │  ✗ Trabajos Cancelados (#)                           │  │
│  │  ⏱️ Tiempo Promedio Contratación (horas)             │  │
│  │  ⭐ Rating Promedio Otorgado (1-5)                   │  │
│  │  💸 Gasto Total ($)                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  PLATAFORMA (8 KPIs × 3 niveles temporales)          │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  📈 Trabajos Creados                                 │  │
│  │  ✓ Tasa Finalización (%)                             │  │
│  │  ✗ Tasa Cancelación (%)                              │  │
│  │  💼 GMV ($)                                          │  │
│  │  💰 Ingresos ($)                                     │  │
│  │  📊 Take Rate (%)                                    │  │
│  │  ⏱️ Matching Time (horas)                             │  │
│  │  👥 Usuarios Activos (#)                             │  │
│  │                                                       │  │
│  │  Disponible en: DIARIO | SEMANAL | MENSUAL           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🔌 Endpoints Rápido

### 👤 Técnico
```
GET  /api/kpi/technician/{id}        → KPI específico
GET  /api/kpi/technicians?...         → Lista con filtros
```

### 👥 Cliente  
```
GET  /api/kpi/client/{id}             → KPI específico
GET  /api/kpi/clients?...             → Lista con filtros
```

### 📊 Plataforma
```
GET  /api/kpi/platform/summary?days=7 → Resumen diario
GET  /api/kpi/platform/weekly?weeks=4 → Métricas semanales
POST /api/kpi/platform/snapshot       → Refrescar vistas
```

## 📈 Interpretar Valores

### Técnico
```
Rating ⭐
  4.8-5.0 → Excelente
  4.0-4.7 → Muy bueno
  3.0-3.9 → Aceptable
  < 3.0  → Revisar

Acceptance Rate 📊
  > 80%  → Selectivo
  50-80% → Moderado
  < 50%  → Muy disponible

Completion Rate ⚡
  > 95%  → Muy confiable
  90-95% → Confiable
  < 90%  → Revisar comportamiento

First-Time Fix ✓
  > 90%  → Excelente calidad
  75-90% → Buena calidad
  < 75%  → Mejorar proceso
```

### Plataforma
```
Completion Rate ✓
  > 85%  → Plataforma saludable
  70-85% → Necesita mejora
  < 70%  → Crítico

Take Rate 📊
  12-20% → Óptimo
  < 12%  → Bajo (revisar pricing)
  > 20%  → Alto (revisar commission)

Avg Match Hours ⏱️
  < 2h   → Excelente
  2-4h   → Bueno
  > 4h   → Lento (revisar algoritmo)
```

## 🔐 Permisos

```
Técnico/Cliente
├─ Ver su propio KPI ✓
└─ Ver otros KPIs ✗

Supervisor
├─ Ver todos los KPIs ✓
├─ Ver listas ordenadas ✓
├─ Refrescar snapshots ✗

Admin  
├─ Ver todos los KPIs ✓
├─ Ver listas ordenadas ✓
└─ Refrescar snapshots ✓
```

## 🚀 Quickstart

### 1. Instalar
```bash
# Linux/Mac
bash setup_kpis.sh

# Windows  
setup_kpis.bat
```

### 2. Probar
```bash
# Obtener token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -d '{"email":"admin@example.com","password":"password"}' | jq -r '.access_token')

# Probar endpoint
curl "http://localhost:8000/api/kpi/platform/summary?days=7" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Ver en Swagger
```
http://localhost:8000/docs
```

## 📊 SQL Views

```
TÉCNICO
├─ v_tech_acceptance_rate
├─ v_tech_rating
├─ v_tech_earnings
├─ v_tech_first_time_fix
├─ v_tech_completion_rate
├─ v_tech_resolution_time
├─ v_tech_applied
└─ v_tech_metrics ★

CLIENTE
└─ v_client_metrics ★

PLATAFORMA
├─ v_platform_daily_metrics
├─ v_platform_weekly_metrics
├─ v_platform_monthly_metrics
└─ v_platform_summary

★ = Vista consolidada/unificada
```

## 📝 Schemas Python

```python
# Respuesta de técnico
TechKPIResponse(
    technician_id: str,
    email: str,
    acceptance_rate: Decimal,
    avg_rating: Decimal,
    total_earnings: Decimal,
    ...
)

# Respuesta de cliente
ClientKPIResponse(
    client_id: str,
    email: str,
    jobs_published: int,
    total_spent: Decimal,
    ...
)

# Respuesta de plataforma
PlatformMetricsResponse(
    period_date: datetime,
    jobs_created: int,
    completion_rate: Decimal,
    revenue: Decimal,
    ...
)
```

## ⚙️ Parámetros

### Paginación
```
skip=0          # Saltar primeros N registros
limit=10        # Máximo 100 registros
```

### Ordenamiento
```
sort_by=avg_rating      # Campo a ordenar
order=DESC              # ASC o DESC
```

### Temporal
```
days=7                  # 1-90 días
weeks=4                 # 1-52 semanas
```

## 📚 Archivos

```
📁 rapijob-flask/db/
   └─ kpis.sql (15+ vistas SQL)

📁 backend/app/routes/
   └─ kpis.py (7 endpoints)

📁 backend/app/schemas/
   └─ schemas.py (+6 schemas)

📁 root/
   ├─ KPI_INTEGRATION.md (técnico)
   ├─ KPI_USAGE_EXAMPLES.md (práctico)
   ├─ KPI_SUMMARY.md (resumen)
   ├─ setup_kpis.sh (Linux/Mac)
   └─ setup_kpis.bat (Windows)
```

## 🎯 Uso Típico

### Dashboard Admin
```bash
GET /api/kpi/platform/summary?days=7
GET /api/kpi/technicians?sort_by=avg_rating&limit=10
GET /api/kpi/clients?sort_by=total_spent&limit=10
```

### Perfil Técnico
```bash
GET /api/kpi/technician/{id}
```

### Perfil Cliente
```bash
GET /api/kpi/client/{id}
```

### Reportes
```bash
GET /api/kpi/platform/weekly?weeks=12
GET /api/kpi/platform/summary?days=30
```

## 🔗 URLs

```
Docs:     http://localhost:8000/docs
API Base: http://localhost:8000/api/kpi
DB:       postgresql://localhost/rapijob
```

## ✅ Checklist

- [ ] Ejecutar setup_kpis.sh / setup_kpis.bat
- [ ] Verificar que vistas SQL están creadas
- [ ] Reiniciar backend
- [ ] Acceder a /docs en el navegador
- [ ] Probar GET /api/kpi/platform/summary
- [ ] Integrar en dashboard frontend
- [ ] Configurar alertas automáticas
- [ ] Documentar en wiki interna

## 🚨 Errores Comunes

```
❌ "Vista no encontrada"
✓ Solución: Ejecutar setup script

❌ "No tiene permisos"  
✓ Solución: Usar token de admin/supervisor

❌ "Timeout"
✓ Solución: Reducir rango de dates/weeks

❌ "Datos inconsistentes"
✓ Solución: Ejecutar POST /api/kpi/platform/snapshot
```

## 📞 Soporte

**Documentación Completa:**
- 📖 KPI_INTEGRATION.md (detalles técnicos)
- 📖 KPI_USAGE_EXAMPLES.md (ejemplos prácticos)

**Contacto:**
- Issues: Abrir issue en repositorio
- Docs: Ver /docs en aplicación
- Logs: Revisar backend logs

---

**v1.0** | 22 Sep 2026 | Producción lista ✅
