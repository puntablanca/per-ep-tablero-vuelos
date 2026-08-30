# Tablero de vuelos

Aplicación de ejemplo para la Sesión 3 del programa **De Espectadores a Protagonistas**.
Ya corre: el trabajo de la sesión es agregarle una vista, no construirla desde cero.

## Correrla

```
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8080
```

O con contenedor, que es lo que usa el pipeline:

```
docker compose up --build
```

Queda en <http://localhost:8080>.

## Probarla

```
pytest -q
```

## Qué hay adentro

| Ruta | Qué hace |
| --- | --- |
| `/posicion` | La vista que ya existe: un renglón por vuelo |
| `/api/vuelos` | Los mismos datos en JSON |
| `/salud` | Para que el pipeline sepa si el servicio está arriba |

Los datos salen de OpenSky. **Si no hay red, cae solo a una instantánea local**, así que la
aplicación corre igual sin internet. El campo `fuente` de la respuesta dice de dónde vinieron.

## El trabajo de la sesión

Está en [`REQUERIMIENTO.md`](REQUERIMIENTO.md).
