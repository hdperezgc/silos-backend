from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    admin_usuarios,
    auth,
    bitacora,
    fincas,
    lecturas,
    ordenes_produccion,
    proyeccion,
    silos,
    simulacion,
)

app = FastAPI(title="Granjazul - Monitoreo de silos", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(fincas.router)
app.include_router(silos.router)
app.include_router(lecturas.router)
app.include_router(proyeccion.router)
app.include_router(simulacion.router)
app.include_router(admin_usuarios.router)
app.include_router(bitacora.router)
app.include_router(ordenes_produccion.router)


@app.get("/health")
def health():
    return {"status": "ok"}
