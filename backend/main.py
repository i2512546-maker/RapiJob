import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from database import Base, engine
from app.routes import auth, servicios, ordenes, metodos_pago, slots_citas

# Configuración
settings = get_settings()

# Crear tablas si la base de datos está disponible
try:
    Base.metadata.create_all(bind=engine)
except Exception as exc:  # pragma: no cover - startup safety for Render/managed DB
    print(f"Advertencia: no se pudo inicializar la base de datos al arrancar: {exc}")

# Crear aplicación
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="API de RapiJob - Plataforma de servicios técnicos"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(auth.router)
app.include_router(servicios.router)
app.include_router(ordenes.router)
app.include_router(metodos_pago.router)
app.include_router(slots_citas.router)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="frontend-static")


@app.get("/")
async def root():
    """Servir el frontend o mostrar información de la API."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
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
    port = int(os.getenv("PORT", settings.PORT))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG
    )
