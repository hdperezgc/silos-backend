from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RolUsuario, Sensor, Usuario
from app.security import decode_access_token

bearer_scheme = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")

    usuario = db.query(Usuario).filter(Usuario.id == payload.get("sub")).first()
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")
    return usuario


def require_roles(*roles_permitidos: RolUsuario):
    def verificador(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenés permiso para esta acción",
            )
        return usuario

    return verificador


def get_sensor_from_api_key(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db),
) -> Sensor:
    sensor = db.query(Sensor).filter(Sensor.api_key == api_key, Sensor.activo.is_(True)).first()
    if sensor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key inválida")
    return sensor
