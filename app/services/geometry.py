"""
Convierte una distancia medida por el sensor ultrasónico en volumen y
porcentaje real de alimento, respetando que un silo NO es un cilindro
simple: tiene una zona cilíndrica (lineal) y una zona cónica (no lineal),
tal como se definió en el diseño del piloto.
"""

import math


def calcular_nivel(
    distancia_cm: float,
    altura_cono_m: float,
    altura_cilindro_m: float,
    diametro_m: float,
    densidad_kg_m3: float,
    altura_zona_ciega_cm: float,
    offset_sensor_cm: float = 0.0,
) -> dict:
    radio_m = diametro_m / 2
    altura_util_m = altura_cono_m + altura_cilindro_m

    cono_vol_m3 = (1 / 3) * math.pi * radio_m**2 * altura_cono_m
    cilindro_vol_m3 = math.pi * radio_m**2 * altura_cilindro_m
    total_vol_m3 = cono_vol_m3 + cilindro_vol_m3

    if distancia_cm < altura_zona_ciega_cm:
        # el alimento está más cerca que la zona ciega del sensor: tratamos
        # como silo lleno, no como error, porque es la lectura esperada
        # cuando acaban de hacer el refill
        distancia_cm = altura_zona_ciega_cm

    distancia_libre_m = distancia_cm / 100
    altura_alimento_m = altura_util_m - distancia_libre_m
    altura_alimento_m = max(0.0, min(altura_alimento_m, altura_util_m))

    # Zona ciega geométrica por sensor descentrado. En un cono recto el radio
    # a una altura h medida desde el vértice es r(h) = radio_m * h / altura_cono_m.
    # Con el sensor a offset_m del eje, la línea vertical de medición choca con
    # la pared del cono a la altura en que r(h) == offset_m. Por debajo de esa
    # altura el sensor ya no ve la superficie real del alimento. El número no
    # se modifica: solo se avisa que la lectura entra en zona dudosa.
    advertencia = None
    offset_m = max(0.0, offset_sensor_cm or 0.0) / 100
    if offset_m > 0 and altura_cono_m > 0 and radio_m > 0:
        altura_limite_vision_m = min(altura_cono_m, altura_cono_m * offset_m / radio_m)
        if altura_alimento_m < altura_limite_vision_m:
            advertencia = (
                f"Nivel por debajo de la zona que alcanza a ver el sensor "
                f"(montado a {offset_sensor_cm:.0f} cm del eje central): la pared "
                f"del cono tapa la medición, el valor puede no ser exacto."
            )

    if altura_alimento_m <= altura_cono_m:
        # el alimento todavía no llena el cono: el volumen ocupado crece
        # con el cubo de la altura (es un cono geométricamente similar
        # al cono completo, no una proporción lineal)
        proporcion = altura_alimento_m / altura_cono_m if altura_cono_m > 0 else 0
        vol_m3 = cono_vol_m3 * (proporcion**3)
    else:
        altura_cilindro_llena_m = altura_alimento_m - altura_cono_m
        proporcion_cilindro = (
            altura_cilindro_llena_m / altura_cilindro_m if altura_cilindro_m > 0 else 0
        )
        vol_m3 = cono_vol_m3 + cilindro_vol_m3 * proporcion_cilindro

    porcentaje = (vol_m3 / total_vol_m3 * 100) if total_vol_m3 > 0 else 0
    kg_estimados = vol_m3 * densidad_kg_m3

    return {
        "altura_alimento_m": round(altura_alimento_m, 3),
        "volumen_m3": round(vol_m3, 3),
        "porcentaje": round(min(porcentaje, 100.0), 2),
        "kg_estimados": round(kg_estimados, 1),
        "advertencia": advertencia,
    }


def calcular_distancia_desde_porcentaje(
    porcentaje: float,
    altura_cono_m: float,
    altura_cilindro_m: float,
    diametro_m: float,
) -> float:
    """
    Inversa de calcular_nivel: dado un porcentaje de volumen deseado,
    devuelve la distancia (cm) que el sensor reportaría. Se usa solo para
    generar datos simulados realistas, nunca para procesar lecturas reales.
    """
    radio_m = diametro_m / 2
    altura_util_m = altura_cono_m + altura_cilindro_m

    cono_vol_m3 = (1 / 3) * math.pi * radio_m**2 * altura_cono_m
    cilindro_vol_m3 = math.pi * radio_m**2 * altura_cilindro_m
    total_vol_m3 = cono_vol_m3 + cilindro_vol_m3

    porcentaje = max(0.0, min(100.0, porcentaje))
    vol_objetivo_m3 = (porcentaje / 100) * total_vol_m3

    if vol_objetivo_m3 <= cono_vol_m3:
        proporcion = (vol_objetivo_m3 / cono_vol_m3) ** (1 / 3) if cono_vol_m3 > 0 else 0
        altura_alimento_m = altura_cono_m * proporcion
    else:
        vol_restante = vol_objetivo_m3 - cono_vol_m3
        proporcion_cilindro = vol_restante / cilindro_vol_m3 if cilindro_vol_m3 > 0 else 0
        altura_alimento_m = altura_cono_m + altura_cilindro_m * proporcion_cilindro

    distancia_libre_m = altura_util_m - altura_alimento_m
    return round(max(0.0, distancia_libre_m) * 100, 2)
