import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import Lectura, RolUsuario, Sensor, Silo
from app.schemas import DescargaIn, LlenadoIn, SimulacionIn, SimulacionOut
from app.services.geometry import calcular_distancia_desde_porcentaje, calcular_nivel

router = APIRouter(tags=["simulacion"])


def _get_silo_y_sensor(silo_id: int, db: Session):
    silo = db.query(Silo).filter(Silo.id == silo_id).first()
    if silo is None:
        raise HTTPException(status_code=404, detail="Silo no encontrado")
    sensor = db.query(Sensor).filter(Sensor.silo_id == silo_id).first()
    if sensor is None:
        raise HTTPException(status_code=404, detail="Este silo no tiene sensor asignado")
    return silo, sensor


def _kg_a_pct(kg: float, capacidad_kg: float) -> float:
    return max(0.0, min(100.0, (kg / capacidad_kg) * 100))


def _ultima_lectura_pct(sensor_id: int, silo: Silo, db: Session) -> float:
    ultima = (
        db.query(Lectura)
        .filter(Lectura.sensor_id == sensor_id)
        .order_by(Lectura.medido_en.desc())
        .first()
    )
    if ultima is None:
        return 0.0
    r = calcular_nivel(
        distancia_cm=float(ultima.distancia_cm),
        altura_cono_m=float(silo.altura_cono_m),
        altura_cilindro_m=float(silo.altura_cilindro_m),
        diametro_m=float(silo.diametro_m),
        densidad_kg_m3=float(silo.densidad_alimento_kg_m3),
        altura_zona_ciega_cm=float(silo.altura_zona_ciega_cm),
    )
    return r["porcentaje"]


def _distancia(pct: float, silo: Silo) -> float:
    return calcular_distancia_desde_porcentaje(
        porcentaje=pct,
        altura_cono_m=float(silo.altura_cono_m),
        altura_cilindro_m=float(silo.altura_cilindro_m),
        diametro_m=float(silo.diametro_m),
    )


# ── Serie automática ──────────────────────────────────────────────────────────

@router.post("/silos/{silo_id}/simular", response_model=SimulacionOut)
def simular_lecturas(
    silo_id: int,
    payload: SimulacionIn,
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin)),
):
    silo, sensor = _get_silo_y_sensor(silo_id, db)
    capacidad = float(silo.capacidad_kg)

    if payload.kg_inicial > capacidad:
        raise HTTPException(status_code=400, detail=f"kg inicial supera la capacidad del silo ({capacidad:.0f} kg)")

    borradas = 0
    if payload.borrar_anteriores:
        borradas = db.query(Lectura).filter(Lectura.sensor_id == sensor.id).delete()

    total_puntos = payload.dias * payload.lecturas_por_dia
    if total_puntos < 2:
        raise HTTPException(status_code=400, detail="dias * lecturas_por_dia debe ser al menos 2")

    pct_inicial = _kg_a_pct(payload.kg_inicial, capacidad)
    pct_final = _kg_a_pct(payload.kg_final, capacidad)

    intervalo_horas = (payload.dias * 24) / total_puntos
    ahora = datetime.utcnow()
    nuevas = []

    for i in range(total_puntos):
        avance = i / (total_puntos - 1)
        pct_base = pct_inicial + (pct_final - pct_inicial) * avance
        pct = max(0.0, min(100.0, pct_base + random.uniform(-payload.ruido_pct, payload.ruido_pct)))
        nuevas.append(Lectura(
            sensor_id=sensor.id,
            distancia_cm=_distancia(pct, silo),
            voltaje_bateria=round(random.uniform(3.6, 4.1), 2),
            medido_en=ahora - timedelta(hours=(total_puntos - 1 - i) * intervalo_horas),
        ))

    db.bulk_save_objects(nuevas)
    db.commit()
    return SimulacionOut(silo_id=silo_id, lecturas_insertadas=len(nuevas), borradas=borradas)


# ── Llenar silo ───────────────────────────────────────────────────────────────

@router.post("/silos/{silo_id}/simular/llenar", response_model=SimulacionOut)
def llenar_silo(
    silo_id: int,
    payload: LlenadoIn,
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin)),
):
    silo, sensor = _get_silo_y_sensor(silo_id, db)
    capacidad = float(silo.capacidad_kg)

    if payload.kg > capacidad:
        raise HTTPException(status_code=400, detail=f"Supera la capacidad del silo ({capacidad:.0f} kg)")

    pct_objetivo = _kg_a_pct(payload.kg, capacidad)
    ahora = datetime.utcnow()
    nuevas = []

    # Lecturas ruidosas simulando el polvo al llenar
    for i in range(3):
        nuevas.append(Lectura(
            sensor_id=sensor.id,
            distancia_cm=_distancia(random.uniform(20, 80), silo),
            voltaje_bateria=round(random.uniform(3.6, 4.1), 2),
            medido_en=ahora - timedelta(minutes=30 - i * 10),
        ))

    # Lectura estable al nivel real (polvo asentado)
    nuevas.append(Lectura(
        sensor_id=sensor.id,
        distancia_cm=_distancia(pct_objetivo, silo),
        voltaje_bateria=round(random.uniform(3.6, 4.1), 2),
        medido_en=ahora,
    ))

    db.bulk_save_objects(nuevas)
    db.commit()
    return SimulacionOut(silo_id=silo_id, lecturas_insertadas=len(nuevas), borradas=0)


# ── Descarga manual ───────────────────────────────────────────────────────────

@router.post("/silos/{silo_id}/simular/descarga", response_model=SimulacionOut)
def registrar_descarga(
    silo_id: int,
    payload: DescargaIn,
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin)),
):
    silo, sensor = _get_silo_y_sensor(silo_id, db)
    capacidad = float(silo.capacidad_kg)

    pct_actual = _ultima_lectura_pct(sensor.id, silo, db)
    kg_actual = (pct_actual / 100) * capacidad
    kg_nuevo = max(0.0, kg_actual - payload.kg_bajada)
    pct_nuevo = _kg_a_pct(kg_nuevo, capacidad)

    lectura = Lectura(
        sensor_id=sensor.id,
        distancia_cm=_distancia(pct_nuevo, silo),
        voltaje_bateria=round(random.uniform(3.6, 4.1), 2),
        medido_en=datetime.utcnow() - timedelta(hours=payload.hace_horas),
    )
    db.add(lectura)
    db.commit()
    return SimulacionOut(silo_id=silo_id, lecturas_insertadas=1, borradas=0)
