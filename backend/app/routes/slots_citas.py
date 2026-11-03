from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from app.models.models import SlotCita, SlotTecnico
from app.schemas.schemas import SlotCitaCreate, SlotCitaResponse
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/admin/slots-citas", tags=["horarios"])


def verificar_admin(current_user=Depends(get_current_user)):
    # No existe rol administrador en el registro público. Solo técnicos pueden
    # gestionar disponibilidad en esta versión.
    if current_user.tipo_usuario != "tecnico":
        raise HTTPException(status_code=403, detail="Solo un técnico puede gestionar horarios.")
    return current_user


@router.post("/", response_model=SlotCitaResponse, status_code=status.HTTP_201_CREATED)
def crear_slot_cita(slot: SlotCitaCreate, db: Session = Depends(get_db), tecnico=Depends(verificar_admin)):
    if slot.hora_inicio >= slot.hora_fin:
        raise HTTPException(status_code=400, detail="La hora de inicio debe ser anterior a la hora de fin.")
    if slot.hora_inicio <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="El horario debe ser futuro.")
    conflicto = db.query(SlotCita).join(SlotTecnico, SlotTecnico.id_slot == SlotCita.id_slot).filter(
        SlotTecnico.id_tecnico == tecnico.user_id,
        SlotCita.hora_inicio < slot.hora_fin,
        SlotCita.hora_fin > slot.hora_inicio,
        SlotCita.estado != "bloqueado",
    ).first()
    if conflicto:
        raise HTTPException(status_code=409, detail="Ese horario se cruza con otro horario disponible.")
    nuevo = SlotCita(
        fecha=slot.fecha, hora_inicio=slot.hora_inicio, hora_fin=slot.hora_fin,
        capacidad_maxima=slot.capacidad_maxima, reservas_actuales=0, estado="disponible",
    )
    db.add(nuevo)
    db.flush()
    db.add(SlotTecnico(id_slot=nuevo.id_slot, id_tecnico=tecnico.user_id))
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.get("/", response_model=list[SlotCitaResponse])
def obtener_slots_disponibles(fecha_desde: datetime | None = None, fecha_hasta: datetime | None = None, id_tecnico: int | None = None, db: Session = Depends(get_db)):
    query = db.query(SlotCita).filter(
        SlotCita.estado == "disponible",
        SlotCita.reservas_actuales < SlotCita.capacidad_maxima,
        SlotCita.hora_inicio > datetime.utcnow(),
    )
    if id_tecnico is not None:
        query = query.join(SlotTecnico, SlotTecnico.id_slot == SlotCita.id_slot).filter(SlotTecnico.id_tecnico == id_tecnico)
    if fecha_desde:
        query = query.filter(SlotCita.hora_inicio >= fecha_desde)
    if fecha_hasta:
        query = query.filter(SlotCita.hora_inicio <= fecha_hasta)
    return query.order_by(SlotCita.hora_inicio).all()


@router.get("/{slot_id}", response_model=SlotCitaResponse)
def obtener_slot(slot_id: int, db: Session = Depends(get_db)):
    slot = db.query(SlotCita).filter(SlotCita.id_slot == slot_id, SlotCita.estado == "disponible").first()
    if not slot:
        raise HTTPException(status_code=404, detail="Horario no encontrado.")
    return slot


@router.patch("/{slot_id}/bloquear")
def bloquear_slot(slot_id: int, db: Session = Depends(get_db), tecnico=Depends(verificar_admin)):
    slot = db.query(SlotCita).filter(SlotCita.id_slot == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Horario no encontrado.")
    if slot.reservas_actuales:
        raise HTTPException(status_code=409, detail="No se puede bloquear un horario que ya tiene reservas.")
    slot.estado = "bloqueado"
    db.commit()
    return {"mensaje": "Horario bloqueado."}
