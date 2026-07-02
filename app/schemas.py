from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import RolUsuario


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


# --- Lecturas ---

class LecturaIn(BaseModel):
    device_id: str
    distancia_cm: float = Field(gt=0)
    voltaje_bateria: float = Field(gt=0, lt=5)
    medido_en: datetime


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


# --- Simulación (datos de prueba, solo admin) ---

class SimulacionIn(BaseModel):
    kg_inicial: float = Field(gt=0)
    kg_final: float = Field(ge=0)
    dias: int = Field(default=14, ge=1, le=90)
    lecturas_por_dia: int = Field(default=12, ge=1, le=48)
    ruido_pct: float = Field(default=2.0, ge=0, le=20)
    borrar_anteriores: bool = False


class SimulacionOut(BaseModel):
    silo_id: int
    lecturas_insertadas: int
    borradas: int


class LlenadoIn(BaseModel):
    kg: float = Field(gt=0)


class DescargaIn(BaseModel):
    kg_bajada: float = Field(gt=0)
    hace_horas: float = Field(default=0, ge=0)
