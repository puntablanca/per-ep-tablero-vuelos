# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado según [SemVer](https://semver.org/lang/es/).

## [0.1.1] - 2026-08-31

### Agregado
- Autenticación con OpenSky por OAuth2 *client credentials*, con las credenciales en
  `OPENSKY_CLIENT_ID` y `OPENSKY_CLIENT_SECRET`. Sube el presupuesto de 400 créditos
  diarios a 4.000.
- `.env.example` con las dos variables y de dónde salen.
- El campo `fuente` distingue ahora `opensky` de `opensky-anonimo`, para saber si las
  credenciales se están usando de verdad.

### Cambiado
- El `.env` se carga en `app/__init__.py` y no en `app/main.py`: así cualquier entrada
  al código tiene las credenciales, no solo la aplicación web.

## [0.1.0] - 2026-08-30

### Agregado
- Vista de posición de vuelos, con el conteo de los que están en tierra.
- `GET /api/vuelos` y `GET /salud`.
- Respaldo local de datos, para trabajar sin red.
