#!/bin/bash
# ============================================================
# Setup script para integración de KPIs en RapiJob
# Uso: bash setup_kpis.sh
# ============================================================

set -e

echo "🚀 Iniciando setup de KPIs para RapiJob..."

# Verificar que DATABASE_URL esté configurado
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: La variable de entorno DATABASE_URL no está configurada"
    echo "Configúrala con: export DATABASE_URL='postgresql://user:password@localhost/rapijob'"
    exit 1
fi

echo "✅ DATABASE_URL configurado"
echo "📍 Base de datos: $DATABASE_URL"

# Convertir postgres:// a postgresql+psycopg2:// si es necesario
DB_URL="$DATABASE_URL"
if [[ $DB_URL == postgres://* ]]; then
    DB_URL="postgresql+psycopg2://${DB_URL#postgres://}"
fi

# Ejecutar script de KPIs
echo "📝 Ejecutando script de vistas SQL..."
psql "$DATABASE_URL" -f rapijob-flask/db/kpis.sql

if [ $? -eq 0 ]; then
    echo "✅ Vistas SQL creadas exitosamente"
else
    echo "❌ Error al crear vistas SQL"
    exit 1
fi

# Verificar que las vistas fueron creadas
echo "🔍 Verificando vistas creadas..."
VIEWS_COUNT=$(psql "$DATABASE_URL" -t -c "
    SELECT COUNT(*) FROM information_schema.views 
    WHERE table_schema = 'public' 
    AND table_name LIKE 'v_%kpi%' OR table_name LIKE 'v_%metrics%' OR table_name LIKE 'v_client%'
" 2>/dev/null || echo "0")

echo "📊 Vistas creadas: $VIEWS_COUNT"

# Listar las vistas creadas
echo ""
echo "📋 Listado de vistas disponibles:"
psql "$DATABASE_URL" -c "
    SELECT table_name 
    FROM information_schema.views 
    WHERE table_schema = 'public' 
    AND (table_name LIKE 'v_%' OR table_name LIKE 'mv_%')
    ORDER BY table_name
" 2>/dev/null || echo "No se pudo listar las vistas"

echo ""
echo "✅ Setup de KPIs completado exitosamente!"
echo ""
echo "📚 Próximos pasos:"
echo "1. Reinicia el servidor backend: python -m uvicorn main:app --reload"
echo "2. Accede a la documentación: http://localhost:8000/docs"
echo "3. Prueba los endpoints de KPI en /api/kpi/*"
echo ""
echo "🔗 Endpoints disponibles:"
echo "  - GET /api/kpi/technician/{id}"
echo "  - GET /api/kpi/technicians"
echo "  - GET /api/kpi/client/{id}"
echo "  - GET /api/kpi/clients"
echo "  - GET /api/kpi/platform/summary"
echo "  - GET /api/kpi/platform/weekly"
echo "  - POST /api/kpi/platform/snapshot"
echo ""
