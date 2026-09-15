from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# ==================== USUARIO ====================
class UsuarioRegistro(BaseModel):
    """Schema para registro de usuario"""
    nombre: str
    apellido: str
    email: EmailStr
    telefono: Optional[str] = None
    tipo_usuario: str  # 'cliente' o 'tecnico'
    documento_identidad: Optional[str] = None
    contraseña: str


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
    experiencia_años: int
    tarifa_base: float
    zona_servicio: str
    biografias: Optional[str] = None
    certificaciones: Optional[str] = None


class PerfilTecnicoResponse(BaseModel):
    """Schema de respuesta de perfil técnico"""
    id_perfil: int
    experiencia_años: int
    calificacion_promedio: float
    numero_trabajos_completados: int
    tarifa_base: float
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
    precio_base: float
    duracion_estimada_minutos: int
    estado: str

    class Config:
        from_attributes = True


# ==================== ORDEN DE TRABAJO ====================
class OrdenTrabajoCreate(BaseModel):
    """Schema para crear orden de trabajo"""
    id_servicio: int
    fecha_programada: datetime
    ubicacion_servicio: str
    descripcion_problema: str
    notas_adicionales: Optional[str] = None


class OrdenTrabajoResponse(BaseModel):
    """Schema de respuesta de orden de trabajo"""
    id_orden: int
    id_cliente: int
    id_tecnico: Optional[int]
    id_servicio: int
    fecha_programada: datetime
    ubicacion_servicio: str
    estado_orden: str
    precio_final: Optional[float]

    class Config:
        from_attributes = True


# ==================== RESEÑA ====================
class ResenaCreate(BaseModel):
    """Schema para crear reseña"""
    calificacion_servicio: int  # 1-5
    calificacion_tecnico: int  # 1-5
    comentario: Optional[str] = None


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
