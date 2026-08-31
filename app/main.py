"""Tablero de vuelos.

Hoy tiene una sola vista: la posición de los vuelos que se están siguiendo.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# El `.env` ya lo cargó `app/__init__.py`, que corre antes de esto.
from app.opensky import obtener_vuelos

BASE = Path(__file__).parent
app = FastAPI(title="Tablero de vuelos", version="0.1.1")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
plantillas = Jinja2Templates(directory=str(BASE / "templates"))


@app.get("/salud")
def salud() -> dict:
    return {"estado": "ok", "version": app.version}


@app.get("/api/vuelos")
def api_vuelos(limite: int = 40) -> dict:
    vuelos, fuente = obtener_vuelos(limite)
    return {"fuente": fuente, "total": len(vuelos), "vuelos": vuelos}


@app.get("/")
def raiz() -> RedirectResponse:
    return RedirectResponse("/posicion")


@app.get("/posicion")
def posicion(request: Request):
    vuelos, fuente = obtener_vuelos()
    sin_senal = [v for v in vuelos if v["en_tierra"]]
    return plantillas.TemplateResponse(
        request=request,
        name="posicion.html",
        context={"vuelos": vuelos, "fuente": fuente, "sin_senal": len(sin_senal)},
    )
