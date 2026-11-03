from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db
from app.models.models import Usuario, PerfilTecnico
from app.schemas.schemas import UsuarioRegistro, UsuarioLogin, UsuarioResponse, Token
from app.middleware.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post("/registro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registro(usuario: UsuarioRegistro, db: Session = Depends(get_db)):
    if usuario.tipo_usuario not in ("cliente", "tecnico"):
        raise HTTPException(status_code=400, detail="Selecciona cliente o técnico.")

    email = str(usuario.email).strip().lower()
    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(status_code=409, detail="Este correo ya está registrado.")

    if usuario.documento_identidad and db.query(Usuario).filter(
        Usuario.documento_identidad == usuario.documento_identidad
    ).first():
        raise HTTPException(status_code=409, detail="El documento ya está registrado.")

    nuevo = Usuario(
        nombre=usuario.nombre.strip(),
        apellido=usuario.apellido.strip(),
        email=email,
        telefono=(usuario.telefono or "").strip() or None,
        tipo_usuario=usuario.tipo_usuario,
        documento_identidad=(usuario.documento_identidad or "").strip() or None,
        contraseña_hash=hash_password(usuario.contraseña),
        estado="activo",
    )
    db.add(nuevo)
    db.flush()

    # Todo técnico necesita un perfil para poder recibir y aceptar solicitudes.
    if nuevo.tipo_usuario == "tecnico":
        db.add(PerfilTecnico(
            id_usuario=nuevo.id_usuario,
            experiencia_años=0,
            tarifa_base=0,
            zona_servicio="Por definir",
            disponible=True,
        ))

    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.post("/login", response_model=Token)
def login(credenciales: UsuarioLogin, db: Session = Depends(get_db)):
    email = str(credenciales.email).strip().lower()
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario or not verify_password(credenciales.contraseña, usuario.contraseña_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
    if usuario.estado != "activo":
        raise HTTPException(status_code=403, detail="La cuenta no está activa.")

    token = create_access_token(
        data={"sub": str(usuario.id_usuario), "email": usuario.email, "tipo_usuario": usuario.tipo_usuario},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer", "user_id": usuario.id_usuario, "tipo_usuario": usuario.tipo_usuario}


@router.get("/me", response_model=UsuarioResponse)
def perfil_actual(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id_usuario == current_user.user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return usuario
