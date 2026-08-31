#!/usr/bin/env bash
# Despliega el tablero a Cloud Run, etiquetando la imagen con el commit.
#
#   scripts/desplegar.sh
#
# Por qué existe este script y no se llama a `gcloud builds submit` a mano. Dos razones,
# las dos salidas de fallas reales del programa de donde sale este patrón
# (int-01-agente-de-whatsapp):
#
# 1. La imagen se etiquetaba `latest`, así que NADIE podía contestar qué código estaba
#    corriendo. El comentario de cloudbuild.yaml decía desde el primer día que se podía
#    pasar el SHA, y en catorce revisiones nadie lo pasó nunca. Una convención que
#    depende de que alguien se acuerde no es una convención.
# 2. Se descubrió que había archivos de cloudbuild desplegados y sin commitear. Es la
#    peor combinación posible: lo que corre no está en el repositorio, y el próximo que
#    despliegue desde main reintroduce el problema sin saberlo. Por eso este script SE
#    NIEGA a desplegar con el árbol sucio, en vez de avisar y seguir.
set -euo pipefail

PROYECTO=per-ep-tablero-vuelos
SERVICIO=tablero-vuelos
REGION=us-central1

cd "$(dirname "$0")/.."

sucio=$(git status --porcelain | wc -l)
if [ "$sucio" -ne 0 ]; then
  echo "ABORTADO: hay $sucio archivo(s) sin commitear." >&2
  git status --short >&2
  echo >&2
  echo "Desplegar así deja código corriendo que no está en el repositorio, y el" >&2
  echo "próximo despliegue desde main lo revierte sin que nadie se entere." >&2
  echo "Commitea primero." >&2
  exit 1
fi

# Las pruebas antes del despliegue, no después. Cuesta veinte segundos y es la última
# oportunidad de que un fallo salga barato.
echo "corriendo las pruebas antes de desplegar"
pytest -q

TAG=$(git rev-parse --short HEAD)
RAMA=$(git rev-parse --abbrev-ref HEAD)
[ "$RAMA" = "main" ] || echo "OJO: desplegando desde la rama '$RAMA', no desde main."

echo
echo "desplegando $SERVICIO con la imagen etiquetada $TAG (rama $RAMA)"
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions="_TAG=$TAG" \
  --project="$PROYECTO" .

echo
echo "qué quedó corriendo:"
gcloud run services describe "$SERVICIO" \
  --region="$REGION" --project="$PROYECTO" \
  --format='value(status.traffic[0].revisionName, spec.template.spec.containers[0].image, status.url)'

echo
echo "El servicio NO es público. Para verlo, abra un túnel autenticado:"
echo
echo "  gcloud run services proxy $SERVICIO --region=$REGION --project=$PROYECTO --port=8099"
echo
echo "Y el tablero queda en http://localhost:8099"
echo
echo "OJO: OpenSky descarta el tráfico de Cloud Run, así que el servicio desplegado"
echo "sirve la instantánea local, no datos en vivo. La barra lo dice."
