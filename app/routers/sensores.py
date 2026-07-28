import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import RolUsuario, Sensor, Silo
from app.schemas import (
    SensorApiKeyOut,
    SensorCreadoOut,
    SensorCreate,
    SensorOut,
    SensorUpdate,
)

router = APIRouter(prefix="/sensores", tags=["sensores"])


def _generar_api_key() -> str:
    return secrets.token_hex(24)


@router.get("", response_model=list[SensorOut])
def listar_sensores(
    silo_id: int | None = Query(default=None),
    activo: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin, RolUsuario.supervisor, RolUsuario.visor)),
):
    query = db.query(Sensor)
    if silo_id is not None:
        query = query.filter(Sensor.silo_id == silo_id)
    if activo is not None:
        query = query.filter(Sensor.activo.is_(activo))
    return query.order_by(Sensor.id).all()


@router.get("/{sensor_id}", response_model=SensorOut)
def detalle_sensor(
    sensor_id: int,
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin, RolUsuario.supervisor, RolUsuario.visor)),
):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return sensor


@router.post("", response_model=SensorCreadoOut, status_code=201)
def crear_sensor(
    payload: SensorCreate,
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin)),
):
    silo = db.query(Silo).filter(Silo.id == payload.silo_id).first()
    if silo is None:
        raise HTTPException(status_code=404, detail="Silo no encontrado")

    if db.query(Sensor).filter(Sensor.silo_id == payload.silo_id).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese silo ya tiene un sensor asignado")

    if db.query(Sensor).filter(Sensor.device_id == payload.device_id).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un sensor con ese device_id")

    sensor = Sensor(
        silo_id=payload.silo_id,
        device_id=payload.device_id,
        modelo=payload.modelo,
        fecha_instalacion=payload.fecha_instalacion,
        api_key=_generar_api_key(),
        activo=True,
    )
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return sensor


@router.patch("/{sensor_id}", response_model=SensorOut)
def actualizar_sensor(
    sensor_id: int,
    payload: SensorUpdate,
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin)),
):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    if payload.device_id is not None and payload.device_id != sensor.device_id:
        if db.query(Sensor).filter(Sensor.device_id == payload.device_id).first() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un sensor con ese device_id")
        sensor.device_id = payload.device_id

    if payload.modelo is not None:
        sensor.modelo = payload.modelo
    if payload.fecha_instalacion is not None:
        sensor.fecha_instalacion = payload.fecha_instalacion
    if payload.activo is not None:
        sensor.activo = payload.activo

    db.commit()
    db.refresh(sensor)
    return sensor


@router.patch("/{sensor_id}/api-key", response_model=SensorApiKeyOut)
def regenerar_api_key(
    sensor_id: int,
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin)),
):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    sensor.api_key = _generar_api_key()
    db.commit()
    db.refresh(sensor)
    return SensorApiKeyOut(api_key=sensor.api_key)
