from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models import OrdenProduccion, RolUsuario, Silo, Usuario
from app.schemas import (
    OrdenProduccionActualizarEstado,
    OrdenProduccionConfirmar,
    OrdenProduccionOut,
)
from app.services.produccion import evaluar_orden_sugerida

router = APIRouter(tags=["ordenes_produccion"])


@router.get("/ordenes", response_model=list[OrdenProduccionOut])
def listar_ordenes(
    estado: str | None = Query(default=None),
    silo_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin, RolUsuario.supervisor, RolUsuario.visor)),
):
    query = db.query(OrdenProduccion)
    if estado is not None:
        query = query.filter(OrdenProduccion.estado == estado)
    if silo_id is not None:
        query = query.filter(OrdenProduccion.silo_id == silo_id)
    return query.order_by(OrdenProduccion.fecha_necesaria.asc()).all()


@router.post("/ordenes/evaluar-todas", response_model=list[OrdenProduccionOut])
def evaluar_todas(
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin, RolUsuario.supervisor)),
):
    """
    Revisa todos los silos activos y crea una orden 'sugerida' para
    cualquiera que lo necesite según su proyección de consumo y su
    lead_time_dias. Pensado para llamarse al cargar el dashboard.
    """
    silos = db.query(Silo).filter(Silo.activo.is_(True)).all()
    nuevas = []
    for silo in silos:
        orden = evaluar_orden_sugerida(db, silo)
        if orden is not None:
            nuevas.append(orden)
    return nuevas


@router.patch("/ordenes/{orden_id}/confirmar", response_model=OrdenProduccionOut)
def confirmar_orden(
    orden_id: int,
    payload: OrdenProduccionConfirmar,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles(RolUsuario.admin, RolUsuario.supervisor)),
):
    orden = db.query(OrdenProduccion).filter(OrdenProduccion.id == orden_id).first()
    if orden is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if orden.estado != "sugerida":
        raise HTTPException(status_code=400, detail="Solo se puede confirmar una orden en estado 'sugerida'")

    orden.cantidad_kg_confirmada = payload.cantidad_kg_confirmada
    orden.notas = payload.notas
    orden.estado = "confirmada"
    orden.confirmada_por_usuario_id = usuario.id
    orden.actualizado_en = datetime.now(timezone.utc)

    db.commit()
    db.refresh(orden)
    return orden


@router.patch("/ordenes/{orden_id}/estado", response_model=OrdenProduccionOut)
def actualizar_estado_orden(
    orden_id: int,
    payload: OrdenProduccionActualizarEstado,
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin, RolUsuario.supervisor)),
):
    orden = db.query(OrdenProduccion).filter(OrdenProduccion.id == orden_id).first()
    if orden is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    orden.estado = payload.estado
    if payload.notas is not None:
        orden.notas = payload.notas
    orden.actualizado_en = datetime.now(timezone.utc)

    db.commit()
    db.refresh(orden)
    return orden
