from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from app.models.models import MetodoPago
from app.schemas.schemas import MetodoPagoCreate, MetodoPagoResponse
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/admin/metodos-pago", tags=["admin"])


async def verificar_admin(current_user = Depends(get_current_user)):
    """Verificar que sea administrador"""
    # TODO: Implementar rol de admin
    return current_user


@router.post("/", response_model=MetodoPagoResponse, status_code=status.HTTP_201_CREATED)
async def crear_metodo_pago(
    metodo: MetodoPagoCreate,
    db: Session = Depends(get_db),
    admin = Depends(verificar_admin)
):
    """Crear nuevo método de pago (admin)"""
    
    # Validar que no exista
    existente = db.query(MetodoPago).filter(
        MetodoPago.nombre_metodo == metodo.nombre_metodo
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El método de pago ya existe"
        )
    
    nuevo_metodo = MetodoPago(
        nombre_metodo=metodo.nombre_metodo,
        descripcion=metodo.descripcion,
        comision_porcentaje=metodo.comision_porcentaje,
        require_verificacion=metodo.require_verificacion,
        estado='activo'
    )
    
    db.add(nuevo_metodo)
    db.commit()
    db.refresh(nuevo_metodo)
    
    return nuevo_metodo


@router.get("/", response_model=list[MetodoPagoResponse])
async def obtener_metodos_pago(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener métodos de pago disponibles"""
    metodos = db.query(MetodoPago).filter(
        MetodoPago.estado == 'activo'
    ).all()
    return metodos


@router.get("/{metodo_id}", response_model=MetodoPagoResponse)
async def obtener_metodo_pago(
    metodo_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener método de pago específico"""
    metodo = db.query(MetodoPago).filter(
        MetodoPago.id_metodo == metodo_id,
        MetodoPago.estado == 'activo'
    ).first()
    
    if not metodo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Método de pago no encontrado"
        )
    
    return metodo


@router.patch("/{metodo_id}/desactivar")
async def desactivar_metodo_pago(
    metodo_id: int,
    db: Session = Depends(get_db),
    admin = Depends(verificar_admin)
):
    """Desactivar método de pago (admin)"""
    
    metodo = db.query(MetodoPago).filter(MetodoPago.id_metodo == metodo_id).first()
    
    if not metodo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Método de pago no encontrado"
        )
    
    metodo.estado = 'inactivo'
    db.commit()
    
    return {"mensaje": "Método de pago desactivado"}
