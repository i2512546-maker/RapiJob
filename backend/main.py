import os
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import get_settings
from database import Base, engine, SessionLocal
from app.routes import auth, servicios, ordenes, metodos_pago, slots_citas
from app.models.models import CategoriaServicio, Servicio, SlotCita

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="RapiJob conecta clientes con técnicos para solicitar servicios.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(servicios.router)
app.include_router(ordenes.router)
app.include_router(metodos_pago.router)
app.include_router(slots_citas.router)

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="frontend-static")


@app.on_event("startup")
def initialize_database():
    # Crea las tablas definidas por los modelos. Para bases existentes, aplicar
    # las migraciones documentadas antes de desplegar esta versión.
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        category_names = [
            "Computadoras y laptops",
            "Software y sistemas",
            "Redes e internet",
            "Mantenimiento preventivo",
        ]
        categories = {}
        for name in category_names:
            category = db.query(CategoriaServicio).filter(
                CategoriaServicio.nombre_categoria == name
            ).first()
            if not category:
                category = CategoriaServicio(nombre_categoria=name, estado="activa")
                db.add(category)
                db.flush()
            categories[name] = category

        # Precios orientativos en soles peruanos; el técnico confirma el costo final.
        sample_services = [
            ("Diagnóstico de PC o laptop", "Evaluación inicial de fallas de hardware o software.", 45, 30, "Computadoras y laptops"),
            ("Mantenimiento preventivo de PC", "Limpieza interna, revisión de componentes y optimización básica.", 90, 90, "Mantenimiento preventivo"),
            ("Instalación de Windows", "Instalación y configuración del sistema operativo. Licencia no incluida.", 100, 120, "Software y sistemas"),
            ("Eliminación de virus y malware", "Revisión y limpieza de amenazas y programas no deseados.", 70, 60, "Software y sistemas"),
            ("Instalación de SSD o memoria RAM", "Instalación física y comprobación de compatibilidad.", 60, 60, "Computadoras y laptops"),
            ("Configuración de Wi-Fi y red", "Configuración de router, conexión y solución de problemas de red.", 65, 60, "Redes e internet"),
        ]
        if db.query(Servicio).count() == 0:
            for name, description, price, duration, category_name in sample_services:
                db.add(Servicio(
                    id_categoria=categories[category_name].id_categoria,
                    nombre_servicio=name,
                    descripcion=description,
                    duracion_estimada_minutos=duration,
                    precio_base=price,
                    estado="disponible",
                ))

        if db.query(SlotCita).count() == 0:
            now = datetime.utcnow()
            for day_offset in range(1, 8):
                day = (now + timedelta(days=day_offset)).date()
                for hour in (9, 11, 14, 16):
                    start = datetime.combine(day, datetime.min.time()).replace(hour=hour)
                    db.add(SlotCita(
                        fecha=start,
                        hora_inicio=start,
                        hora_fin=start + timedelta(hours=1),
                        capacidad_maxima=1,
                        reservas_actuales=0,
                        estado="disponible",
                    ))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@app.get("/")
def root():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"mensaje": "RapiJob API", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", settings.PORT)), reload=settings.DEBUG)
