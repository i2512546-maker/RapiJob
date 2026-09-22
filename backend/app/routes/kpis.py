from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db
from app.middleware.auth import get_current_user
from app.schemas.schemas import (
    TechKPIResponse,
    TechKPIListResponse,
    ClientKPIResponse,
    ClientKPIListResponse,
    PlatformMetricsResponse,
    PlatformSummaryResponse,
)
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/kpi", tags=["kpi"])


# ============================================================
# KPIs DE TÉCNICO
# ============================================================

@router.get(
    "/technician/{technician_id}",
    response_model=TechKPIResponse,
    status_code=status.HTTP_200_OK
)
async def get_technician_kpi(
    technician_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener KPIs detallados de un técnico específico.
    
    Métricas incluidas:
    - Tasa de aceptación de aplicaciones
    - Rating promedio
    - Ingresos totales
    - Tasa de first-time fix
    - Tasa de finalización
    - Tiempo de resolución promedio
    - Aplicaciones enviadas
    """
    query = """
        SELECT 
            technician_id::text,
            email,
            acceptance_rate,
            avg_rating,
            total_reviews,
            total_earnings,
            completed_jobs,
            first_time_fix_rate,
            completion_rate,
            total_assignments,
            avg_resolution_hours,
            applications_sent,
            applications_accepted
        FROM v_tech_metrics
        WHERE technician_id::text = :technician_id
    """
    
    result = db.execute(text(query), {"technician_id": technician_id}).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Técnico no encontrado"
        )
    
    return TechKPIResponse(
        technician_id=result[0],
        email=result[1],
        acceptance_rate=result[2],
        avg_rating=result[3],
        total_reviews=result[4],
        total_earnings=result[5],
        completed_jobs=result[6],
        first_time_fix_rate=result[7],
        completion_rate=result[8],
        total_assignments=result[9],
        avg_resolution_hours=result[10],
        applications_sent=result[11],
        applications_accepted=result[12],
    )


@router.get(
    "/technicians",
    response_model=TechKPIListResponse,
    status_code=status.HTTP_200_OK
)
async def list_technician_kpis(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("avg_rating", regex="^(avg_rating|acceptance_rate|total_earnings|completion_rate)$"),
    order: str = Query("DESC", regex="^(ASC|DESC)$"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Listar KPIs de todos los técnicos con paginación y ordenamiento.
    
    Parámetros de ordenamiento:
    - avg_rating: ordenar por calificación promedio
    - acceptance_rate: ordenar por tasa de aceptación
    - total_earnings: ordenar por ingresos totales
    - completion_rate: ordenar por tasa de finalización
    """
    # Validar que solo admin o supervisor puedan acceder
    if current_user.tipo_usuario not in ['admin', 'supervisor']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a esta información"
        )
    
    # Construir query con validación de SQL injection
    allowed_columns = {
        "avg_rating": "avg_rating",
        "acceptance_rate": "acceptance_rate",
        "total_earnings": "total_earnings",
        "completion_rate": "completion_rate"
    }
    sort_column = allowed_columns.get(sort_by, "avg_rating")
    
    count_query = "SELECT COUNT(*) FROM v_tech_metrics"
    total = db.execute(text(count_query)).scalar()
    
    query = f"""
        SELECT 
            technician_id::text,
            email,
            acceptance_rate,
            avg_rating,
            total_reviews,
            total_earnings,
            completed_jobs,
            first_time_fix_rate,
            completion_rate,
            total_assignments,
            avg_resolution_hours,
            applications_sent,
            applications_accepted
        FROM v_tech_metrics
        ORDER BY {sort_column} {order}
        LIMIT :limit OFFSET :skip
    """
    
    results = db.execute(
        text(query),
        {"skip": skip, "limit": limit}
    ).fetchall()
    
    data = [
        TechKPIResponse(
            technician_id=r[0],
            email=r[1],
            acceptance_rate=r[2],
            avg_rating=r[3],
            total_reviews=r[4],
            total_earnings=r[5],
            completed_jobs=r[6],
            first_time_fix_rate=r[7],
            completion_rate=r[8],
            total_assignments=r[9],
            avg_resolution_hours=r[10],
            applications_sent=r[11],
            applications_accepted=r[12],
        )
        for r in results
    ]
    
    return TechKPIListResponse(total=total, data=data)


