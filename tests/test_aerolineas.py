"""La agregación por aerolínea, probada sin levantar el servidor.

`agrupar_por_aerolinea` es una función pura: recibe vuelos y devuelve filas. Eso
es a propósito, y es lo que permite que estas pruebas armen a mano el caso raro
—una aerolínea con todo en tierra, dos empatadas— que en el dato en vivo
aparecería una vez cada tanto y nunca cuando uno lo necesita.
"""
from app.aerolineas import agrupar_por_aerolinea


def vuelo(callsign: str, altitud: float = 10000.0, en_tierra: bool = False) -> dict:
    """Un vuelo con la misma forma que arma `opensky._normalizar`."""
    return {
        "callsign": callsign,
        "pais": "Mexico",
        "longitud": -99.1,
        "latitud": 19.4,
        "altitud": altitud,
        "velocidad": 220.0,
        "en_tierra": en_tierra,
    }


def test_agrupa_por_las_tres_primeras_letras_del_callsign():
    filas = agrupar_por_aerolinea([
        vuelo("AMX404"),
        vuelo("AMX7"),
        vuelo("VOI1234"),
    ])
    assert [(f["codigo"], f["total"]) for f in filas] == [("AMX", 2), ("VOI", 1)]


def test_cuenta_los_que_estan_en_tierra():
    filas = agrupar_por_aerolinea([
        vuelo("VIV100", en_tierra=True),
        vuelo("VIV200", en_tierra=True),
        vuelo("VIV300"),
    ])
    assert filas[0]["total"] == 3
    assert filas[0]["en_tierra"] == 2


def test_el_promedio_de_altitud_ignora_los_que_estan_en_tierra():
    """Un avión en tierra reporta 0 m y arrastraría el promedio hacia abajo.

    Con 9000 y 11000 en ruta el promedio es 10000. Si el de tierra entrara,
    saldría 6666,67 y la columna diría que la flota vuela más bajo de lo que vuela.
    """
    filas = agrupar_por_aerolinea([
        vuelo("AMX1", altitud=9000.0),
        vuelo("AMX2", altitud=11000.0),
        vuelo("AMX3", altitud=0.0, en_tierra=True),
    ])
    assert filas[0]["altitud_promedio"] == 10000.0


def test_sin_ninguno_en_ruta_el_promedio_no_existe():
    """None, no 0. Cero metros es un dato; la ausencia de dato es otra cosa."""
    filas = agrupar_por_aerolinea([
        vuelo("SLI1", altitud=0.0, en_tierra=True),
        vuelo("SLI2", altitud=0.0, en_tierra=True),
    ])
    assert filas[0]["altitud_promedio"] is None


def test_ordena_por_mas_vuelos_en_tierra_primero():
    """Es la pregunta que operaciones hace en la mañana: cuál está peor."""
    filas = agrupar_por_aerolinea([
        vuelo("AMX1"),
        vuelo("AMX2"),
        vuelo("AMX3"),
        vuelo("VOI1", en_tierra=True),
        vuelo("VOI2", en_tierra=True),
    ])
    assert [f["codigo"] for f in filas] == ["VOI", "AMX"]


def test_con_los_mismos_en_tierra_manda_el_que_tiene_mas_vuelos():
    filas = agrupar_por_aerolinea([
        vuelo("AMX1", en_tierra=True),
        vuelo("AMX2"),
        vuelo("AMX3"),
        vuelo("VOI1", en_tierra=True),
        vuelo("VOI2"),
    ])
    assert [f["codigo"] for f in filas] == ["AMX", "VOI"]


def test_empatados_en_todo_el_orden_es_alfabetico():
    """El desempate final existe para que el orden no dependa del azar.

    Sin él, dos aerolíneas iguales saldrían en el orden en que llegaron del feed
    y la tabla cambiaría de forma entre dos recargas sin que cambie nada.
    """
    filas = agrupar_por_aerolinea([vuelo("VOI1"), vuelo("AMX1"), vuelo("VIV1")])
    assert [f["codigo"] for f in filas] == ["AMX", "VIV", "VOI"]


def test_sin_vuelos_no_hay_filas():
    assert agrupar_por_aerolinea([]) == []
