from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import EstadoOrdenProduccion, RolUsuario


# --- Auth ---

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    rol: RolUsuario
    activo: bool

    class Config:
        from_attributes = True


class UsuarioCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)
    rol: RolUsuario = RolUsuario.visor


class UsuarioUpdate(BaseModel):
    rol: RolUsuario | None = None
    activo: bool | None = None


# --- Fincas ---

class FincaOut(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True


class FincaCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)


# --- Silos ---

class SiloCreate(BaseModel):
    finca_id: int
    codigo: str = Field(min_length=2, max_length=40)
    nombre: str = Field(min_length=2, max_length=120)
    diametro_m: float = Field(gt=0)
    altura_total_m: float = Field(gt=0)
    altura_cono_m: float = Field(gt=0)
    altura_cilindro_m: float = Field(gt=0)
    angulo_cono_grados: float = Field(gt=0, lt=180)
    altura_zona_ciega_cm: float = Field(ge=0)
    capacidad_kg: float = Field(gt=0)
    densidad_alimento_kg_m3: float = Field(gt=0)
    lead_time_dias: int | None = Field(default=None, ge=0)


class SiloOut(BaseModel):
    id: int
    finca_id: int
    codigo: str
    nombre: str
    diametro_m: float
    altura_total_m: float
    altura_cono_m: float
    altura_cilindro_m: float
    angulo_cono_grados: float
    altura_zona_ciega_cm: float
    capacidad_kg: float
    densidad_alimento_kg_m3: float
    lead_time_dias: int | None
    activo: bool

    class Config:
        from_attributes = True


class NivelActual(BaseModel):
    distancia_cm: float
    altura_alimento_m: float
    volumen_m3: float
    porcentaje: float
    kg_estimados: float
    medido_en: datetime
    voltaje_bateria: float


class SiloDetalleOut(SiloOut):
    nivel_actual: NivelActual | None = None


# --- Sensores ---

class SensorCreate(BaseModel):
    silo_id: int
    device_id: str = Field(min_length=2, max_length=60)
    modelo: str = Field(default="DYP-A01-V2.0", max_length=80)
    fecha_instalacion: date


class SensorOut(BaseModel):
    id: int
    silo_id: int
    device_id: str
    modelo: str
    fecha_instalacion: date
    activo: bool
    intervalo_envio_seg: int
    solicitud_lectura_pendiente: bool
    creado_en: datetime

    class Config:
        from_attributes = True


class SensorCreadoOut(SensorOut):
    api_key: str  # solo se devuelve completo al crear el sensor


class SensorUpdate(BaseModel):
    device_id: str | None = Field(default=None, min_length=2, max_length=60)
    modelo: str | None = Field(default=None, max_length=80)
    fecha_instalacion: date | None = None
    activo: bool | None = None
    intervalo_envio_seg: int | None = Field(default=None, ge=30, le=86400)


class SensorApiKeyOut(BaseModel):
    api_key: str


class SensorConfigOut(BaseModel):
    """
    Lo que el dispositivo recibe al consultar su propia configuración.
    Incluye la bandera de solicitud para que, en la misma conexión GPRS,
    el Arduino sepa tanto su intervalo normal como si debe reportar YA.
    """

    intervalo_envio_seg: int
    solicitud_lectura_pendiente: bool


# --- Lecturas ---

class LecturaIn(BaseModel):
    device_id: str
    distancia_cm: float = Field(gt=0)
    voltaje_bateria: float = Field(gt=0, lt=5)
    medido_en: datetime | None = None  # si no llega, el backend usa la hora del servidor


class LecturaOut(BaseModel):
    id: int
    distancia_cm: float
    voltaje_bateria: float
    medido_en: datetime
    recibido_en: datetime

    class Config:
        from_attributes = True


# --- Proyección ---

class ProyeccionOut(BaseModel):
    silo_id: int
    porcentaje_actual: float
    consumo_diario_promedio_kg: float
    dias_restantes: float | None
    confiable: bool
    mensaje: str


# --- Órdenes de producción ---

class OrdenProduccionOut(BaseModel):
    id: int
    silo_id: int
    estado: EstadoOrdenProduccion
    cantidad_kg_sugerida: float
    cantidad_kg_confirmada: float | None
    fecha_necesaria: datetime
    generada_por_usuario_id: int | None
    confirmada_por_usuario_id: int | None
    notas: str | None
    creado_en: datetime
    actualizado_en: datetime

    class Config:
        from_attributes = True


class OrdenProduccionConfirmar(BaseModel):
    cantidad_kg_confirmada: float = Field(gt=0)
    notas: str | None = Field(default=None, max_length=500)


class OrdenProduccionActualizarEstado(BaseModel):
    estado: EstadoOrdenProduccion
    notas: str | None = Field(default=None, max_length=500)
