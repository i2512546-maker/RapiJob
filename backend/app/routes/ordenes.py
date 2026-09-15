from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from app.models.models import OrdenTrabajo, Servicio, SlotCita, MetodoPago
from app.schemas.schemas import OrdenTrabajoCreate, OrdenTrabajoUpdate, OrdenTrabajoResponse
from app.middleware.auth import get_current_user
from decimal import Decimal

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
    
    # Validar servicio
    servicio = db.query(Servicio).filter(Servicio.id_servicio == orden.id_servicio).first()
    if not servicio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado")
    
    # Validar slot disponible
    slot = db.query(SlotCita).filter(SlotCita.id_slot == orden.id_slot_cita).first()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot no disponible")
    
    if slot.estado != 'disponible':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El slot no está disponible"
        )
    
    if slot.reservas_actuales >= slot.capacidad_maxima:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El slot está lleno"
        )
    
    # Validar método de pago
    metodo = db.query(MetodoPago).filter(
        MetodoPago.id_metodo == orden.id_metodo_pago,
        MetodoPago.estado == 'activo'
    ).first()
    if not metodo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Método de pago no válido")
    
    # Calcular precio final
    precio_base = Decimal(str(servicio.precio_base))
    precio_negociado = orden.precio_negociado or precio_base
    
    # Validar que precio negociado sea válido (no menos del 50% del base)
    if precio_negociado < (precio_base * Decimal('0.5')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Precio mínimo permitido es {precio_base * Decimal('0.5')}"
        )
    
    # Crear orden
    nueva_orden = OrdenTrabajo(
        id_cliente=current_user.user_id,
        id_servicio=orden.id_servicio,
        id_slot_cita=orden.id_slot_cita,
        id_metodo_pago=orden.id_metodo_pago,
        
        ubicacion_servicio=orden.ubicacion_servicio,
        descripcion_problema=orden.descripcion_problema,
        notas_adicionales=orden.notas_adicionales,
        
        precio_base=precio_base,
        precio_negociado=precio_negociado,
        precio_final=precio_negociado,
        
        estado_orden='pendiente',
        estado_pago='pendiente'
    )
    
    # Reservar slot
    slot.reservas_actuales += 1
    if slot.reservas_actuales >= slot.capacidad_maxima:
        slot.estado = 'lleno'
    
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


@router.patch("/{orden_id}/negociar-precio")
async def negociar_precio(
    orden_id: int,
    actualizacion: OrdenTrabajoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Negociar precio de la orden (cliente)"""
    
    if current_user.tipo_usuario != 'cliente':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los clientes pueden negociar"
        )
    
    orden = db.query(OrdenTrabajo).filter(OrdenTrabajo.id_orden == orden_id).first()
    
    if not orden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada")
    
    if orden.id_cliente != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    
    if orden.estado_orden != 'pendiente':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La orden no puede ser negociada en este estado"
        )
    
    # Validar precio mínimo
    if actualizacion.precio_negociado < (orden.precio_base * Decimal('0.5')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Precio mínimo permitido es {orden.precio_base * Decimal('0.5')}"
        )
    
    orden.precio_negociado = actualizacion.precio_negociado
    orden.precio_final = actualizacion.precio_negociado
    
    db.commit()
    db.refresh(orden)
    
    return {"mensaje": "Precio actualizado", "precio_final": orden.precio_final}


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


@router.patch("/{orden_id}/cancelar")
async def cancelar_orden(
    orden_id: int,
    razon: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Cancelar una orden"""
    
    orden = db.query(OrdenTrabajo).filter(OrdenTrabajo.id_orden == orden_id).first()
    
    if not orden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada")
    
    # Validar permisos
    es_cliente = current_user.tipo_usuario == 'cliente' and orden.id_cliente == current_user.user_id
    es_tecnico = current_user.tipo_usuario == 'tecnico' and orden.id_tecnico == current_user.user_id
    
    if not (es_cliente or es_tecnico):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    
    if orden.estado_orden not in ['pendiente', 'aceptada']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La orden no puede ser cancelada en este estado"
        )
    
    # Liberar slot
    slot = db.query(SlotCita).filter(SlotCita.id_slot == orden.id_slot_cita).first()
    if slot and slot.reservas_actuales > 0:
        slot.reservas_actuales -= 1
        if slot.estado == 'lleno':
            slot.estado = 'disponible'
    
    orden.estado_orden = 'cancelada'
    orden.razon_cancelacion = razon
    
    db.commit()
    db.refresh(orden)
    
    return {"mensaje": "Orden cancelada", "orden": orden}
