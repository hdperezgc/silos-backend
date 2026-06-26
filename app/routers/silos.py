from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import Lectura, RolUsuario, Sensor, Silo
from app.schemas import NivelActual, SiloCreate, SiloDetalleOut, SiloOut
from app.services.geometry import calcular_nivel

router = APIRouter(prefix="/silos", tags=["silos"])


@router.get("", response_model=list[SiloOut])
def listar_silos(
    finca_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin, RolUsuario.supervisor, RolUsuario.visor)),
):
    query = db.query(Silo).filter(Silo.activo.is_(True))
    if finca_id is not None:
        query = query.filter(Silo.finca_id == finca_id)
    return query.order_by(Silo.codigo).all()


@router.get("/{silo_id}", response_model=SiloDetalleOut)
def detalle_silo(
    silo_id: int,
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin, RolUsuario.supervisor, RolUsuario.visor)),
):
    silo = db.query(Silo).filter(Silo.id == silo_id).first()
    if silo is None:
        raise HTTPException(status_code=404, detail="Silo no encontrado")

    nivel_actual = None
    sensor = db.query(Sensor).filter(Sensor.silo_id == silo.id).first()
    if sensor is not None:
        ultima = (
            db.query(Lectura)
            .filter(Lectura.sensor_id == sensor.id)
            .order_by(Lectura.medido_en.desc())
            .first()
        )
        if ultima is not None:
            calculo = calcular_nivel(
                distancia_cm=float(ultima.distancia_cm),
                altura_cono_m=float(silo.altura_cono_m),
                altura_cilindro_m=float(silo.altura_cilindro_m),
                diametro_m=float(silo.diametro_m),
                densidad_kg_m3=float(silo.densidad_alimento_kg_m3),
                altura_zona_ciega_cm=float(silo.altura_zona_ciega_cm),
            )
            nivel_actual = NivelActual(
                distancia_cm=float(ultima.distancia_cm),
                medido_en=ultima.medido_en,
                voltaje_bateria=float(ultima.voltaje_bateria),
                **calculo,
            )

    return SiloDetalleOut(
        **SiloOut.model_validate(silo).model_dump(),
        nivel_actual=nivel_actual,
    )


@router.post("", response_model=SiloOut, status_code=201)
def crear_silo(
    payload: SiloCreate,
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin)),
):
    silo = Silo(**payload.model_dump())
    db.add(silo)
    db.commit()
    db.refresh(silo)
    return silo
