# Tablero de vuelos

Aplicación de ejemplo para la Sesión 3 del programa **De Espectadores a Protagonistas**,
de Punta Blanca. Muestra la posición de vuelos en tiempo real con datos de OpenSky.

**Ya corre.** El trabajo de la sesión es agregarle una vista, no construirla desde cero,
que es lo que pasa en un equipo de verdad. El pedido no vive acá: viene con el material de
la sesión, como le llegaría de operaciones en un equipo real.

---

## Antes de empezar

| Hace falta | Para qué | Obligatorio |
| --- | --- | --- |
| **Git** | Clonar el repositorio | Sí |
| **Python 3.12** | Correr la aplicación y las pruebas | Sí |
| **Una cuenta de OpenSky** | Sacar diez veces más datos al día | No, pero conviene |
| **Docker** | Correr la misma imagen que va a producción | No para la práctica |
| **Cuenta de Google Cloud** | Desplegar | No para la práctica |

Sin cuenta de OpenSky la aplicación corre igual: usa el nivel anónimo, y si ese también
falla usa una instantánea local. Nunca se queda sin datos.

## Paso 1 · Clonar

```
git clone https://github.com/puntablanca/per-ep-tablero-vuelos.git
cd per-ep-tablero-vuelos
```

## Paso 2 · Las credenciales de OpenSky

Este paso se puede saltar, pero cuesta tres minutos y multiplica por diez el
presupuesto de datos.

1. **Cree una cuenta**, si no tiene, en <https://opensky-network.org/index.php?option=com_users&view=registration>.
2. Entre a su cuenta y vaya a **<https://opensky-network.org/my-opensky/account>**.
3. En la sección de **clientes de API**, cree uno. El `client_id` va a quedar con la
   forma `su-usuario-api-client`.
4. **Descargue el `credentials.json`** que le ofrece la página. Hágalo por ahí y no
   copiando a mano: el secreto son 32 caracteres y es fácil cortarlo al seleccionar.
5. Copie la plantilla y llene los dos valores:

   ```
   cp .env.example .env
   ```

   ```
   OPENSKY_CLIENT_ID=su-usuario-api-client
   OPENSKY_CLIENT_SECRET=los32caracteresdelcredentialsjson
   ```

`.env` está en el `.gitignore` y no se sube nunca. `.env.example` sí se sube: es el que
le dice al que clona qué variables hacen falta.

### Dos cosas que cuestan tiempo si no se saben

- **OpenSky ya no acepta usuario y contraseña.** Solo el flujo *client credentials* de
  OAuth2. Si pone acá su usuario de la web, no funciona.
- **El secreto son 32 caracteres.** Si le quedó más corto, se cortó al copiar. El error
  que devuelve el servidor es `unauthorized_client`, que suena a que el cliente está mal
  registrado cuando en realidad el cliente está bien y el secreto no. Para distinguirlos:
  `invalid_client` es "ese cliente no existe", `unauthorized_client` es "el cliente
  existe, el secreto no coincide".

## Paso 3 · Correrla

