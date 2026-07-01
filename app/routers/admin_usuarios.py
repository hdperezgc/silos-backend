from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import RolUsuario, Usuario
from app.schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.security import hash_password

router = APIRouter(prefix="/admin/usuarios", tags=["admin"])


@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin)),
):
    return db.query(Usuario).order_by(Usuario.nombre).all()


@router.post("", response_model=UsuarioOut, status_code=201)
def crear_usuario(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles(RolUsuario.admin)),
):
    existente = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email",
        )

    usuario = Usuario(
        nombre=payload.nombre,
        email=payload.email,
        password_hash=hash_password(payload.password),
        rol=payload.rol,
        activo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.patch("/{usuario_id}", response_model=UsuarioOut)
def actualizar_usuario(
    usuario_id: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario_actual=Depends(require_roles(RolUsuario.admin)),
):
    if usuario_id == usuario_actual.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No podés modificar tu propio usuario desde este panel",
        )

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if payload.rol is not None:
        usuario.rol = payload.rol
    if payload.activo is not None:
        usuario.activo = payload.activo

    db.commit()
    db.refresh(usuario)
    return usuario


class PasswordReset(BaseModel):
    nueva_password: str = Field(min_length=8)


@router.patch("/{usuario_id}/password", status_code=204)
def resetear_password(
    usuario_id: int,
    payload: PasswordReset,
    db: Session = Depends(get_db),
    usuario_actual=Depends(require_roles(RolUsuario.admin)),
):
    if usuario_id == usuario_actual.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usá el perfil para cambiar tu propia contraseña",
        )

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.password_hash = hash_password(payload.nueva_password)
    db.commit()
