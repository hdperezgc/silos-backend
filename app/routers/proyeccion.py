from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import Lectura, RolUsuario, Sensor, Silo
from app.schemas import ProyeccionOut
from app.services.geometry import calcular_nivel
from app.services.projection import calcular_proyeccion

router = APIRouter(tags=["proyeccion"])

VENTANA_LECTURAS = 50  # suficiente para varios días si se mide cada 1-2 horas


@router.get("/silos/{silo_id}/proyeccion", response_model=ProyeccionOut)
def proyeccion_silo(
    silo_id: int,
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin, RolUsuario.supervisor, RolUsuario.visor)),
):
    silo = db.query(Silo).filter(Silo.id == silo_id).first()
    if silo is None:
        raise HTTPException(status_code=404, detail="Silo no encontrado")

    sensor = db.query(Sensor).filter(Sensor.silo_id == silo_id).first()
    if sensor is None:
        raise HTTPException(status_code=404, detail="Este silo no tiene sensor asignado")

    lecturas = (
        db.query(Lectura)
        .filter(Lectura.sensor_id == sensor.id)
        .order_by(Lectura.medido_en.desc())
        .limit(VENTANA_LECTURAS)
        .all()
    )
    lecturas.reverse()  # de más antigua a más reciente, lo que espera projection.py

    if not lecturas:
        raise HTTPException(status_code=404, detail="Este silo todavía no tiene lecturas")

    puntos = []
    for lectura in lecturas:
        calculo = calcular_nivel(
            distancia_cm=float(lectura.distancia_cm),
            altura_cono_m=float(silo.altura_cono_m),
            altura_cilindro_m=float(silo.altura_cilindro_m),
            diametro_m=float(silo.diametro_m),
            densidad_kg_m3=float(silo.densidad_alimento_kg_m3),
            altura_zona_ciega_cm=float(silo.altura_zona_ciega_cm),
        )
        puntos.append((lectura.medido_en, calculo["kg_estimados"]))

    resultado = calcular_proyeccion(puntos)
    porcentaje_actual = calcular_nivel(
        distancia_cm=float(lecturas[-1].distancia_cm),
        altura_cono_m=float(silo.altura_cono_m),
        altura_cilindro_m=float(silo.altura_cilindro_m),
        diametro_m=float(silo.diametro_m),
        densidad_kg_m3=float(silo.densidad_alimento_kg_m3),
        altura_zona_ciega_cm=float(silo.altura_zona_ciega_cm),
    )["porcentaje"]

    return ProyeccionOut(silo_id=silo_id, porcentaje_actual=porcentaje_actual, **resultado)
