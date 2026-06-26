"""
Proyección de días restantes a partir de la tendencia reciente de consumo.

A propósito NO usa machine learning: es una regresión lineal simple sobre
los kg estimados de las últimas lecturas. Esto se decidió explícitamente
porque el problema (cuántos días quedan al ritmo de consumo actual) no
necesita un modelo entrenado, y agregar uno solo suma complejidad sin
mejorar la respuesta real que necesita el negocio.
"""

from datetime import datetime

MIN_LECTURAS = 3
MIN_HORAS_VENTANA = 12.0


def calcular_proyeccion(puntos: list[tuple[datetime, float]]) -> dict:
    """
    puntos: lista de (medido_en, kg_estimados), ordenada de más antigua a más reciente.
    """
    if len(puntos) < MIN_LECTURAS:
        return {
            "consumo_diario_promedio_kg": 0.0,
            "dias_restantes": None,
            "confiable": False,
            "mensaje": "Todavía no hay suficientes lecturas para proyectar (mínimo 3).",
        }

    t0 = puntos[0][0]
    xs = [(p[0] - t0).total_seconds() / 3600 for p in puntos]  # horas desde la primera lectura
    ys = [p[1] for p in puntos]

    horas_ventana = xs[-1] - xs[0]
    if horas_ventana < MIN_HORAS_VENTANA:
        return {
            "consumo_diario_promedio_kg": 0.0,
            "dias_restantes": None,
            "confiable": False,
            "mensaje": f"La ventana de datos es muy corta ({horas_ventana:.1f}h, se necesitan {MIN_HORAS_VENTANA:.0f}h).",
        }

    n = len(xs)
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    sum_xx = sum(x * x for x in xs)

    denom = n * sum_xx - sum_x**2
    if denom == 0:
        return {
            "consumo_diario_promedio_kg": 0.0,
            "dias_restantes": None,
            "confiable": False,
            "mensaje": "No se pudo calcular una tendencia con estos datos.",
        }

    pendiente_kg_por_hora = (n * sum_xy - sum_x * sum_y) / denom  # negativa si está consumiendo
    kg_actual = ys[-1]

    if pendiente_kg_por_hora >= 0:
        return {
            "consumo_diario_promedio_kg": 0.0,
            "dias_restantes": None,
            "confiable": False,
            "mensaje": "El nivel no muestra una tendencia de consumo (puede que se haya rellenado recientemente).",
        }

    consumo_diario_kg = -pendiente_kg_por_hora * 24
    horas_restantes = kg_actual / (-pendiente_kg_por_hora)
    dias_restantes = round(horas_restantes / 24, 1)

    return {
        "consumo_diario_promedio_kg": round(consumo_diario_kg, 1),
        "dias_restantes": dias_restantes,
        "confiable": True,
        "mensaje": "Proyección calculada con regresión lineal sobre el historial reciente.",
    }
