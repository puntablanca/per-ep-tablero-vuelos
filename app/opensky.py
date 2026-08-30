"""Fuente de datos de vuelos.

Intenta OpenSky y, si no hay red o la API responde mal, cae a un archivo local.
El respaldo existe a propósito: en un salón de clase la red falla, y una demo que
depende de internet es una demo que no se puede dar.
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx

RESPALDO = Path(__file__).parent / "static" / "vuelos-respaldo.json"
URL = "https://opensky-network.org/api/states/all"
TIMEOUT = 4.0


def _normalizar(estado: list) -> dict | None:
    """Un estado de OpenSky es una lista posicional. Acá se le ponen nombres."""
    callsign = (estado[1] or "").strip()
    if not callsign or estado[5] is None or estado[6] is None:
        return None
    return {
        "callsign": callsign,
        "pais": estado[2] or "desconocido",
        "longitud": estado[5],
        "latitud": estado[6],
        "altitud": estado[7] or 0,
        "velocidad": estado[9] or 0,
        "en_tierra": bool(estado[8]),
    }


def leer_respaldo() -> list[dict]:
    with RESPALDO.open(encoding="utf-8") as f:
        return json.load(f)["vuelos"]


def obtener_vuelos(limite: int = 40) -> tuple[list[dict], str]:
    """Devuelve los vuelos y de dónde salieron: 'opensky' o 'respaldo'."""
    try:
        r = httpx.get(URL, timeout=TIMEOUT)
        r.raise_for_status()
        estados = r.json().get("states") or []
        vuelos = [v for v in (_normalizar(e) for e in estados) if v]
        if vuelos:
            return vuelos[:limite], "opensky"
    except Exception:
        pass
    return leer_respaldo()[:limite], "respaldo"