# ============================================================
# KPIs DE CLIENTE
# ============================================================

@router.get(
    "/client/{client_id}",
    response_model=ClientKPIResponse,
    status_code=status.HTTP_200_OK
)
async def get_client_kpi(
    client_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener KPIs detallados de un cliente específico.
    
    Métricas incluidas:
    - Trabajos publicados
    - Trabajos completados/cancelados
    - Tiempo promedio de contratación
    - Rating promedio otorgado
    - Gasto total en plataforma
    """
    query = """
        SELECT 
            client_id::text,
            email,
            jobs_published,
            jobs_completed,
            jobs_cancelled,
            avg_hiring_time_hours,
            avg_rating_given,
            total_spent
        FROM v_client_metrics
        WHERE client_id::text = :client_id
    """
    
    result = db.execute(text(query), {"client_id": client_id}).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    return ClientKPIResponse(
        client_id=result[0],
        email=result[1],
        jobs_published=result[2],
        jobs_completed=result[3],
        jobs_cancelled=result[4],
        avg_hiring_time_hours=result[5],
        avg_rating_given=result[6],
        total_spent=result[7],
    )


@router.get(
    "/clients",
    response_model=ClientKPIListResponse,
    status_code=status.HTTP_200_OK
)
async def list_client_kpis(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("jobs_published", regex="^(jobs_published|jobs_completed|total_spent)$"),
    order: str = Query("DESC", regex="^(ASC|DESC)$"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Listar KPIs de todos los clientes con paginación y ordenamiento.
    
    Parámetros de ordenamiento:
    - jobs_published: ordenar por trabajos publicados
    - jobs_completed: ordenar por trabajos completados
    - total_spent: ordenar por gasto total
    """
    # Validar que solo admin o supervisor puedan acceder
    if current_user.tipo_usuario not in ['admin', 'supervisor']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a esta información"
        )
    
    allowed_columns = {
        "jobs_published": "jobs_published",
        "jobs_completed": "jobs_completed",
        "total_spent": "total_spent"
    }
    sort_column = allowed_columns.get(sort_by, "jobs_published")
    
    count_query = "SELECT COUNT(*) FROM v_client_metrics"
    total = db.execute(text(count_query)).scalar()
    
    query = f"""
        SELECT 
            client_id::text,
            email,
            jobs_published,
            jobs_completed,
            jobs_cancelled,
            avg_hiring_time_hours,
            avg_rating_given,
            total_spent
        FROM v_client_metrics
        ORDER BY {sort_column} {order}
        LIMIT :limit OFFSET :skip
    """
    
    results = db.execute(
        text(query),
        {"skip": skip, "limit": limit}
    ).fetchall()
    
    data = [
        ClientKPIResponse(
            client_id=r[0],
            email=r[1],
            jobs_published=r[2],
            jobs_completed=r[3],
            jobs_cancelled=r[4],
            avg_hiring_time_hours=r[5],
            avg_rating_given=r[6],
            total_spent=r[7],
        )
        for r in results
    ]
    
    return ClientKPIListResponse(total=total, data=data)


# ============================================================
# KPIs DE PLATAFORMA
# ============================================================

