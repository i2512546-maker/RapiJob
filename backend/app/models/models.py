from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer,
    Numeric, String, Text
)
from sqlalchemy.orm import relationship

from database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    telefono = Column(String(20))
    tipo_usuario = Column(Enum("cliente", "tecnico"), nullable=False)
    documento_identidad = Column(String(20), unique=True)
    contraseña_hash = Column(String(255), nullable=False)
    fotografia_url = Column(String(255))
    estado = Column(Enum("activo", "inactivo", "suspendido"), default="activo")
    fecha_registro = Column(DateTime, default=datetime.utcnow)

    perfil_tecnico = relationship("PerfilTecnico", back_populates="usuario", uselist=False)


class PerfilTecnico(Base):
    __tablename__ = "perfiles_tecnicos"

    id_perfil = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), unique=True, nullable=False)
    experiencia_años = Column(Integer, default=0)
    calificacion_promedio = Column(Numeric(3, 2), default=0.00)
    numero_trabajos_completados = Column(Integer, default=0)
    biografias = Column(Text)
    tarifa_base = Column(Numeric(10, 2), nullable=False, default=0)
    disponible = Column(Boolean, default=True)
    zona_servicio = Column(String(255), default="Por definir")
    certificaciones = Column(Text)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="perfil_tecnico")


class CategoriaServicio(Base):
    __tablename__ = "categorias_servicios"

    id_categoria = Column(Integer, primary_key=True, index=True)
    nombre_categoria = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)
    icono_url = Column(String(255))
    estado = Column(Enum("activa", "inactiva"), default="activa")

    servicios = relationship("Servicio", back_populates="categoria")


class Servicio(Base):
    __tablename__ = "servicios"

    id_servicio = Column(Integer, primary_key=True, index=True)
    id_categoria = Column(Integer, ForeignKey("categorias_servicios.id_categoria"), nullable=False)
    nombre_servicio = Column(String(150), nullable=False)
    descripcion = Column(Text)
    duracion_estimada_minutos = Column(Integer)
    precio_base = Column(Numeric(10, 2), nullable=False)
    estado = Column(Enum("disponible", "no_disponible"), default="disponible")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    categoria = relationship("CategoriaServicio", back_populates="servicios")


class SlotCita(Base):
    __tablename__ = "slots_citas"
    __table_args__ = (
        Index("idx_slots_fecha", "fecha"),
        Index("idx_slots_estado", "estado"),
    )

    id_slot = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, nullable=False)
    hora_inicio = Column(DateTime, nullable=False)
    hora_fin = Column(DateTime, nullable=False)
    capacidad_maxima = Column(Integer, default=1, nullable=False)
    reservas_actuales = Column(Integer, default=0, nullable=False)
    estado = Column(Enum("disponible", "lleno", "bloqueado"), default="disponible")

    ordenes = relationship("OrdenTrabajo", back_populates="slot")


class OrdenTrabajo(Base):
    __tablename__ = "ordenes_trabajo"
    __table_args__ = (
        Index("idx_ordenes_cliente", "id_cliente"),
        Index("idx_ordenes_tecnico", "id_tecnico"),
        Index("idx_ordenes_estado", "estado_orden"),
    )

    id_orden = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    id_tecnico = Column(Integer, ForeignKey("perfiles_tecnicos.id_usuario", ondelete="SET NULL"))
    id_servicio = Column(Integer, ForeignKey("servicios.id_servicio"), nullable=False)
    id_slot_cita = Column(Integer, ForeignKey("slots_citas.id_slot"), nullable=True)

    fecha_solicitud = Column(DateTime, default=datetime.utcnow)
    fecha_programada = Column(DateTime, nullable=False)
    fecha_completada = Column(DateTime)

    ubicacion_servicio = Column(String(255), nullable=False)
    descripcion_problema = Column(Text, nullable=False)
    notas_adicionales = Column(Text)

    # Importe orientativo: no representa un cobro ni un pago realizado.
    precio_base = Column(Numeric(10, 2), nullable=True)
    precio_negociado = Column(Numeric(10, 2))
    precio_final = Column(Numeric(10, 2))

    estado_orden = Column(
        Enum("pendiente", "aceptada", "en_progreso", "completada", "cancelada"),
        default="pendiente",
    )
    razon_cancelacion = Column(String(255))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    slot = relationship("SlotCita", back_populates="ordenes")


