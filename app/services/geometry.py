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
    }
