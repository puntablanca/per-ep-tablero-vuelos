"""Tablero de vuelos.

Hoy tiene una sola vista: la posición de los vuelos que se están siguiendo.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# El `.env` ya lo cargó `app/__init__.py`, que corre antes de esto.
from app.opensky import obtener_vuelos

# Sin esto los `log.warning` de opensky.py no salen: uvicorn configura su propio
# logger y el resto del arbol se queda en WARNING pero sin manejador que escriba.
logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")

BASE = Path(__file__).parent
app = FastAPI(title="Tablero de vuelos", version="0.4.1")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
plantillas = Jinja2Templates(directory=str(BASE / "templates"))

# La hora de carga la resuelve la plantilla sola, no la vista. Así cualquier vista
# nueva la tiene sin acordarse de pasarla, y la barra nunca queda a medias.
plantillas.env.globals["hora_de_carga"] = lambda: time.strftime("%H:%M:%S")


def _hora(momento: float | None) -> str | None:
    """La marca de tiempo de OpenSky en hora local, o None si no vino."""
    return time.strftime("%H:%M:%S", time.localtime(momento)) if momento else None


def _antiguedad(momento: float | None) -> int | None:
    """Cuántos segundos tenía el dato cuando se sirvió esta página."""
    return round(time.time() - momento) if momento else None


@app.get("/salud")
def salud() -> dict:
    return {"estado": "ok", "version": app.version}


@app.get("/api/vuelos")
def api_vuelos(limite: int = 40) -> dict:
    lote = obtener_vuelos(limite)
    return {
        "fuente": lote.fuente,
        "total": len(lote.vuelos),
        # De cuándo es el dato, no de cuándo se pidió. `null` en el respaldo, que
        # no tiene hora porque es una instantánea guardada.
        "momento": lote.momento,
        "hora": _hora(lote.momento),
        "antiguedad_s": _antiguedad(lote.momento),
        "vuelos": lote.vuelos,
    }


@app.get("/")
def raiz() -> RedirectResponse:
    return RedirectResponse("/posicion")


@app.get("/posicion")
def posicion(request: Request):
    lote = obtener_vuelos()
    sin_senal = [v for v in lote.vuelos if v["en_tierra"]]
    return plantillas.TemplateResponse(
        request=request,
        name="posicion.html",
        context={
            "vuelos": lote.vuelos,
            "fuente": lote.fuente,
            "sin_senal": len(sin_senal),
            "hora_dato": _hora(lote.momento),
            "antiguedad_s": _antiguedad(lote.momento),
        },
    )
