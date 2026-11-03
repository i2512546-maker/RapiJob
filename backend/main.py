import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="RapiJob",
    version="2.0.0",
    description="RapiJob conecta clientes con técnicos profesionales en Junín.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"
ASSETS = WEB_DIST / "assets"

@app.get("/config.json")
def public_config():
    # La anon key de Supabase y la clave de navegador de Maps son públicas por diseño.
    # La seguridad de datos se aplica con RLS en Supabase; nunca exponer service_role.
    return JSONResponse({
        "supabaseUrl": os.getenv("SUPABASE_URL", ""),
        "supabaseAnonKey": os.getenv("SUPABASE_ANON_KEY", ""),
        "googleMapsApiKey": os.getenv("GOOGLE_MAPS_API_KEY", ""),
    })

@app.get("/health")
def health():
    return {"status": "ok", "app": "RapiJob", "frontend_built": (WEB_DIST / "index.html").exists()}

if ASSETS.exists():
    app.mount("/assets", StaticFiles(directory=ASSETS), name="assets")

@app.get("/", include_in_schema=False)
def index():
    file = WEB_DIST / "index.html"
    if file.exists():
        return FileResponse(file)
    return {"message": "RapiJob web build not found", "hint": "Build the React app from /web."}

@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    candidate = (WEB_DIST / full_path).resolve()
    if WEB_DIST.resolve() in candidate.parents and candidate.is_file():
        return FileResponse(candidate)
    index_file = WEB_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"detail": "Not found"}
