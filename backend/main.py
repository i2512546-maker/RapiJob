from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from database import Base, engine
from app.routes import auth, servicios, ordenes

# Configuración
settings = get_settings()

# Crear tablas (solo en desarrollo)
Base.metadata.create_all(bind=engine)

# Crear aplicación
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="API de RapiJob - Plataforma de servicios técnicos"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambiar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(auth.router)
app.include_router(servicios.router)
app.include_router(ordenes.router)


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "mensaje": "Bienvenido a RapiJob API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
