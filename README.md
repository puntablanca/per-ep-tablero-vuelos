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
