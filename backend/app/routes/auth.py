from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from database import get_db
from app.models.models import Usuario
from app.schemas.schemas import UsuarioRegistro, UsuarioLogin, UsuarioResponse, Token
from app.middleware.auth import (
    hash_password, verify_password, create_access_token, 
    get_current_user
)
from config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post("/registro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def registro(usuario: UsuarioRegistro, db: Session = Depends(get_db)):
    """Registrar nuevo usuario"""
    
    # Validar que el email no exista
    user_existente = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if user_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Validar tipo de usuario
    if usuario.tipo_usuario not in ['cliente', 'tecnico']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de usuario inválido"
        )
    
    # Crear usuario
    nuevo_usuario = Usuario(
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        telefono=usuario.telefono,
        tipo_usuario=usuario.tipo_usuario,
        documento_identidad=usuario.documento_identidad,
        contraseña_hash=hash_password(usuario.contraseña),
        estado='activo'
    )
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    return nuevo_usuario


@router.post("/login", response_model=Token)
async def login(credenciales: UsuarioLogin, db: Session = Depends(get_db)):
    """Login de usuario"""
    
    # Buscar usuario por email
    usuario = db.query(Usuario).filter(Usuario.email == credenciales.email).first()
    
    if not usuario or not verify_password(credenciales.contraseña, usuario.contraseña_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    if usuario.estado != 'activo':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario no activo"
        )
    
    # Crear token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": usuario.id_usuario,
            "email": usuario.email,
            "tipo_usuario": usuario.tipo_usuario
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": usuario.id_usuario,
        "tipo_usuario": usuario.tipo_usuario
    }


@router.get("/me", response_model=UsuarioResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener información del usuario actual"""
    usuario = db.query(Usuario).filter(Usuario.id_usuario == current_user.user_id).first()
    
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    return usuario
