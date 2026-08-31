# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado según [SemVer](https://semver.org/lang/es/).

## [0.3.1] - 2026-08-31

### Corregido
- La degradación a un nivel más bajo **ahora se registra**. Antes el `except` se tragaba
  el motivo y el servicio caía al respaldo sin una línea que explicara por qué, lo que
  hizo imposible diagnosticar el primer despliegue a Cloud Run desde afuera.

## [0.3.0] - 2026-08-31

### Agregado
- `diagrams/` con tres vistas en `.drawio` sin comprimir y su `.png` al lado: componentes
  (N0), tecnologías (N1), y los tres entornos con su cruce con las ramas.
- `scripts/desplegar.sh`, que **se niega a desplegar con el árbol sucio** y etiqueta la
  imagen con el commit en vez de `latest`.
- El CI verifica que la suite haya corrido de verdad: cero salteadas y una cuenta mínima.
- `tests/test_centinela.py`, que mantiene ese mínimo honesto y revisa que el workflow siga
  sin secretos.
- README como guía completa de replicación: prerrequisitos, clonar, sacar las credenciales
  de OpenSky paso a paso, correr en los tres niveles, probar y desplegar.

### Quitado
- `REQUERIMIENTO.md` sale del repositorio. Un pedido de negocio no nace en el repositorio
  de quien lo va a implementar: vive con el material de la sesión.

## [0.2.0] - 2026-08-31

### Agregado
- La barra del tablero muestra **de cuándo es el dato**: la hora que OpenSky trae con el
  lote, su antigüedad, y la hora en que se cargó la página. Sin la última, una pestaña
  vieja parece en vivo.
- `GET /api/vuelos` devuelve `momento`, `hora` y `antiguedad_s`.
- El puerto de la máquina se puede cambiar con `PUERTO=...` al levantar el contenedor.
- La zona horaria del contenedor se toma de `TZ`: sin eso corre en UTC y la hora sale
  corrida respecto al reloj de quien mira.

### Cambiado
- `obtener_vuelos()` devuelve un `Lote` con `vuelos`, `fuente` y `momento`, en vez de una
  tupla de dos. Con tres valores una tupla suelta se vuelve adivinanza.
- Cuando la fuente es el respaldo, la hora va en `null` y la pantalla lo dice. **No se le
  inventa una hora**: que falte es la información.

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
