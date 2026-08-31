"""Fuente de datos de vuelos.

Tres niveles, y se intentan en este orden:

1. **OpenSky con credenciales**, si hay `OPENSKY_CLIENT_ID` y `OPENSKY_CLIENT_SECRET`
   en el entorno. Son 4.000 créditos al día.
2. **OpenSky anónimo**, si no hay credenciales o si las que hay no sirven. Son 400
   créditos al día y **se cuentan por dirección IP**, así que una oficina entera
   comparte los mismos 400.
3. **Un archivo local**, si nada de lo anterior contestó.

Los tres niveles importan. El respaldo existe porque en un salón de clase la red
falla, y una demo que depende de internet es una demo que no se puede dar. Y el nivel
anónimo existe porque este repositorio es público: quien lo clone sin credenciales
tiene que poder correrlo igual.

OpenSky ya no acepta usuario y contraseña: solo el flujo *client credentials* de
OAuth2. Las credenciales se sacan de la página de cuenta de OpenSky, creando un
cliente de API.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import NamedTuple

import httpx

log = logging.getLogger("opensky")

RESPALDO = Path(__file__).parent / "static" / "vuelos-respaldo.json"
URL = "https://opensky-network.org/api/states/all"
URL_TOKEN = (
    "https://auth.opensky-network.org/auth/realms/opensky-network"
    "/protocol/openid-connect/token"
)
# Configurable por entorno: en una maquina de escritorio 8 segundos sobran, y desde
# un servicio en la nube el mismo destino puede tardar bastante mas o no contestar.
# Poder subirlo sin tocar el codigo es lo que permite distinguir "lento" de "bloqueado".
TIMEOUT = float(os.getenv("OPENSKY_TIMEOUT", "8"))

# El token de OpenSky vive 30 minutos. Se renueva con margen para no llegar justo
# y comerse un 401 en medio de una demostración.
MARGEN_TOKEN = 120.0

# El token se guarda entre llamadas: pedir uno nuevo en cada carga de la página
# agrega casi un segundo y no hace falta.
_token_guardado: dict = {"valor": None, "vence": 0.0}

# Lo que OpenSky dice que queda de presupuesto, de la cabecera de la última
# respuesta. Es None hasta que haya una llamada que la traiga.
credito_restante: int | None = None


class Lote(NamedTuple):
    """Lo que devuelve una consulta de vuelos.

    `momento` es la marca de tiempo que OpenSky manda con el lote, en segundos epoch.
    **Es None cuando los datos salieron del respaldo local**, que no tiene hora, y esa
    ausencia es información: significa que lo que se está viendo no es en vivo.

    No es la hora en que se pidió el dato, es la hora en que OpenSky lo consolidó. Las
    dos se separan por unos segundos, y saber cuántos es justamente el punto.
    """

    vuelos: list[dict]
    fuente: str
    momento: float | None


def credenciales() -> tuple[str, str] | None:
    """Las credenciales del entorno, o None si falta alguna de las dos."""
    cliente = os.getenv("OPENSKY_CLIENT_ID", "").strip()
    secreto = os.getenv("OPENSKY_CLIENT_SECRET", "").strip()
    return (cliente, secreto) if cliente and secreto else None


def _token(forzar: bool = False) -> str | None:
    """Un token válido, del caché si todavía sirve. None si no se pudo conseguir."""
    creds = credenciales()
    if creds is None:
        return None

    ahora = time.time()
    if not forzar and _token_guardado["valor"] and _token_guardado["vence"] > ahora:
        return _token_guardado["valor"]

    cliente, secreto = creds
    try:
        r = httpx.post(
            URL_TOKEN,
            data={
                "grant_type": "client_credentials",
                "client_id": cliente,
                "client_secret": secreto,
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        datos = r.json()
    except Exception as e:
        # Credenciales malas, sin red, o el servidor de auth caído. No es fatal:
        # quien llama sigue con el nivel anónimo. Pero se dice, porque un agente que
        # degrada en silencio es imposible de diagnosticar desde afuera: eso costó
        # una tarde el 2026-08-31, con el servicio en Cloud Run cayendo al respaldo
        # sin una sola línea en los logs que explicara por qué.
        log.warning("no se pudo obtener el token de OpenSky: %s: %s",
                    type(e).__name__, e)
        return None

    _token_guardado["valor"] = datos.get("access_token")
    _token_guardado["vence"] = ahora + max(float(datos.get("expires_in", 1800)) - MARGEN_TOKEN, 0.0)
    return _token_guardado["valor"]


def _anotar_credito(r: httpx.Response) -> None:
    global credito_restante
    queda = r.headers.get("x-rate-limit-remaining")
    if queda is not None:
        try:
            credito_restante = int(queda)
        except ValueError:
            pass


def _pedir_estados() -> tuple[list, str, float | None]:
    """Los estados crudos, con qué credencial se consiguieron, y de cuándo son."""
    token = _token()
    if token:
        r = httpx.get(URL, headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)
        # El token vive 30 minutos y OpenSky contesta 401 cuando vence. Se pide
        # otro y se reintenta una sola vez.
        if r.status_code == 401:
            token = _token(forzar=True)
            if token:
                r = httpx.get(
                    URL, headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT
                )
        if r.status_code == 200:
            _anotar_credito(r)
            datos = r.json()
            return datos.get("states") or [], "opensky", datos.get("time")
        # Con credenciales que no sirven conviene intentar anónimo antes de
        # rendirse: 400 créditos son mejores que ninguno.
        log.warning("OpenSky autenticado devolvió %s, se intenta anónimo: %s",
                    r.status_code, r.text[:200])

    r = httpx.get(URL, timeout=TIMEOUT)
    r.raise_for_status()
    _anotar_credito(r)
    datos = r.json()
    return datos.get("states") or [], "opensky-anonimo", datos.get("time")


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


def obtener_vuelos(limite: int = 40) -> Lote:
    """Los vuelos, de dónde salieron, y de cuándo es el dato.

    La fuente es 'opensky', 'opensky-anonimo' o 'respaldo'.
    """
    try:
        estados, fuente, momento = _pedir_estados()
        vuelos = [v for v in (_normalizar(e) for e in estados) if v]
        if vuelos:
            return Lote(vuelos[:limite], fuente, momento)
        log.warning("OpenSky contestó pero sin vuelos usables: %s estados crudos",
                    len(estados))
    except Exception as e:
        # Nunca se propaga: el tablero tiene que responder igual. Pero se registra
        # el motivo, que es la diferencia entre degradar y fallar a ciegas.
        log.warning("cayendo al respaldo local: %s: %s", type(e).__name__, e)
    return Lote(leer_respaldo()[:limite], "respaldo", None)
