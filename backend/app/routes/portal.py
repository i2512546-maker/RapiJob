from datetime import datetime
import os
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from app.models.models import Usuario, PerfilTecnico, PerfilTecnicoPublico
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/tecnicos", tags=["técnicos"])


class PerfilPublicoInput(BaseModel):
    especialidad: str = Field(..., min_length=2, max_length=100)
    ciudad: str = Field(..., min_length=2, max_length=80)
    distrito: str = Field(..., min_length=2, max_length=100)
    latitud: Optional[float] = Field(None, ge=-90, le=90)
    longitud: Optional[float] = Field(None, ge=-180, le=180)
    tarifa_desde: Decimal = Field(..., ge=0, le=100000)
    experiencia_anios: int = Field(..., ge=0, le=60)
    descripcion_publica: Optional[str] = Field(None, max_length=1500)
    foto_url: Optional[str] = Field(None, max_length=500)
    disponible: bool = True


def serialize_profile(usuario, perfil):
    return {
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "telefono": usuario.telefono,
        "especialidad": perfil.especialidad,
        "ciudad": perfil.ciudad,
        "distrito": perfil.distrito,
        "latitud": float(perfil.latitud) if perfil.latitud is not None else None,
        "longitud": float(perfil.longitud) if perfil.longitud is not None else None,
        "tarifa_desde": float(perfil.tarifa_desde or 0),
        "experiencia_anios": perfil.experiencia_anios,
        "descripcion_publica": perfil.descripcion_publica or "",
        "foto_url": perfil.foto_url,
        "disponible": perfil.disponible,
        "aprobado": perfil.aprobado,
        "calificacion_promedio": float(usuario.perfil_tecnico.calificacion_promedio or 0) if usuario.perfil_tecnico else 0,
        "numero_trabajos_completados": usuario.perfil_tecnico.numero_trabajos_completados if usuario.perfil_tecnico else 0,
    }


@router.get("/")
def listar_tecnicos(ciudad: Optional[str] = None, especialidad: Optional[str] = None,
                    disponibles: bool = False, db: Session = Depends(get_db)):
    query = db.query(Usuario, PerfilTecnicoPublico).join(
        PerfilTecnicoPublico, PerfilTecnicoPublico.id_usuario == Usuario.id_usuario
    ).filter(Usuario.estado == "activo", PerfilTecnicoPublico.aprobado.is_(True))
    if ciudad:
        query = query.filter(PerfilTecnicoPublico.ciudad.ilike(ciudad.strip()))
    if especialidad:
        query = query.filter(PerfilTecnicoPublico.especialidad.ilike(especialidad.strip()))
    if disponibles:
        query = query.filter(PerfilTecnicoPublico.disponible.is_(True))
    return [serialize_profile(user, profile) for user, profile in query.order_by(
        PerfilTecnicoPublico.disponible.desc(), Usuario.nombre.asc()
    ).all()]


@router.get("/me")
def mi_perfil_tecnico(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.tipo_usuario != "tecnico":
        raise HTTPException(status_code=403, detail="Esta sección es solo para técnicos.")
    profile = db.query(PerfilTecnicoPublico).filter_by(id_usuario=current_user.user_id).first()
    if not profile:
        return None
    user = db.query(Usuario).filter_by(id_usuario=current_user.user_id).first()
    return serialize_profile(user, profile)


@router.put("/me")
def guardar_perfil_tecnico(data: PerfilPublicoInput, current_user=Depends(get_current_user),
                           db: Session = Depends(get_db)):
    if current_user.tipo_usuario != "tecnico":
        raise HTTPException(status_code=403, detail="Solo los técnicos pueden editar su perfil.")
    base = db.query(PerfilTecnico).filter_by(id_usuario=current_user.user_id).first()
    if not base:
        raise HTTPException(status_code=409, detail="No se encontró el perfil técnico base.")
    profile = db.query(PerfilTecnicoPublico).filter_by(id_usuario=current_user.user_id).first()
    values = data.model_dump()
    if profile is None:
        profile = PerfilTecnicoPublico(id_usuario=current_user.user_id, **values, aprobado=False)
        db.add(profile)
    else:
        for key, value in values.items():
            setattr(profile, key, value)
        # Cualquier cambio sustancial requiere nueva aprobación del administrador.
        profile.aprobado = False
    base.experiencia_años = data.experiencia_anios
    base.tarifa_base = data.tarifa_desde
    base.zona_servicio = f"{data.distrito}, {data.ciudad}"
    base.biografias = data.descripcion_publica
    base.disponible = data.disponible
    db.commit()
    db.refresh(profile)
    user = db.query(Usuario).filter_by(id_usuario=current_user.user_id).first()
    return serialize_profile(user, profile)


@router.get("/admin/pendientes")
def perfiles_pendientes(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    admin_email = os.getenv("RAPIJOB_ADMIN_EMAIL", "").strip().lower()
    if not admin_email or current_user.email.strip().lower() != admin_email:
        raise HTTPException(status_code=403, detail="Acceso reservado al administrador configurado.")
    query = db.query(Usuario, PerfilTecnicoPublico).join(
        PerfilTecnicoPublico, PerfilTecnicoPublico.id_usuario == Usuario.id_usuario
    ).filter(PerfilTecnicoPublico.aprobado.is_(False))
    return [serialize_profile(user, profile) for user, profile in query.all()]


@router.patch("/{tecnico_id}/aprobar")
def aprobar_tecnico(tecnico_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    admin_email = os.getenv("RAPIJOB_ADMIN_EMAIL", "").strip().lower()
    if not admin_email or current_user.email.strip().lower() != admin_email:
        raise HTTPException(status_code=403, detail="Acceso reservado al administrador configurado.")
    profile = db.query(PerfilTecnicoPublico).filter_by(id_usuario=tecnico_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil técnico no encontrado.")
    profile.aprobado = True
    db.commit()
    return {"message": "Perfil aprobado y publicado.", "id_usuario": tecnico_id}
