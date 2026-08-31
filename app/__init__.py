"""Tablero de vuelos.

El `.env` se carga acá, en el paquete, y no en `main.py`. La razón es concreta:
`opensky.py` lee las credenciales del entorno, y si la carga viviera en `main.py`
cualquier otra entrada al código (un script, una prueba que importe solo
`app.opensky`, un comando de mantenimiento) se quedaría sin credenciales y caería
al nivel anónimo **sin decir nada**. Acá corre para todos.

La ruta va explícita porque `load_dotenv()` sin argumentos busca el archivo subiendo
desde el directorio de quien llama, y eso depende de dónde se arrancó el proceso.
Si no hay `.env`, no pasa nada: la aplicación usa el nivel anónimo de OpenSky.
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