class MetodoPago(Base):
    """Modelo legado; no se utiliza para cobrar dentro de RapiJob."""

    __tablename__ = "metodos_pago"

    id_metodo = Column(Integer, primary_key=True, index=True)
    nombre_metodo = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    estado = Column(Enum("activo", "inactivo"), default="activo")
    comision_porcentaje = Column(Numeric(5, 2), default=0.00)
    require_verificacion = Column(Boolean, default=False)


class Pago(Base):
    """Modelo reservado para una futura integración de pagos."""

    __tablename__ = "pagos"

    id_pago = Column(Integer, primary_key=True, index=True)
    id_orden = Column(Integer, ForeignKey("ordenes_trabajo.id_orden"), unique=True, nullable=False)
    id_metodo = Column(Integer, ForeignKey("metodos_pago.id_metodo"), nullable=True)
    monto = Column(Numeric(10, 2), nullable=False)
    comision = Column(Numeric(10, 2), default=0.00)
    monto_neto = Column(Numeric(10, 2))
    estado_pago = Column(Enum("pendiente", "procesando", "completado", "rechazado", "reembolsado"), default="pendiente")
    numero_transaccion = Column(String(100), unique=True)
    referencia_banco = Column(String(100))
    razon_rechazo = Column(String(255))
    fecha_pago = Column(DateTime)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ResenaCalificacion(Base):
    __tablename__ = "resenas_calificaciones"

    id_resena = Column(Integer, primary_key=True, index=True)
    id_orden = Column(Integer, ForeignKey("ordenes_trabajo.id_orden"), unique=True, nullable=False)
    id_cliente = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_tecnico = Column(Integer, ForeignKey("perfiles_tecnicos.id_usuario"), nullable=False)
    calificacion_servicio = Column(Integer)
    calificacion_tecnico = Column(Integer)
    comentario = Column(Text)
    fecha_resena = Column(DateTime, default=datetime.utcnow)
    respuesta_tecnico = Column(Text)
    fecha_respuesta = Column(DateTime)


class PerfilTecnicoPublico(Base):
    """Datos públicos y ubicación declarada por cada técnico registrado."""

    __tablename__ = "perfiles_tecnicos_publicos"

    id_perfil_publico = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    especialidad = Column(String(100), nullable=False)
    ciudad = Column(String(80), nullable=False)
    distrito = Column(String(100), nullable=False)
    latitud = Column(Numeric(10, 7))
    longitud = Column(Numeric(10, 7))
    tarifa_desde = Column(Numeric(10, 2), nullable=False, default=0)
    experiencia_anios = Column(Integer, nullable=False, default=0)
    descripcion_publica = Column(Text)
    foto_url = Column(String(500))
    disponible = Column(Boolean, nullable=False, default=True)
    aprobado = Column(Boolean, nullable=False, default=False)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UbicacionOrden(Base):
    __tablename__ = "ubicaciones_ordenes"

    id_ubicacion = Column(Integer, primary_key=True, index=True)
    id_orden = Column(Integer, ForeignKey("ordenes_trabajo.id_orden", ondelete="CASCADE"), unique=True, nullable=False)
    latitud = Column(Numeric(10, 7), nullable=False)
    longitud = Column(Numeric(10, 7), nullable=False)
    direccion_formateada = Column(String(500))
    fecha_registro = Column(DateTime, default=datetime.utcnow)


class AdjuntoOrden(Base):
    __tablename__ = "adjuntos_ordenes"

    id_adjunto = Column(Integer, primary_key=True, index=True)
    id_orden = Column(Integer, ForeignKey("ordenes_trabajo.id_orden", ondelete="CASCADE"), nullable=False, index=True)
    nombre_archivo = Column(String(255), nullable=False)
    tipo_contenido = Column(String(100), nullable=False)
    contenido_base64 = Column(Text, nullable=False)
    fecha_subida = Column(DateTime, default=datetime.utcnow)


class SlotTecnico(Base):
    __tablename__ = "slots_tecnicos"

    id_asignacion = Column(Integer, primary_key=True, index=True)
    id_slot = Column(Integer, ForeignKey("slots_citas.id_slot", ondelete="CASCADE"), unique=True, nullable=False)
    id_tecnico = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False, index=True)
