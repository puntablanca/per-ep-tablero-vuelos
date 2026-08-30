# Requerimiento · Tablero por aerolínea

**De:** operaciones
**Para:** el equipo de desarrollo

## Qué necesitamos

Hoy el tablero muestra un renglón por vuelo. Cuando son sesenta vuelos, esa lista no
responde la pregunta que hacemos todas las mañanas: **¿cuál aerolínea está peor?**

Queremos una segunda vista, agrupada por aerolínea, que muestre por cada una cuántos vuelos
seguimos, cuántos están en tierra y la altitud promedio de los que están en ruta. Ordenada
por la que tiene más vuelos en tierra, que es la que hay que mirar primero.

## Cómo sabemos que está lista

Que se pueda abrir `/aerolineas` en el navegador, ver la tabla ordenada, y llegar a ella
desde la vista que ya existe sin escribir la dirección a mano.

## Notas

- La aerolínea sale de las tres primeras letras del `callsign`. `AAL2314` es `AAL`.
- Los vuelos en tierra no cuentan para el promedio de altitud: distorsionan el número.
- No hace falta tocar la fuente de datos. Todo lo que se necesita ya viene en `/api/vuelos`.
