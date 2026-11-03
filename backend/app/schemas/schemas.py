from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class MetodoPagoCreate(BaseModel):
    nombre_metodo: str = Field(..., min_length=3, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=255)
    comision_porcentaje: Decimal = Field(default=0.00, ge=0, le=100)
    require_verificacion: bool = False


class MetodoPagoResponse(BaseModel):
    id_metodo: int
    nombre_metodo: str
    descripcion: Optional[str] = None
    estado: str
    comision_porcentaje: Decimal

    class Config:
        from_attributes = True


class SlotCitaCreate(BaseModel):
    fecha: datetime
    hora_inicio: datetime
    hora_fin: datetime
    capacidad_maxima: int = Field(default=1, ge=1, le=20)


class SlotCitaResponse(BaseModel):
    id_slot: int
    fecha: datetime
    hora_inicio: datetime
    hora_fin: datetime
    capacidad_maxima: int
    reservas_actuales: int
    estado: str

    class Config:
        from_attributes = True


class OrdenTrabajoCreate(BaseModel):
    id_servicio: int
    id_tecnico: Optional[int] = None
    latitud: Optional[float] = Field(None, ge=-90, le=90)
    longitud: Optional[float] = Field(None, ge=-180, le=180)
    id_slot_cita: int
    ubicacion_servicio: str = Field(..., min_length=5, max_length=255)
    descripcion_problema: str = Field(..., min_length=10, max_length=1000)
    notas_adicionales: Optional[str] = Field(None, max_length=500)


class OrdenTrabajoResponse(BaseModel):
    id_orden: int
    id_cliente: int
    id_tecnico: Optional[int] = None
    id_servicio: int
    id_slot_cita: Optional[int] = None
    fecha_solicitud: datetime
    fecha_programada: datetime
    ubicacion_servicio: str
    descripcion_problema: str
    notas_adicionales: Optional[str] = None
    precio_base: Optional[Decimal] = None
    precio_negociado: Optional[Decimal] = None
    precio_final: Optional[Decimal] = None
    estado_orden: str
    razon_cancelacion: Optional[str] = None

    class Config:
        from_attributes = True


class UsuarioRegistro(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefono: Optional[str] = Field(None, max_length=20)
    tipo_usuario: str
    documento_identidad: Optional[str] = Field(None, max_length=20)
    contraseña: str = Field(..., min_length=8, max_length=100)


class UsuarioLogin(BaseModel):
    email: EmailStr
    contraseña: str


class UsuarioResponse(BaseModel):
    id_usuario: int
    nombre: str
    apellido: str
    email: str
    telefono: Optional[str] = None
    tipo_usuario: str
    estado: str

    class Config:
        from_attributes = True


class PerfilTecnicoCreate(BaseModel):
    experiencia_años: int = Field(..., ge=0, le=50)
    tarifa_base: Decimal = Field(..., gt=0)
    zona_servicio: str = Field(..., min_length=5, max_length=255)
    biografias: Optional[str] = Field(None, max_length=1000)
    certificaciones: Optional[str] = Field(None, max_length=500)


class PerfilTecnicoResponse(BaseModel):
    id_perfil: int
    experiencia_años: int
    calificacion_promedio: Decimal
    numero_trabajos_completados: int
    tarifa_base: Decimal
    disponible: bool
    zona_servicio: str

    class Config:
        from_attributes = True


class ServicioResponse(BaseModel):
    id_servicio: int
    nombre_servicio: str
    descripcion: Optional[str] = None
    precio_base: Decimal
    duracion_estimada_minutos: Optional[int] = None
    estado: str

    class Config:
        from_attributes = True


class ResenaCreate(BaseModel):
    calificacion_servicio: int = Field(..., ge=1, le=5)
    calificacion_tecnico: int = Field(..., ge=1, le=5)
    comentario: Optional[str] = Field(None, max_length=500)


class ResenaResponse(BaseModel):
    id_resena: int
    calificacion_servicio: int
    calificacion_tecnico: int
    comentario: Optional[str] = None
    fecha_resena: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    tipo_usuario: str


class TokenData(BaseModel):
    user_id: int
    email: str
    tipo_usuario: str
