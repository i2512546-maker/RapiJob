@echo off
REM ============================================================
REM Setup script para integración de KPIs en RapiJob (Windows)
REM Uso: setup_kpis.bat
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo 🚀 Iniciando setup de KPIs para RapiJob...
echo.

REM Verificar que DATABASE_URL esté configurado
if "!DATABASE_URL!"=="" (
    echo ❌ ERROR: La variable de entorno DATABASE_URL no está configurada
    echo Configúrala con: set DATABASE_URL=postgresql://user:password@localhost/rapijob
    pause
    exit /b 1
)

echo ✅ DATABASE_URL configurado
echo 📍 Base de datos: !DATABASE_URL!
echo.

REM Ejecutar script de KPIs
echo 📝 Ejecutando script de vistas SQL...
psql "!DATABASE_URL!" -f rapijob-flask\db\kpis.sql

if %errorlevel% neq 0 (
    echo ❌ Error al crear vistas SQL
    pause
    exit /b 1
)

echo ✅ Vistas SQL creadas exitosamente
echo.

REM Verificar que las vistas fueron creadas
echo 🔍 Verificando vistas creadas...
for /f %%i in ('psql "!DATABASE_URL!" -t -c "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public' AND (table_name LIKE 'v_%%' OR table_name LIKE 'mv_%%')" 2^>nul') do set VIEWS_COUNT=%%i

if "!VIEWS_COUNT!"=="" set VIEWS_COUNT=0
echo 📊 Vistas creadas: !VIEWS_COUNT!
echo.

REM Listar las vistas creadas
echo 📋 Listado de vistas disponibles:
psql "!DATABASE_URL!" -c "SELECT table_name FROM information_schema.views WHERE table_schema = 'public' AND (table_name LIKE 'v_%%' OR table_name LIKE 'mv_%%') ORDER BY table_name" 2>nul || echo No se pudo listar las vistas

echo.
echo ✅ Setup de KPIs completado exitosamente!
echo.
echo 📚 Próximos pasos:
echo 1. Reinicia el servidor backend: python -m uvicorn main:app --reload
echo 2. Accede a la documentación: http://localhost:8000/docs
echo 3. Prueba los endpoints de KPI en /api/kpi/*
echo.
echo 🔗 Endpoints disponibles:
echo   - GET /api/kpi/technician/{id}
echo   - GET /api/kpi/technicians
echo   - GET /api/kpi/client/{id}
echo   - GET /api/kpi/clients
echo   - GET /api/kpi/platform/summary
echo   - GET /api/kpi/platform/weekly
echo   - POST /api/kpi/platform/snapshot
echo.

pause