@router.get(
    "/platform/summary",
    response_model=PlatformSummaryResponse,
    status_code=status.HTTP_200_OK
)
async def get_platform_summary(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener resumen de métricas de plataforma para los últimos N días.
    
    Métricas incluidas:
    - Trabajos creados
    - Tasa de finalización
    - Tasa de cancelación
    - GMV (Gross Merchandise Value)
    - Ingresos
    - Take rate
    - Tiempo promedio de matching
    - Usuarios activos
    """
    # Validar que solo admin o supervisor puedan acceder
    if current_user.tipo_usuario not in ['admin', 'supervisor']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a esta información"
        )
    
    query = """
        SELECT 
            period_date,
            jobs_created,
            completion_rate,
            cancel_rate,
            gmv,
            revenue,
            take_rate,
            avg_match_hours,
            active_users
        FROM v_platform_daily_metrics
        WHERE metric_date >= CURRENT_DATE - INTERVAL ':days days'
        ORDER BY metric_date DESC
    """
    
    results = db.execute(
        text(query.replace(":days days", f"'{days} days'")),
        {"days": days}
    ).fetchall()
    
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay datos disponibles"
        )
    
    summary_data = [
        PlatformMetricsResponse(
            period_date=r[0],
            jobs_created=r[1],
            completion_rate=r[2],
            cancel_rate=r[3],
            gmv=r[4],
            revenue=r[5],
            take_rate=r[6],
            avg_match_hours=r[7],
            active_users=r[8],
        )
        for r in results
    ]
    
    # Calcular agregados
    total_jobs = sum(m.jobs_created for m in summary_data)
    avg_completion = sum(m.completion_rate for m in summary_data) / len(summary_data) if summary_data else 0
    total_revenue = sum(m.revenue for m in summary_data if m.revenue)
    avg_take_rate = sum(m.take_rate for m in summary_data if m.take_rate) / len([m for m in summary_data if m.take_rate]) if summary_data else 0
    
    return PlatformSummaryResponse(
        summary=summary_data,
        total_jobs_7d=total_jobs,
        avg_completion_rate_7d=avg_completion,
        total_revenue_7d=total_revenue,
        avg_take_rate_7d=avg_take_rate
    )


@router.get(
    "/platform/weekly",
    response_model=list[PlatformMetricsResponse],
    status_code=status.HTTP_200_OK
)
async def get_platform_weekly_metrics(
    weeks: int = Query(4, ge=1, le=52),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener métricas semanales de plataforma.
    """
    # Validar permisos
    if current_user.tipo_usuario not in ['admin', 'supervisor']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a esta información"
        )
    
    query = """
        SELECT 
            week_start::timestamp,
            jobs_created,
            completion_rate,
            cancel_rate,
            gmv,
            revenue,
            take_rate,
            avg_match_hours,
            weekly_active_users
        FROM v_platform_weekly_metrics
        ORDER BY week_start DESC
        LIMIT :weeks
    """
    
    results = db.execute(
        text(query),
        {"weeks": weeks}
    ).fetchall()
    
    return [
        PlatformMetricsResponse(
            period_date=r[0],
            jobs_created=r[1],
            completion_rate=r[2],
            cancel_rate=r[3],
            gmv=r[4],
            revenue=r[5],
            take_rate=r[6],
            avg_match_hours=r[7],
            active_users=r[8],
        )
        for r in results
    ]


@router.post(
    "/platform/snapshot",
    status_code=status.HTTP_200_OK
)
async def refresh_platform_snapshot(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Refrescar vistas materializadas de métricas de plataforma.
    Normalmente se ejecuta via un worker/cron, pero también disponible
    como endpoint administrativo.
    """
    # Validar que solo admin puede ejecutar
    if current_user.tipo_usuario != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden refrescar snapshots"
        )
    
    try:
        # En PostgreSQL, las vistas que no son materializadas se actualizan
        # automáticamente. Si se implementan vistas materializadas:
        # db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_platform_metrics"))
        # Por ahora, simplemente retornamos que las vistas están actualizadas
        return {
            "status": "success",
            "message": "Métricas de plataforma actualizadas",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al refrescar snapshot: {str(e)}"
        )
