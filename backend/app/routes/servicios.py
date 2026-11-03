from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from app.models.models import Servicio
from app.schemas.schemas import ServicioResponse

router = APIRouter(prefix="/api/servicios", tags=["servicios"])


@router.get("/", response_model=list[ServicioResponse])
def obtener_servicios(db: Session = Depends(get_db)):
    """Catálogo público: cualquier visitante puede consultar los precios referenciales."""
    return db.query(Servicio).filter(Servicio.estado == "disponible").order_by(Servicio.nombre_servicio).all()


@router.get("/{servicio_id}", response_model=ServicioResponse)
def obtener_servicio(servicio_id: int, db: Session = Depends(get_db)):
    servicio = db.query(Servicio).filter(
        Servicio.id_servicio == servicio_id,
        Servicio.estado == "disponible",
    ).first()
    if not servicio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado.")
    return servicio
