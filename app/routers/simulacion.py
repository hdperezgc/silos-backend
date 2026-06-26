import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import Lectura, RolUsuario, Sensor, Silo
from app.schemas import SimulacionIn, SimulacionOut
from app.services.geometry import calcular_distancia_desde_porcentaje

router = APIRouter(tags=["simulacion"])


@router.post("/silos/{silo_id}/simular", response_model=SimulacionOut)
def simular_lecturas(
    silo_id: int,
    payload: SimulacionIn,
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin)),
):
    silo = db.query(Silo).filter(Silo.id == silo_id).first()
    if silo is None:
        raise HTTPException(status_code=404, detail="Silo no encontrado")

    sensor = db.query(Sensor).filter(Sensor.silo_id == silo_id).first()
    if sensor is None:
        raise HTTPException(status_code=404, detail="Este silo no tiene sensor asignado todavía")

    borradas = 0
    if payload.borrar_anteriores:
        borradas = db.query(Lectura).filter(Lectura.sensor_id == sensor.id).delete()

    total_puntos = payload.dias * payload.lecturas_por_dia
    if total_puntos < 2:
        raise HTTPException(status_code=400, detail="dias * lecturas_por_dia debe ser al menos 2")

    intervalo_horas = (payload.dias * 24) / total_puntos
    ahora = datetime.utcnow()

    nuevas = []
    for i in range(total_puntos):
        avance = i / (total_puntos - 1)
        pct_base = payload.porcentaje_inicial + (payload.porcentaje_final - payload.porcentaje_inicial) * avance
        ruido = random.uniform(-payload.ruido_pct, payload.ruido_pct)
        pct = max(0.0, min(100.0, pct_base + ruido))

        distancia_cm = calcular_distancia_desde_porcentaje(
            porcentaje=pct,
            altura_cono_m=float(silo.altura_cono_m),
            altura_cilindro_m=float(silo.altura_cilindro_m),
            diametro_m=float(silo.diametro_m),
        )

        medido_en = ahora - timedelta(hours=(total_puntos - 1 - i) * intervalo_horas)
        voltaje = round(random.uniform(3.6, 4.1), 2)

        nuevas.append(
            Lectura(
                sensor_id=sensor.id,
                distancia_cm=distancia_cm,
                voltaje_bateria=voltaje,
                medido_en=medido_en,
            )
        )

    db.bulk_save_objects(nuevas)
    db.commit()

    return SimulacionOut(silo_id=silo_id, lecturas_insertadas=len(nuevas), borradas=borradas)
