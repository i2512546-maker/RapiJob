from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, Boolean, Text, Numeric, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Usuario(Base):
    """Modelo de usuario (cliente o técnico)"""
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    telefono = Column(String(20))
    tipo_usuario = Column(Enum('cliente', 'tecnico'), nullable=False)
    documento_identidad = Column(String(20), unique=True)
    contraseña_hash = Column(String(255), nullable=False)
    fotografia_url = Column(String(255))
    estado = Column(Enum('activo', 'inactivo', 'suspendido'), default='activo')
    fecha_registro = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    perfil_tecnico = relationship("PerfilTecnico", back_populates="usuario", uselist=False)


class PerfilTecnico(Base):
    """Modelo de perfil técnico"""
    __tablename__ = "perfiles_tecnicos"

    id_perfil = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, unique=True, nullable=False)
    experiencia_años = Column(Integer)
    calificacion_promedio = Column(Numeric(3, 2), default=0.00)
    numero_trabajos_completados = Column(Integer, default=0)
    biografias = Column(Text)
    tarifa_base = Column(Numeric(10, 2), nullable=False)
    disponible = Column(Boolean, default=True)
    zona_servicio = Column(String(255))
    certificaciones = Column(Text)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    usuario = relationship("Usuario", back_populates="perfil_tecnico")


class CategoriaServicio(Base):
    """Modelo de categoría de servicios"""
    __tablename__ = "categorias_servicios"

    id_categoria = Column(Integer, primary_key=True, index=True)
    nombre_categoria = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)
    icono_url = Column(String(255))
    estado = Column(Enum('activa', 'inactiva'), default='activa')

    # Relaciones
    servicios = relationship("Servicio", back_populates="categoria")


class Servicio(Base):
    """Modelo de servicio"""
    __tablename__ = "servicios"

    id_servicio = Column(Integer, primary_key=True, index=True)
    id_categoria = Column(Integer, nullable=False)
    nombre_servicio = Column(String(150), nullable=False)
    descripcion = Column(Text)
    duracion_estimada_minutos = Column(Integer)
    precio_base = Column(Numeric(10, 2), nullable=False)
    estado = Column(Enum('disponible', 'no_disponible'), default='disponible')
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    categoria = relationship("CategoriaServicio", back_populates="servicios")


class MetodoPago(Base):
    """Modelo de método de pago (administrador)"""
    __tablename__ = "metodos_pago"

    id_metodo = Column(Integer, primary_key=True, index=True)
    nombre_metodo = Column(String(50), unique=True, nullable=False)
    estado = Column(Enum('activo', 'inactivo'), default='activo')
    comision_porcentaje = Column(Numeric(5, 2), default=0.00)

    # Relaciones
    pagos = relationship("Pago", back_populates="metodo")


class SlotCita(Base):
    """Modelo de slots de citas disponibles (administrador)"""
    __tablename__ = "slots_citas"
    __table_args__ = (
        Index('idx_fecha', 'fecha'),
        Index('idx_estado', 'estado'),
    )

    id_slot = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, nullable=False)
    hora_inicio = Column(DateTime, nullable=False)
    hora_fin = Column(DateTime, nullable=False)
    capacidad_maxima = Column(Integer, default=1)
    reservas_actuales = Column(Integer, default=0)
    estado = Column(Enum('disponible', 'lleno', 'bloqueado'), default='disponible')

    # Relaciones
    ordenes = relationship("OrdenTrabajo", back_populates="slot")


class OrdenTrabajo(Base):
    """Modelo de orden de trabajo"""
    __tablename__ = "ordenes_trabajo"
    __table_args__ = (
        Index('idx_cliente', 'id_cliente'),
        Index('idx_tecnico', 'id_tecnico'),
        Index('idx_estado', 'estado_orden'),
    )

    id_orden = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, nullable=False)
    id_tecnico = Column(Integer)
    id_servicio = Column(Integer, nullable=False)
    id_slot_cita = Column(Integer, nullable=False)  # Referencia a slot disponible
    id_metodo_pago = Column(Integer)  # Referencia a tabla de métodos
    
    fecha_solicitud = Column(DateTime, default=datetime.utcnow)
    fecha_completada = Column(DateTime)
    
    ubicacion_servicio = Column(String(255), nullable=False)
    descripcion_problema = Column(String(1000), nullable=False)  # Máx 1000 caracteres
    notas_adicionales = Column(String(500))  # Máx 500 caracteres
    
    # Precios
    precio_base = Column(Numeric(10, 2), nullable=False)  # Del servicio
    precio_negociado = Column(Numeric(10, 2))  # NULL = usa base, si tiene valor = precio final
    precio_final = Column(Numeric(10, 2))  # Calculado automáticamente
    
    # Estado
    estado_orden = Column(Enum('pendiente', 'aceptada', 'en_progreso', 'completada', 'cancelada'), default='pendiente')
    razon_cancelacion = Column(String(255))
    
    # Pago
    estado_pago = Column(Enum('pendiente', 'procesando', 'completado', 'rechazado'), default='pendiente')
    fecha_pago = Column(DateTime)
    referencia_transaccion = Column(String(100))
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    slot = relationship("SlotCita", back_populates="ordenes")
    metodo = relationship("MetodoPago", back_populates="pagos")


class Pago(Base):
    """Modelo de pago (registro de transacciones)"""
    __tablename__ = "pagos"
    __table_args__ = (
        Index('idx_estado', 'estado_pago'),
        Index('idx_fecha', 'fecha_pago'),
    )

    id_pago = Column(Integer, primary_key=True, index=True)
    id_orden = Column(Integer, unique=True, nullable=False)
    id_metodo = Column(Integer, nullable=False)  # Referencia a métodos_pago
    
    monto = Column(Numeric(10, 2), nullable=False)
    comision = Column(Numeric(10, 2), default=0.00)
    monto_neto = Column(Numeric(10, 2))  # monto - comision
    
    estado_pago = Column(Enum('pendiente', 'procesando', 'completado', 'rechazado', 'reembolsado'), default='pendiente')
    numero_transaccion = Column(String(100), unique=True)
    referencia_banco = Column(String(100))
    razon_rechazo = Column(String(255))
    
    fecha_pago = Column(DateTime)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    metodo = relationship("MetodoPago", back_populates="pagos")


class ResenaCalificacion(Base):
    """Modelo de reseña y calificación"""
    __tablename__ = "resenas_calificaciones"

    id_resena = Column(Integer, primary_key=True, index=True)
    id_orden = Column(Integer, unique=True, nullable=False)
    id_cliente = Column(Integer, nullable=False)
    id_tecnico = Column(Integer, nullable=False)
    calificacion_servicio = Column(Integer)  # 1-5
    calificacion_tecnico = Column(Integer)  # 1-5
    comentario = Column(Text)
    fecha_resena = Column(DateTime, default=datetime.utcnow)
    respuesta_tecnico = Column(Text)
    fecha_respuesta = Column(DateTime)
