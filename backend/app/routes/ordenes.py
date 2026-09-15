from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from app.models.models import OrdenTrabajo, Servicio, Usuario, PerfilTecnico
from app.schemas.schemas import OrdenTrabajoCreate, OrdenTrabajoResponse
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/ordenes", tags=["ordenes"])


@router.post("/", response_model=OrdenTrabajoResponse, status_code=status.HTTP_201_CREATED)
async def crear_orden(
    orden: OrdenTrabajoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Crear nueva orden de trabajo (solo clientes)"""
    
    # Validar que sea cliente
    if current_user.tipo_usuario != 'cliente':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los clientes pueden crear órdenes"
        )
    
    # Validar que el servicio exista
    servicio = db.query(Servicio).filter(Servicio.id_servicio == orden.id_servicio).first()
    if not servicio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado")
    
    # Crear orden
    nueva_orden = OrdenTrabajo(
        id_cliente=current_user.user_id,
        id_servicio=orden.id_servicio,
        fecha_programada=orden.fecha_programada,
        ubicacion_servicio=orden.ubicacion_servicio,
        descripcion_problema=orden.descripcion_problema,
        notas_adicionales=orden.notas_adicionales,
        estado_orden='pendiente',
        precio_final=float(servicio.precio_base)
    )
    
    db.add(nueva_orden)
    db.commit()
    db.refresh(nueva_orden)
    
    return nueva_orden


@router.get("/", response_model=list[OrdenTrabajoResponse])
async def obtener_ordenes(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener órdenes (filtra según rol)"""
    
    if current_user.tipo_usuario == 'cliente':
        ordenes = db.query(OrdenTrabajo).filter(OrdenTrabajo.id_cliente == current_user.user_id).all()
    else:  # técnico
        ordenes = db.query(OrdenTrabajo).filter(OrdenTrabajo.id_tecnico == current_user.user_id).all()
    
    return ordenes


@router.get("/{orden_id}", response_model=OrdenTrabajoResponse)
async def obtener_orden(
    orden_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener una orden específica"""
    
    orden = db.query(OrdenTrabajo).filter(OrdenTrabajo.id_orden == orden_id).first()
    
    if not orden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada")
    
    # Validar acceso
    if current_user.tipo_usuario == 'cliente' and orden.id_cliente != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    
    if current_user.tipo_usuario == 'tecnico' and orden.id_tecnico != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    
    return orden


@router.patch("/{orden_id}/aceptar")
async def aceptar_orden(
    orden_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Aceptar una orden (solo técnicos)"""
    
    if current_user.tipo_usuario != 'tecnico':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los técnicos pueden aceptar órdenes"
        )
    
    orden = db.query(OrdenTrabajo).filter(OrdenTrabajo.id_orden == orden_id).first()
    
    if not orden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada")
    
    if orden.estado_orden != 'pendiente':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La orden no puede ser aceptada en este estado"
        )
    
    orden.id_tecnico = current_user.user_id
    orden.estado_orden = 'aceptada'
    
    db.commit()
    db.refresh(orden)
    
    return {"mensaje": "Orden aceptada", "orden": orden}
