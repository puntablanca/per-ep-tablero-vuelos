"""Agrupación de vuelos por aerolínea.

Un renglón por vuelo no responde la pregunta que operaciones hace todas las
mañanas, que es cuál aerolínea está peor. Este módulo convierte la lista de
vuelos en una lista de aerolíneas, ordenada por la que hay que mirar primero.

Es una función pura a propósito: no pide datos, no sabe de HTTP y no toca el
reloj. Recibe vuelos y devuelve filas. Así se prueba el caso raro sin esperar a
que el cielo lo produzca, y la vista se queda siendo solo la vista.
"""
from __future__ import annotations

from collections import defaultdict


def codigo_de(callsign: str) -> str:
    """Las tres primeras letras del callsign, que es la aerolínea.

    `AAL2314` es `AAL`. La regla la dio operaciones y tiene una consecuencia
    conocida: las matrículas privadas mexicanas empiezan con XA o XB, así que
    cada avión particular queda como su propia "aerolínea" de un solo vuelo.
    """
    return callsign.strip()[:3].upper()


def agrupar_por_aerolinea(vuelos: list[dict]) -> list[dict]:
    """Una fila por aerolínea, ordenada por la que tiene más vuelos en tierra.

    Cada fila trae el código, cuántos vuelos se le siguen, cuántos están en
    tierra y la altitud promedio de los que van en ruta. El promedio es None
    cuando la aerolínea no tiene ninguno volando: cero metros sería un dato, y
    lo que pasa ahí es que no hay dato.
    """
    grupos: dict[str, list[dict]] = defaultdict(list)
    for v in vuelos:
        grupos[codigo_de(v["callsign"])].append(v)

    filas = []
    for codigo, dentro in grupos.items():
        # Los que están en tierra reportan altitud 0 y hundirían el promedio:
        # la columna diría que la flota vuela más bajo de lo que vuela.
        en_ruta = [v for v in dentro if not v["en_tierra"]]
        filas.append({
            "codigo": codigo,
            "total": len(dentro),
            "en_tierra": len(dentro) - len(en_ruta),
            "altitud_promedio": (
                sum(v["altitud"] for v in en_ruta) / len(en_ruta) if en_ruta else None
            ),
        })

    # Primero la que tiene más vuelos en tierra, que es la pregunta. Los dos
    # desempates son para que el orden no dependa del azar: sin ellos, dos
    # aerolíneas iguales saldrían en el orden en que llegaron del feed y la
    # tabla cambiaría de forma entre dos recargas sin que cambie nada.
    filas.sort(key=lambda f: (-f["en_tierra"], -f["total"], f["codigo"]))
    return filas