Hay **tres maneras**, y no son alternativas: son tres niveles que prueban cosas distintas.
El detalle de por qué está en [Los tres entornos](#los-tres-entornos).

| Nivel | Cómo | Queda en |
| --- | --- | --- |
| **1 · Local** | `uvicorn app.main:app --reload --port 8080` | `localhost:8080` |
| **2 · Contenedor** | `docker compose up --build` | `localhost:8080` |
| **3 · Nube** | `gcloud run services proxy ...` | `localhost:8097` |

### 1 · Con Python, para desarrollar

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

### 2 · Con contenedor, que es lo que usa el pipeline

```
docker compose up --build
```

También en <http://localhost:8080/posicion>. Para usar otro puerto de la máquina:

```
PUERTO=8099 docker compose up --build
```

Compose lee el `.env` de esta carpeta, así que las credenciales y la zona horaria entran
solas. Agregue `-d` para dejarlo de fondo, y `docker compose down` para bajarlo.

**Ponga su zona horaria en el `.env`.** Sin eso el contenedor corre en UTC y la hora que
muestra el tablero sale corrida respecto a su reloj:

```
TZ=America/Mexico_City
```

### 3 · El servicio de la nube, en su máquina

El servicio desplegado **no es público**: no hay una dirección que se pueda abrir en el
navegador. Se llega con un túnel autenticado, que firma cada petición con su identidad de
`gcloud`:

```
gcloud run services proxy tablero-vuelos \
  --region=us-central1 \
  --project=per-ep-tablero-vuelos \
  --port=8097
```

Y el tablero queda en <http://localhost:8097/posicion>.

Tres cosas de este comando:

- **Se queda corriendo.** Mientras el proceso viva, el túnel vive. Se cierra con `Ctrl+C`.
- **No hay contraseña ni llave que copiar.** Usa su credencial de `gcloud`, que es la que
  tiene el `run.invoker`. Si expira, `gcloud auth login`.
- **El puerto va en 8097 y no en 8080** para no chocar con la copia local ni con el
  contenedor. Puede correr los tres a la vez, cada uno en su puerto, y comparar.

**Lo que va a ver ahí es la instantánea local, no vuelos en vivo.** No es una falla del
despliegue: OpenSky no es alcanzable desde Cloud Run, y la barra lo dice en ámbar. El
detalle está más abajo, en [OpenSky no es alcanzable desde Cloud Run](#opensky-no-es-alcanzable-desde-cloud-run).

## Paso 4 · Probarla

```
pytest -q
```

Son 15 pruebas y **ninguna sale a la red**: el cliente de OpenSky se reemplaza por uno
falso. Si alguna falla por no encontrar el paquete `app`, es que se corrió desde otra
carpeta: el `pyproject.toml` trae `pythonpath = ["."]` y hay que estar en la raíz.

## Qué está viendo

| Ruta | Qué hace |
| --- | --- |
| `/posicion` | La vista que ya existe: un renglón por vuelo |
| `/api/vuelos` | Los mismos datos en JSON, con la hora del dato |
| `/salud` | Para que el pipeline sepa si el servicio está arriba |

La tabla muestra **40 vuelos**, que son los primeros que devuelve OpenSky, sin ordenar y
sin filtrar. OpenSky manda unos trece mil en cada consulta, así que lo que se ve es
menos del 1 %, y cambia por completo en cada recarga.

**La barra de arriba dice de cuándo es el dato:**

```
fuente: opensky · dato 10:09:12 (hace 7 s) · cargado 10:09:18
```

Son tres cosas distintas y las tres hacen falta. `dato` es cuándo OpenSky consolidó el
lote, no cuándo se lo pedimos. `hace 7 s` es la antigüedad en el momento de servir la
página, y se congela con ella. **`cargado` es la que resuelve la pregunta**: si deja la
pestaña abierta una hora, esa hora comparada con su reloj le dice que lo que está
mirando ya no es de ahora.

**La página no se actualiza sola.** No hay refresco automático ni JavaScript: los datos
se piden en el servidor una vez, al cargar. Se actualiza cuando usted recarga.

## De dónde salen los datos

Tres niveles, y se intentan en ese orden. **La aplicación corre en los tres.**

| `fuente` | Cuándo | Presupuesto |
| --- | --- | --- |
| `opensky` | Hay credenciales y sirven | **4.000 créditos al día** |
| `opensky-anonimo` | No hay credenciales, o no sirven | 400 al día, **contados por dirección IP** |
| `respaldo` | Nada de lo anterior contestó | Una instantánea local, sin límite |

**Lo de la dirección IP importa.** En el nivel anónimo los 400 créditos se cuentan por
IP, así que una oficina entera detrás del mismo NAT comparte un solo presupuesto. Cada
consulta cuesta 4 créditos: son unas 100 cargas de página al día entre todos, y cuando
se agotan la aplicación cae al respaldo **sin avisar**. Con credenciales el mismo cálculo
da unas 1.000.

## La arquitectura

Los diagramas están en [`diagrams/`](diagrams/), en `.drawio` sin comprimir para que se
puedan leer y diffear, con su `.png` al lado.

| Diagrama | Qué responde |
| --- | --- |
| [Vista Técnica N0](diagrams/vista_tecnica_n0.png) | Qué componentes hay, sin tecnología |
| [Vista Técnica N1](diagrams/vista_tecnica_n1.png) | Con qué está hecho cada componente |
| [Entornos y ramas](diagrams/entornos_y_ramas.png) | Los tres entornos y qué prueba cada uno |

Dos cosas que los diagramas dicen y el código no grita:

- **No hay almacenamiento, y es a propósito.** La E y la T del ETL corren dentro de la
  misma petición que sirve la pantalla, y el dato se descarta. Por eso no hay historia y
  nadie puede responder qué pasó ayer. Es la primera pieza que habría que agregar.
- **La procedencia del dato es un componente**, no un adorno. Sin ella una pantalla vieja
  se ve igual que una en vivo.

## Los tres entornos

| Nivel | Comando | Qué demuestra |
| --- | --- | --- |
| **1 · Local** | `uvicorn app.main:app --reload` | Que la lógica hace lo que uno cree |
| **2 · Contenedor** | `PUERTO=8099 docker compose up --build` | Que el empaque está completo y corre en una máquina limpia |
| **3 · Nube** | `scripts/desplegar.sh` para subirlo, `gcloud run services proxy` para verlo | Que arranca con los permisos y la red de verdad |

**No se sube al siguiente nivel hasta que el anterior está en verde.** Un fallo
descubierto en el nivel 3 cuesta minutos de espera; el mismo fallo en el nivel 1 cuesta
segundos.

## Desplegar

```
scripts/desplegar.sh
```

El script **se niega a desplegar con el árbol sucio** y etiqueta la imagen con el commit
en vez de `latest`, para que siempre se pueda contestar qué código está corriendo. Corre
las pruebas antes, y al terminar imprime qué revisión quedó arriba.

### El servicio no es público

Se despliega con `--no-allow-unauthenticated`, y quién puede invocarlo lo decide IAM con
un binding nominal. No hay una dirección que cualquiera pueda abrir. Para verlo:

```
gcloud run services proxy tablero-vuelos \
  --region=us-central1 --project=per-ep-tablero-vuelos --port=8097
```

Eso abre un túnel autenticado y el tablero queda en <http://localhost:8097>. El puerto va
explícito para no chocar con la copia local ni con el contenedor.

Para darle acceso a alguien más:

```
gcloud run services add-iam-policy-binding tablero-vuelos \
  --region=us-central1 --member=user:alguien@ejemplo.com --role=roles/run.invoker
```

**Un aviso que costó una tarde:** la bandera contraria, `--allow-unauthenticated`, **falla
en silencio**. El despliegue sale `SUCCESS`, el policy IAM del servicio queda vacío, y
todo devuelve 403 sin una línea que lo explique. Si algún día hace falta que sea público,
hay que otorgar `run.invoker` a `allUsers` en un paso aparte **y verificar el policy**.

### Las credenciales en la nube

El servicio **no lee el `.env` local**. Las de OpenSky van por Secret Manager:

```
gcloud secrets create opensky-client-id --data-file=- <<< "su-usuario-api-client"
gcloud run services update tablero-vuelos --region=us-central1 \
  --set-secrets=OPENSKY_CLIENT_ID=opensky-client-id:latest
```

Con `--set-secrets` y no `--set-env-vars`: con variables de entorno el secreto queda
visible en la descripción del servicio y en el historial de despliegues.

### OpenSky no es alcanzable desde Cloud Run

Medido el 31 de agosto de 2026: `ConnectTimeout` contra `194.209.200.34:443`, con 8 y con
30 segundos de espera, en el servidor de autenticación y en el de datos. No es lentitud ni
credenciales: el tráfico se descarta, que es lo que hace un servicio académico para
defenderse de raspadores en la nube.

**El servicio desplegado sirve siempre la instantánea local**, y lo dice en la barra. Por
eso `OPENSKY_TIMEOUT` va bajo ahí: esperar por algo que no va a contestar solo hace lenta
la página.

## Integración continua

`.github/workflows/tests.yml` corre las pruebas en cada push y cada pull request, y **no
tiene ni un secreto**: un CI sin credenciales es un CI que no puede filtrarlas.

Además de correr la suite, verifica que la suite haya corrido de verdad. Un CI que da
verde sin probar lo que cree es peor que no tener CI, así que revisa dos cosas: que
ninguna prueba se haya salteado, y que la cuenta llegue al mínimo. `tests/test_centinela.py`
mantiene ese mínimo honesto: falla, con el número exacto que hay que poner, en cuanto se
queda atrás.

## El trabajo de la sesión

El requerimiento **no está en este repositorio**, y es a propósito: un pedido de negocio no
nace en el repositorio de quien lo va a implementar. Llega con el material de la sesión, en
el Drive del programa, igual que llegaría de operaciones o del gestor de proyectos.

Este repositorio es la aplicación. El requerimiento es el trabajo.
