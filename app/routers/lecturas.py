from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_sensor_from_api_key, require_roles
from app.models import Lectura, RolUsuario, Sensor, Silo
from app.schemas import LecturaIn, LecturaOut

router = APIRouter(tags=["lecturas"])


@router.post("/lecturas", response_model=LecturaOut, status_code=201)
def recibir_lectura(
    payload: LecturaIn,
    db: Session = Depends(get_db),
    sensor: Sensor = Depends(get_sensor_from_api_key),
):
    # el device_id en el body es una verificación extra de que el payload
    # corresponde al mismo dispositivo que la API key, no la fuente de verdad
    if payload.device_id != sensor.device_id:
        raise HTTPException(status_code=400, detail="device_id no coincide con la API key usada")

    lectura = Lectura(
        sensor_id=sensor.id,
        distancia_cm=payload.distancia_cm,
        voltaje_bateria=payload.voltaje_bateria,
        # si el dispositivo no manda medido_en (ej. no tiene RTC ni hora de
        # red confiable), usamos la hora real del servidor como respaldo
        medido_en=payload.medido_en or datetime.now(timezone.utc),
    )
    db.add(lectura)
    db.commit()
    db.refresh(lectura)
    return lectura


@router.get("/silos/{silo_id}/lecturas", response_model=list[LecturaOut])
def historico_lecturas(
    silo_id: int,
    desde: datetime | None = Query(default=None),
    hasta: datetime | None = Query(default=None),
    limite: int = Query(default=500, le=2000),
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin, RolUsuario.supervisor, RolUsuario.visor)),
):
    silo = db.query(Silo).filter(Silo.id == silo_id).first()
    if silo is None:
        raise HTTPException(status_code=404, detail="Silo no encontrado")

    sensor = db.query(Sensor).filter(Sensor.silo_id == silo_id).first()
    if sensor is None:
        return []

    query = db.query(Lectura).filter(Lectura.sensor_id == sensor.id)
    if desde is not None:
        query = query.filter(Lectura.medido_en >= desde)
    if hasta is not None:
        query = query.filter(Lectura.medido_en <= hasta)

    return query.order_by(Lectura.medido_en.desc()).limit(limite).all()
