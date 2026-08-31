# Tablero de vuelos

Aplicación de ejemplo para la Sesión 3 del programa **De Espectadores a Protagonistas**.
Ya corre: el trabajo de la sesión es agregarle una vista, no construirla desde cero.

## Correrla

### Con Python, para desarrollar

Un entorno propio, para no mezclar con lo que tenga instalado en el sistema:

```
python3 -m venv .venv
source .venv/bin/activate          # en Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

Y a correr. El `--reload` recarga sola cuando guarda un archivo:

```
uvicorn app.main:app --reload --port 8080
```

Queda en <http://localhost:8080/posicion>.

**Si el 8080 está ocupado**, y pasa seguido, cambie el número:

```
uvicorn app.main:app --reload --port 8099
```

### Con contenedor, que es lo que usa el pipeline

```
docker compose up --build
```

También en <http://localhost:8080/posicion>. Para usar otro puerto de la máquina:

```
PUERTO=8099 docker compose up --build
```

Compose lee el `.env` de esta carpeta, así que las credenciales y la zona horaria
entran solas. Para dejarlo corriendo de fondo agregue `-d`, y para bajarlo:

```
docker compose down
```

## Probarla

```
pytest -q
```

Son 12 pruebas y **ninguna sale a la red**: el cliente de OpenSky se reemplaza por uno
falso. Si alguna falla por no encontrar el paquete `app`, es que se corrió desde otra
carpeta: el `pyproject.toml` trae `pythonpath = ["."]` y hay que estar en la raíz.

## Qué hay adentro

| Ruta | Qué hace |
| --- | --- |
| `/posicion` | La vista que ya existe: un renglón por vuelo |
| `/api/vuelos` | Los mismos datos en JSON |
| `/salud` | Para que el pipeline sepa si el servicio está arriba |

## De dónde salen los datos

Tres niveles, y se intentan en ese orden. **La aplicación corre en los tres**, así que quien
clone esto sin credenciales no tiene nada que configurar.

| `fuente` | Cuándo | Presupuesto |
| --- | --- | --- |
| `opensky` | Hay credenciales en el entorno y sirven | **4.000 créditos al día** |
| `opensky-anonimo` | No hay credenciales, o las que hay no sirven | 400 créditos al día, **contados por dirección IP** |
| `respaldo` | Nada de lo anterior contestó | Una instantánea local, sin límite |

El campo `fuente` de `/api/vuelos` dice cuál se usó, y también sale en la esquina de la vista.

**Lo de la dirección IP importa.** En el nivel anónimo los 400 créditos se cuentan por IP, así
que una oficina entera detrás del mismo NAT comparte un solo presupuesto. Cada carga de la
página cuesta 4 créditos: son unas 100 cargas al día entre todos, y cuando se agotan la
aplicación cae al respaldo **sin avisar**. Con credenciales el mismo cálculo da unas 1.000.

### Poner credenciales

```
cp .env.example .env
```

Y llenar los dos valores. Salen de la página de cuenta de OpenSky, en la sección de clientes
de API: <https://opensky-network.org/my-opensky/account>. Ahí hay un botón que descarga un
`credentials.json` con los dos, que es la manera segura de copiarlos sin cortarlos.

```
OPENSKY_CLIENT_ID=su-usuario-api-client
OPENSKY_CLIENT_SECRET=...
```

Dos cosas que cuestan tiempo si no se saben:

- **OpenSky ya no acepta usuario y contraseña.** Solo el flujo *client credentials* de OAuth2.
- **El secreto son 32 caracteres.** Si le quedó más corto, se cortó al copiar, y el error que
  devuelve el servidor es `unauthorized_client`, que suena a que el cliente está mal cuando en
  realidad el cliente está bien y el secreto no.

`.env` está en el `.gitignore` y no se sube nunca. `.env.example` sí se sube: es el que le dice
al que clona qué variables hacen falta.

## El trabajo de la sesión

Está en [`REQUERIMIENTO.md`](REQUERIMIENTO.md).
