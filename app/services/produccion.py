"""
Lógica de sugerencia de órdenes de producción.

Un silo necesita una orden sugerida cuando, según la proyección de consumo
reciente, se va a quedar sin alimento antes de que el molino pueda producir
y entregar un lote nuevo (su lead_time_dias configurado).
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import EstadoOrdenProduccion, Lectura, OrdenProduccion, Sensor, Silo
from app.services.geometry import calcular_nivel
from app.services.projection import calcular_proyeccion

VENTANA_LECTURAS = 50

ESTADOS_ABIERTOS = (
    EstadoOrdenProduccion.sugerida,
    EstadoOrdenProduccion.confirmada,
    EstadoOrdenProduccion.en_proceso,
)


def evaluar_orden_sugerida(db: Session, silo: Silo) -> OrdenProduccion | None:
    """
    Revisa un silo y, si corresponde, crea una nueva orden en estado
    'sugerida'. Devuelve la orden creada, o None si no corresponde crear
    una (silo sin lead_time configurado, ya tiene una orden abierta,
    proyección no confiable, o todavía tiene margen de sobra).
    """
    if silo.lead_time_dias is None:
        return None

    ya_tiene_abierta = (
        db.query(OrdenProduccion)
        .filter(
            OrdenProduccion.silo_id == silo.id,
            OrdenProduccion.estado.in_(ESTADOS_ABIERTOS),
        )
        .first()
    )
    if ya_tiene_abierta:
        return None

    sensor = db.query(Sensor).filter(Sensor.silo_id == silo.id).first()
    if sensor is None:
        return None

    lecturas = (
        db.query(Lectura)
        .filter(Lectura.sensor_id == sensor.id)
        .order_by(Lectura.medido_en.desc())
        .limit(VENTANA_LECTURAS)
        .all()
    )
    lecturas.reverse()
    if not lecturas:
        return None

    puntos = []
    for lectura in lecturas:
        calculo = calcular_nivel(
            distancia_cm=float(lectura.distancia_cm),
            altura_cono_m=float(silo.altura_cono_m),
            altura_cilindro_m=float(silo.altura_cilindro_m),
            diametro_m=float(silo.diametro_m),
            densidad_kg_m3=float(silo.densidad_alimento_kg_m3),
            altura_zona_ciega_cm=float(silo.altura_zona_ciega_cm),
        )
        puntos.append((lectura.medido_en, calculo["kg_estimados"]))

    resultado = calcular_proyeccion(puntos)
    if not resultado["confiable"] or resultado["dias_restantes"] is None:
        return None

    if resultado["dias_restantes"] > silo.lead_time_dias:
        return None

    kg_actual = puntos[-1][1]
    cantidad_sugerida = float(silo.capacidad_kg) - kg_actual
    if cantidad_sugerida <= 0:
        return None

    fecha_necesaria = datetime.now(timezone.utc) + timedelta(days=resultado["dias_restantes"])

    orden = OrdenProduccion(
        silo_id=silo.id,
        estado=EstadoOrdenProduccion.sugerida,
        cantidad_kg_sugerida=round(cantidad_sugerida, 1),
        fecha_necesaria=fecha_necesaria,
        generada_por_usuario_id=None,  # None = generada por el sistema
    )
    db.add(orden)
    db.commit()
    db.refresh(orden)
    return orden
