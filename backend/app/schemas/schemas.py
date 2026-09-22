from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal


# ==================== MÉTODO DE PAGO ====================
class MetodoPagoCreate(BaseModel):
    """Schema para crear método de pago"""
    nombre_metodo: str = Field(..., min_length=3, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=255)
    comision_porcentaje: Decimal = Field(default=0.00, ge=0, le=100)
    require_verificacion: bool = False


class MetodoPagoResponse(BaseModel):
    """Schema de respuesta de método de pago"""
    id_metodo: int
    nombre_metodo: str
    descripcion: Optional[str]
    estado: str
    comision_porcentaje: Decimal

    class Config:
        from_attributes = True


# ==================== SLOT DE CITA ====================
class SlotCitaCreate(BaseModel):
    """Schema para crear slot de cita"""
    fecha: datetime
    hora_inicio: datetime
    hora_fin: datetime
    capacidad_maxima: int = Field(default=1, ge=1)


class SlotCitaResponse(BaseModel):
    """Schema de respuesta de slot"""
    id_slot: int
    fecha: datetime
    hora_inicio: datetime
    hora_fin: datetime
    capacidad_maxima: int
    reservas_actuales: int
    estado: str

    class Config:
        from_attributes = True


# ==================== ORDEN DE TRABAJO ====================
class OrdenTrabajoCreate(BaseModel):
    """Schema para crear orden de trabajo"""
    id_servicio: int
    id_slot_cita: int  # Reservar slot disponible
    id_metodo_pago: int  # Seleccionar método de pago
    
    ubicacion_servicio: str = Field(..., min_length=5, max_length=255)
    descripcion_problema: str = Field(..., min_length=10, max_length=1000)
    notas_adicionales: Optional[str] = Field(None, max_length=500)
    
    precio_negociado: Optional[Decimal] = Field(None, gt=0)  # Opcional, negociable


class OrdenTrabajoUpdate(BaseModel):
    """Schema para actualizar precio negociado"""
    precio_negociado: Decimal = Field(..., gt=0)


class OrdenTrabajoResponse(BaseModel):
    """Schema de respuesta de orden de trabajo"""
    id_orden: int
    id_cliente: int
    id_tecnico: Optional[int]
    id_servicio: int
    id_slot_cita: int
    id_metodo_pago: int
    
    ubicacion_servicio: str
    descripcion_problema: str
    notas_adicionales: Optional[str]
    
    precio_base: Decimal
    precio_negociado: Optional[Decimal]
    precio_final: Decimal
    
    estado_orden: str
    estado_pago: str
    fecha_solicitud: datetime

    class Config:
        from_attributes = True


# ==================== PAGO ====================
class PagoCreate(BaseModel):
    """Schema para procesar pago"""
    id_orden: int
    id_metodo: int
    numero_transaccion: Optional[str] = None


class PagoResponse(BaseModel):
    """Schema de respuesta de pago"""
    id_pago: int
    id_orden: int
    monto: Decimal
    comision: Decimal
    monto_neto: Decimal
    estado_pago: str
    fecha_pago: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== USUARIO ====================
class UsuarioRegistro(BaseModel):
    """Schema para registro de usuario"""
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefono: Optional[str] = Field(None, max_length=20)
    tipo_usuario: str  # 'cliente' o 'tecnico'
    documento_identidad: Optional[str] = Field(None, max_length=20)
    contraseña: str = Field(..., min_length=8, max_length=100)


class UsuarioLogin(BaseModel):
    """Schema para login"""
    email: EmailStr
    contraseña: str


class UsuarioResponse(BaseModel):
    """Schema de respuesta de usuario"""
    id_usuario: int
    nombre: str
    apellido: str
    email: str
    tipo_usuario: str
    estado: str

    class Config:
        from_attributes = True


# ==================== PERFIL TÉCNICO ====================
class PerfilTecnicoCreate(BaseModel):
    """Schema para crear perfil técnico"""
    experiencia_años: int = Field(..., ge=0, le=50)
    tarifa_base: Decimal = Field(..., gt=0)
    zona_servicio: str = Field(..., min_length=5, max_length=255)
    biografias: Optional[str] = Field(None, max_length=1000)
    certificaciones: Optional[str] = Field(None, max_length=500)


class PerfilTecnicoResponse(BaseModel):
    """Schema de respuesta de perfil técnico"""
    id_perfil: int
    experiencia_años: int
    calificacion_promedio: Decimal
    numero_trabajos_completados: int
    tarifa_base: Decimal
    disponible: bool
    zona_servicio: str

    class Config:
        from_attributes = True


# ==================== SERVICIO ====================
class ServicioResponse(BaseModel):
    """Schema de respuesta de servicio"""
    id_servicio: int
    nombre_servicio: str
    descripcion: Optional[str]
    precio_base: Decimal
    duracion_estimada_minutos: int
    estado: str

    class Config:
        from_attributes = True


# ==================== RESEÑA ====================
class ResenaCreate(BaseModel):
    """Schema para crear reseña"""
    calificacion_servicio: int = Field(..., ge=1, le=5)
    calificacion_tecnico: int = Field(..., ge=1, le=5)
    comentario: Optional[str] = Field(None, max_length=500)


class ResenaResponse(BaseModel):
    """Schema de respuesta de reseña"""
    id_resena: int
    calificacion_servicio: int
    calificacion_tecnico: int
    comentario: Optional[str]
    fecha_resena: datetime

    class Config:
        from_attributes = True


# ==================== TOKEN ====================
class Token(BaseModel):
    """Schema de token JWT"""
    access_token: str
    token_type: str
    user_id: int
    tipo_usuario: str


class TokenData(BaseModel):
    """Schema de datos en token"""
    user_id: int
    email: str
    tipo_usuario: str