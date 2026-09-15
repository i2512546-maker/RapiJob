from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from app.models.models import Servicio, CategoriaServicio
from app.schemas.schemas import ServicioResponse
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/servicios", tags=["servicios"])


@router.get("/", response_model=list[ServicioResponse])
async def obtener_servicios(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener todos los servicios disponibles"""
    servicios = db.query(Servicio).filter(Servicio.estado == 'disponible').all()
    return servicios


@router.get("/{servicio_id}", response_model=ServicioResponse)
async def obtener_servicio(
    servicio_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener un servicio específico"""
    servicio = db.query(Servicio).filter(Servicio.id_servicio == servicio_id).first()
    
    if not servicio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado")
    
    return servicio
