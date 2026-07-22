"""
Envío del webhook saliente hacia n8n cada vez que llega una lectura nueva.

Corre en background (ver BackgroundTasks en el router de lecturas): si n8n
está caído o lento, el dispositivo que mandó la lectura ya recibió su
201 Created antes de que esto se ejecute, así que un fallo acá nunca debe
afectarlo. Cualquier error se registra en el log, nunca se propaga.
"""

import logging
from datetime import datetime, timezone

import httpx

from app.config import settings
from app.database import SessionLocal
from app.models import Lectura, Sensor, Silo
from app.services.geometry import calcular_nivel
from app.services.projection import calcular_proyeccion

logger = logging.getLogger(__name__)

VENTANA_LECTURAS = 50


def _construir_payload(db, lectura: Lectura, sensor: Sensor, silo: Silo) -> dict:
    nivel = calcular_nivel(
        distancia_cm=float(lectura.distancia_cm),
        altura_cono_m=float(silo.altura_cono_m),
        altura_cilindro_m=float(silo.altura_cilindro_m),
        diametro_m=float(silo.diametro_m),
        densidad_kg_m3=float(silo.densidad_alimento_kg_m3),
        altura_zona_ciega_cm=float(silo.altura_zona_ciega_cm),
    )

    lecturas_historicas = (
        db.query(Lectura)
        .filter(Lectura.sensor_id == sensor.id)
        .order_by(Lectura.medido_en.desc())
        .limit(VENTANA_LECTURAS)
        .all()
    )
    lecturas_historicas.reverse()

    puntos = []
    for l in lecturas_historicas:
        calculo = calcular_nivel(
            distancia_cm=float(l.distancia_cm),
            altura_cono_m=float(silo.altura_cono_m),
            altura_cilindro_m=float(silo.altura_cilindro_m),
            diametro_m=float(silo.diametro_m),
            densidad_kg_m3=float(silo.densidad_alimento_kg_m3),
            altura_zona_ciega_cm=float(silo.altura_zona_ciega_cm),
        )
        puntos.append((l.medido_en, calculo["kg_estimados"]))

    proyeccion = calcular_proyeccion(puntos)

    return {
        "origen": {
            "sistema": "silos-backend",
            "version_payload": "1.0",
            "enviado_en": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lectura_id": lectura.id,
        },
        "silo": {
            "device_id": sensor.device_id,
            "silo_codigo": silo.codigo,
            "silo_nombre": silo.nombre,
            "finca_nombre": silo.finca.nombre,
            "capacidad_kg": float(silo.capacidad_kg),
            "densidad_alimento_kg_m3": float(silo.densidad_alimento_kg_m3),
        },
        "lectura_cruda": {
            "distancia_cm": float(lectura.distancia_cm),
            "voltaje_bateria": float(lectura.voltaje_bateria),
            "medido_en": lectura.medido_en.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "nivel_calculado": {
            "altura_alimento_m": nivel["altura_alimento_m"],
            "volumen_m3": nivel["volumen_m3"],
            "porcentaje": nivel["porcentaje"],
            "kg_estimados": nivel["kg_estimados"],
        },
        "proyeccion": {
            "consumo_diario_promedio_kg": proyeccion["consumo_diario_promedio_kg"],
            "dias_restantes": proyeccion["dias_restantes"],
            "confiable": proyeccion["confiable"],
            "mensaje": proyeccion["mensaje"],
        },
    }


def enviar_webhook_lectura(lectura_id: int) -> None:
    if not settings.n8n_webhook_url:
        return

    db = SessionLocal()
    try:
        lectura = db.query(Lectura).filter(Lectura.id == lectura_id).first()
        if lectura is None:
            return
        sensor = db.query(Sensor).filter(Sensor.id == lectura.sensor_id).first()
        if sensor is None:
            return
        silo = db.query(Silo).filter(Silo.id == sensor.silo_id).first()
        if silo is None:
            return

        payload = _construir_payload(db, lectura, sensor, silo)

        try:
            httpx.post(settings.n8n_webhook_url, json=payload, timeout=10.0)
        except httpx.HTTPError as e:
            logger.warning("Fallo al enviar webhook de lectura %s a n8n: %s", lectura_id, e)
    finally:
        db.close()
