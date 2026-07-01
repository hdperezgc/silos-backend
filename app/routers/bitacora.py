from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import Lectura, RolUsuario, Sensor, Silo
from app.services.geometry import calcular_nivel

router = APIRouter(tags=["bitacora"])

# ── Schemas ───────────────────────────────────────────────────────────────────

class EventoBitacora(BaseModel):
    silo_id: int
    silo_nombre: str
    fecha: datetime
    tipo: Literal["descarga", "llenado"]
    nivel_antes_pct: float
    nivel_despues_pct: float
    variacion_pct: float


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pct(distancia_cm: float, silo: Silo) -> float:
    r = calcular_nivel(
        distancia_cm=float(distancia_cm),
        altura_cono_m=float(silo.altura_cono_m),
        altura_cilindro_m=float(silo.altura_cilindro_m),
        diametro_m=float(silo.diametro_m),
        densidad_kg_m3=float(silo.densidad_alimento_kg_m3),
        altura_zona_ciega_cm=float(silo.altura_zona_ciega_cm),
    )
    return r["porcentaje"]


def _detectar_eventos(
    lecturas: list[Lectura],
    silo: Silo,
    umbral_descarga: float,
    umbral_llenado: float,
    ventana_ruido_min: int,
) -> list[EventoBitacora]:
    """
    Algoritmo:
    1. Convertir cada lectura a porcentaje.
    2. Descartar lecturas que suban y bajen dentro de una ventana corta
       (ruido de polvo al llenar).
    3. Detectar caídas >= umbral_descarga → evento "descarga".
    4. Detectar subidas >= umbral_llenado → evento "llenado".
    """
    if len(lecturas) < 2:
        return []

    puntos = []
    for l in lecturas:
        puntos.append({
            "fecha": l.medido_en,
            "pct": _pct(float(l.distancia_cm), silo),
        })

    # Filtrar ruido: si una lectura sube abruptamente y la siguiente vuelve a
    # bajar dentro de la ventana, se descarta (polvo al llenar)
    limpios = [puntos[0]]
    for i in range(1, len(puntos) - 1):
        prev = limpios[-1]["pct"]
        curr = puntos[i]["pct"]
        siguiente = puntos[i + 1]["pct"]
        delta_min = (puntos[i]["fecha"] - limpios[-1]["fecha"]).total_seconds() / 60
        # Si sube >15% y en menos de ventana_ruido_min minutos baja de nuevo → ruido
        if curr > prev + 15 and siguiente < curr - 10 and delta_min < ventana_ruido_min:
            continue
        limpios.append(puntos[i])
    limpios.append(puntos[-1])

    eventos = []
    for i in range(1, len(limpios)):
        antes = limpios[i - 1]["pct"]
        despues = limpios[i]["pct"]
        variacion = despues - antes

        if variacion <= -umbral_descarga:
            eventos.append(EventoBitacora(
                silo_id=silo.id,
                silo_nombre=silo.nombre,
                fecha=limpios[i]["fecha"],
                tipo="descarga",
                nivel_antes_pct=round(antes, 1),
                nivel_despues_pct=round(despues, 1),
                variacion_pct=round(variacion, 1),
            ))
        elif variacion >= umbral_llenado:
            eventos.append(EventoBitacora(
                silo_id=silo.id,
                silo_nombre=silo.nombre,
                fecha=limpios[i]["fecha"],
                tipo="llenado",
                nivel_antes_pct=round(antes, 1),
                nivel_despues_pct=round(despues, 1),
                variacion_pct=round(variacion, 1),
            ))

    return eventos


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("/bitacora", response_model=list[EventoBitacora])
def bitacora(
    finca_id: int | None = Query(default=None),
    silo_id: int | None = Query(default=None),
    desde: datetime | None = Query(default=None),
    hasta: datetime | None = Query(default=None),
    umbral_descarga: float = Query(default=3.0, ge=0.5, le=50),
    umbral_llenado: float = Query(default=20.0, ge=5, le=100),
    ventana_ruido_min: int = Query(default=60, ge=5, le=360),
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin, RolUsuario.supervisor, RolUsuario.visor)),
):
    # Silos a consultar
    query_silos = db.query(Silo).filter(Silo.activo.is_(True))
    if finca_id is not None:
        query_silos = query_silos.filter(Silo.finca_id == finca_id)
    if silo_id is not None:
        query_silos = query_silos.filter(Silo.id == silo_id)
    silos = query_silos.all()

    todos_eventos = []

    for silo in silos:
        sensor = db.query(Sensor).filter(Sensor.silo_id == silo.id).first()
        if sensor is None:
            continue

        query_lecturas = (
            db.query(Lectura)
            .filter(Lectura.sensor_id == sensor.id)
        )
        if desde:
            query_lecturas = query_lecturas.filter(Lectura.medido_en >= desde)
        if hasta:
            query_lecturas = query_lecturas.filter(Lectura.medido_en <= hasta)

        lecturas = query_lecturas.order_by(Lectura.medido_en.asc()).all()
        eventos = _detectar_eventos(lecturas, silo, umbral_descarga, umbral_llenado, ventana_ruido_min)
        todos_eventos.extend(eventos)

    # Ordenar cronológico descendente (más reciente primero)
    todos_eventos.sort(key=lambda e: e.fecha, reverse=True)
    return todos_eventos
