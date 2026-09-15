from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from app.models.models import SlotCita
from app.schemas.schemas import SlotCitaCreate, SlotCitaResponse
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/admin/slots-citas", tags=["admin"])


async def verificar_admin(current_user = Depends(get_current_user)):
    """Verificar que sea administrador"""
    # TODO: Implementar rol de admin
    return current_user


@router.post("/", response_model=SlotCitaResponse, status_code=status.HTTP_201_CREATED)
async def crear_slot_cita(
    slot: SlotCitaCreate,
    db: Session = Depends(get_db),
    admin = Depends(verificar_admin)
):
    """Crear nuevo slot de cita (admin)"""
    
    # Validar que hora_inicio < hora_fin
    if slot.hora_inicio >= slot.hora_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La hora inicio debe ser menor a hora fin"
        )
    
    # Validar que no haya conflicto de horarios
    conflicto = db.query(SlotCita).filter(
        SlotCita.fecha == slot.fecha,
        SlotCita.hora_inicio < slot.hora_fin,
        SlotCita.hora_fin > slot.hora_inicio,
        SlotCita.estado != 'bloqueado'
    ).first()
    
    if conflicto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Existe un conflicto de horarios en ese rango"
        )
    
    nuevo_slot = SlotCita(
        fecha=slot.fecha,
        hora_inicio=slot.hora_inicio,
        hora_fin=slot.hora_fin,
        capacidad_maxima=slot.capacidad_maxima,
        reservas_actuales=0,
        estado='disponible'
    )
    
    db.add(nuevo_slot)
    db.commit()
    db.refresh(nuevo_slot)
    
    return nuevo_slot


@router.get("/", response_model=list[SlotCitaResponse])
async def obtener_slots_disponibles(
    fecha_desde: datetime = None,
    fecha_hasta: datetime = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener slots disponibles (filtrar por fecha si se proporciona)"""
    
    query = db.query(SlotCita).filter(SlotCita.estado == 'disponible')
    
    if fecha_desde:
        query = query.filter(SlotCita.fecha >= fecha_desde)
    
    if fecha_hasta:
        query = query.filter(SlotCita.fecha <= fecha_hasta)
    
    slots = query.order_by(SlotCita.fecha, SlotCita.hora_inicio).all()
    
    return slots


@router.get("/{slot_id}", response_model=SlotCitaResponse)
async def obtener_slot(
    slot_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener slot específico"""
    
    slot = db.query(SlotCita).filter(SlotCita.id_slot == slot_id).first()
    
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot no encontrado"
        )
    
    return slot


@router.patch("/{slot_id}/reservar")
async def reservar_slot(
    slot_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Reservar un slot (incrementar contador)"""
    
    slot = db.query(SlotCita).filter(SlotCita.id_slot == slot_id).first()
    
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot no encontrado"
        )
    
    if slot.estado != 'disponible':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot no está disponible"
        )
    
    if slot.reservas_actuales >= slot.capacidad_maxima:
        slot.estado = 'lleno'
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot lleno"
        )
    
    slot.reservas_actuales += 1
    
    if slot.reservas_actuales >= slot.capacidad_maxima:
        slot.estado = 'lleno'
    
    db.commit()
    
    return {"mensaje": "Slot reservado", "reservas": slot.reservas_actuales}


@router.patch("/{slot_id}/liberar")
async def liberar_slot(
    slot_id: int,
    db: Session = Depends(get_db),
    admin = Depends(verificar_admin)
):
    """Liberar reserva de un slot (admin)"""
    
    slot = db.query(SlotCita).filter(SlotCita.id_slot == slot_id).first()
    
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot no encontrado"
        )
    
    if slot.reservas_actuales > 0:
        slot.reservas_actuales -= 1
    
    if slot.estado == 'lleno':
        slot.estado = 'disponible'
    
    db.commit()
    
    return {"mensaje": "Reserva liberada", "reservas": slot.reservas_actuales}


@router.patch("/{slot_id}/bloquear")
async def bloquear_slot(
    slot_id: int,
    db: Session = Depends(get_db),
    admin = Depends(verificar_admin)
):
    """Bloquear un slot (admin)"""
    
    slot = db.query(SlotCita).filter(SlotCita.id_slot == slot_id).first()
    
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot no encontrado"
        )
    
    slot.estado = 'bloqueado'
    slot.reservas_actuales = 0
    db.commit()
    
    return {"mensaje": "Slot bloqueado"}
