from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import Finca, RolUsuario
from app.schemas import FincaCreate, FincaOut

router = APIRouter(prefix="/fincas", tags=["fincas"])


@router.get("", response_model=list[FincaOut])
def listar_fincas(
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin, RolUsuario.supervisor, RolUsuario.visor)),
):
    return db.query(Finca).order_by(Finca.nombre).all()


@router.post("", response_model=FincaOut, status_code=201)
def crear_finca(
    payload: FincaCreate,
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin)),
):
    finca = Finca(nombre=payload.nombre)
    db.add(finca)
    db.commit()
    db.refresh(finca)
    return finca
