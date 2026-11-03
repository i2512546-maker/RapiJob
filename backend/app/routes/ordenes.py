from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from app.models.models import OrdenTrabajo, Servicio, SlotCita, PerfilTecnico, PerfilTecnicoPublico
from app.schemas.schemas import OrdenTrabajoCreate, OrdenTrabajoResponse
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/ordenes", tags=["solicitudes"])


@router.post("/", response_model=OrdenTrabajoResponse, status_code=status.HTTP_201_CREATED)
def crear_orden(orden: OrdenTrabajoCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.tipo_usuario != "cliente":
        raise HTTPException(status_code=403, detail="Solo los clientes pueden solicitar un servicio.")

    servicio = db.query(Servicio).filter(
        Servicio.id_servicio == orden.id_servicio,
        Servicio.estado == "disponible",
    ).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="El servicio seleccionado ya no está disponible.")

    slot = db.query(SlotCita).filter(SlotCita.id_slot == orden.id_slot_cita).with_for_update().first()
    if not slot or slot.estado != "disponible" or slot.hora_inicio <= datetime.utcnow():
        raise HTTPException(status_code=409, detail="El horario seleccionado ya no está disponible.")
    if slot.reservas_actuales >= slot.capacidad_maxima:
        slot.estado = "lleno"
        db.commit()
        raise HTTPException(status_code=409, detail="El horario acaba de completarse. Selecciona otro.")

    tecnico_id = None
    if orden.id_tecnico is not None:
        perfil_publico = db.query(PerfilTecnicoPublico).filter(
            PerfilTecnicoPublico.id_usuario == orden.id_tecnico,
            PerfilTecnicoPublico.aprobado.is_(True),
            PerfilTecnicoPublico.disponible.is_(True),
        ).first()
        if not perfil_publico:
            raise HTTPException(status_code=409, detail="El técnico seleccionado no está disponible para recibir solicitudes.")
        tecnico_id = perfil_publico.id_usuario

    nueva = OrdenTrabajo(
        id_cliente=current_user.user_id,
        id_tecnico=tecnico_id,
        id_servicio=servicio.id_servicio,
        id_slot_cita=slot.id_slot,
        fecha_programada=slot.hora_inicio,
        ubicacion_servicio=orden.ubicacion_servicio.strip(),
        descripcion_problema=orden.descripcion_problema.strip(),
        notas_adicionales=(orden.notas_adicionales or "").strip() or None,
        precio_base=Decimal(str(servicio.precio_base)),
        precio_final=Decimal(str(servicio.precio_base)),
        estado_orden="pendiente",
    )
    slot.reservas_actuales += 1
    if slot.reservas_actuales >= slot.capacidad_maxima:
        slot.estado = "lleno"
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.get("/", response_model=list[OrdenTrabajoResponse])
def obtener_ordenes(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.tipo_usuario == "cliente":
        return db.query(OrdenTrabajo).filter(
            OrdenTrabajo.id_cliente == current_user.user_id
        ).order_by(OrdenTrabajo.fecha_solicitud.desc()).all()

    return db.query(OrdenTrabajo).filter(
        (OrdenTrabajo.id_tecnico == current_user.user_id) |
        ((OrdenTrabajo.id_tecnico.is_(None)) & (OrdenTrabajo.estado_orden == "pendiente"))
    ).order_by(OrdenTrabajo.fecha_solicitud.desc()).all()


@router.get("/{orden_id}", response_model=OrdenTrabajoResponse)
def obtener_orden(orden_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    orden = db.query(OrdenTrabajo).filter(OrdenTrabajo.id_orden == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    if current_user.tipo_usuario == "cliente" and orden.id_cliente != current_user.user_id:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta solicitud.")
    if current_user.tipo_usuario == "tecnico" and orden.id_tecnico not in (None, current_user.user_id):
        raise HTTPException(status_code=403, detail="Esta solicitud pertenece a otro técnico.")
    return orden


@router.patch("/{orden_id}/aceptar", response_model=OrdenTrabajoResponse)
def aceptar_orden(orden_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.tipo_usuario != "tecnico":
        raise HTTPException(status_code=403, detail="Solo los técnicos pueden aceptar solicitudes.")
    perfil = db.query(PerfilTecnico).filter(PerfilTecnico.id_usuario == current_user.user_id).first()
    if not perfil:
        raise HTTPException(status_code=409, detail="Completa tu perfil técnico antes de aceptar solicitudes.")
    orden = db.query(OrdenTrabajo).filter(OrdenTrabajo.id_orden == orden_id).with_for_update().first()
    if not orden:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    if orden.estado_orden != "pendiente" or orden.id_tecnico is not None:
        raise HTTPException(status_code=409, detail="Esta solicitud ya fue tomada o no está disponible.")
    orden.id_tecnico = current_user.user_id
    orden.estado_orden = "aceptada"
    db.commit()
    db.refresh(orden)
    return orden


@router.patch("/{orden_id}/cancelar", response_model=OrdenTrabajoResponse)
def cancelar_orden(orden_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    orden = db.query(OrdenTrabajo).filter(OrdenTrabajo.id_orden == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    autorizado = (
        current_user.tipo_usuario == "cliente" and orden.id_cliente == current_user.user_id
    ) or (
        current_user.tipo_usuario == "tecnico" and orden.id_tecnico == current_user.user_id
    )
    if not autorizado:
        raise HTTPException(status_code=403, detail="No tienes permiso para cancelar esta solicitud.")
    if orden.estado_orden not in ("pendiente", "aceptada"):
        raise HTTPException(status_code=409, detail="Esta solicitud ya no se puede cancelar.")
    if orden.id_slot_cita:
        slot = db.query(SlotCita).filter(SlotCita.id_slot == orden.id_slot_cita).first()
        if slot and slot.reservas_actuales > 0:
            slot.reservas_actuales -= 1
            if slot.estado == "lleno":
                slot.estado = "disponible"
    orden.estado_orden = "cancelada"
    db.commit()
    db.refresh(orden)
    return orden
