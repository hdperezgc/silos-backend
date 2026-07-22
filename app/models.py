import enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class RolUsuario(str, enum.Enum):
    admin = "admin"
    supervisor = "supervisor"
    visor = "visor"


class EstadoOrdenProduccion(str, enum.Enum):
    sugerida = "sugerida"
    confirmada = "confirmada"
    en_proceso = "en_proceso"
    completada = "completada"
    cancelada = "cancelada"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(120), nullable=False)
    email = Column(String(160), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(Enum(RolUsuario, name="rol_usuario"), nullable=False, default=RolUsuario.visor)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class Finca(Base):
    __tablename__ = "fincas"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(120), nullable=False, unique=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    silos = relationship("Silo", back_populates="finca")


class Silo(Base):
    __tablename__ = "silos"

    id = Column(Integer, primary_key=True)
    finca_id = Column(Integer, ForeignKey("fincas.id", ondelete="RESTRICT"), nullable=False)
    codigo = Column(String(40), nullable=False, unique=True)
    nombre = Column(String(120), nullable=False)

    diametro_m = Column(Numeric(6, 2), nullable=False)
    altura_total_m = Column(Numeric(6, 2), nullable=False)
    altura_cono_m = Column(Numeric(6, 2), nullable=False)
    altura_cilindro_m = Column(Numeric(6, 2), nullable=False)
    angulo_cono_grados = Column(Numeric(5, 2), nullable=False)
    altura_zona_ciega_cm = Column(Numeric(6, 2), nullable=False)

    capacidad_kg = Column(Numeric(10, 2), nullable=False)
    densidad_alimento_kg_m3 = Column(Numeric(8, 2), nullable=False)

    lead_time_dias = Column(Integer, nullable=True)

    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    finca = relationship("Finca", back_populates="silos")
    sensor = relationship("Sensor", back_populates="silo", uselist=False)
    ordenes_produccion = relationship("OrdenProduccion", back_populates="silo")


class Sensor(Base):
    __tablename__ = "sensores"

    id = Column(Integer, primary_key=True)
    silo_id = Column(Integer, ForeignKey("silos.id", ondelete="RESTRICT"), nullable=False, unique=True)
    device_id = Column(String(60), nullable=False, unique=True)
    api_key = Column(String(64), nullable=False, unique=True)
    modelo = Column(String(80), nullable=False, default="DYP-A01-V2.0")
    fecha_instalacion = Column(Date, nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    silo = relationship("Silo", back_populates="sensor")
    lecturas = relationship("Lectura", back_populates="sensor")


class Lectura(Base):
    __tablename__ = "lecturas"

    id = Column(BigInteger, primary_key=True)
    sensor_id = Column(Integer, ForeignKey("sensores.id", ondelete="CASCADE"), nullable=False)
    distancia_cm = Column(Numeric(6, 2), nullable=False)
    voltaje_bateria = Column(Numeric(4, 2), nullable=False)
    medido_en = Column(DateTime(timezone=True), nullable=False)
    recibido_en = Column(DateTime(timezone=True), server_default=func.now())

    sensor = relationship("Sensor", back_populates="lecturas")


class OrdenProduccion(Base):
    __tablename__ = "ordenes_produccion"

    id = Column(Integer, primary_key=True)
    silo_id = Column(Integer, ForeignKey("silos.id", ondelete="RESTRICT"), nullable=False)
    estado = Column(
        Enum(EstadoOrdenProduccion, name="estado_orden_produccion"),
        nullable=False,
        default=EstadoOrdenProduccion.sugerida,
    )

    cantidad_kg_sugerida = Column(Numeric(10, 2), nullable=False)
    cantidad_kg_confirmada = Column(Numeric(10, 2), nullable=True)

    fecha_necesaria = Column(DateTime(timezone=True), nullable=False)

    generada_por_usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    confirmada_por_usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    notas = Column(String(500), nullable=True)

    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    silo = relationship("Silo", back_populates="ordenes_produccion")
