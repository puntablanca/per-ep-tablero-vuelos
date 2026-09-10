"""El tablero mira un solo país, y el orden en que lo hace importa.

Ninguna de estas pruebas sale a la red: se reemplaza `_pedir_estados`, que es la
única función que habla con OpenSky, por una que devuelve estados armados a mano.
"""
import pytest

import app.opensky as osky


def estado(callsign: str, pais: str, en_tierra: bool = False) -> list:
    """Un estado crudo de OpenSky, que es una lista posicional de 17 casillas.

    Se arma completo, con las 17, y no solo con las que `_normalizar` lee: un
    estado recortado pasaría la prueba y reventaría contra el dato de verdad.
    """
    return [
        "abc123",       # 0  icao24
        callsign,       # 1  callsign
        pais,           # 2  origin_country
        1756000000,     # 3  time_position
        1756000000,     # 4  last_contact
        -99.1,          # 5  longitud
        19.4,           # 6  latitud
        0.0 if en_tierra else 10000.0,  # 7  altitud
        en_tierra,      # 8  en tierra
        220.0,          # 9  velocidad
        90.0,           # 10 rumbo
        0.0,            # 11 razón de ascenso
        None,           # 12 sensores
        10000.0,        # 13 altitud geométrica
        "1234",         # 14 transpondedor
        False,          # 15 alerta
        0,              # 16 origen de la posición
    ]


@pytest.fixture
def fuente(monkeypatch):
    """Reemplaza la consulta a OpenSky por una lista de estados que da la prueba."""
    def poner(estados: list) -> None:
        monkeypatch.setattr(
            osky, "_pedir_estados", lambda: (estados, "opensky", 1756000000.0)
        )
    return poner


def test_solo_devuelve_vuelos_del_pais_configurado(monkeypatch, fuente):
    monkeypatch.setenv("TABLERO_PAIS", "Mexico")
    fuente([
        estado("AMX404", "Mexico"),
        estado("UAL2087", "United States"),
        estado("VOI1234", "Mexico"),
        estado("ACA9470", "Canada"),
    ])
    lote = osky.obtener_vuelos()
    assert [v["callsign"] for v in lote.vuelos] == ["AMX404", "VOI1234"]


def test_el_filtro_corre_antes_del_corte_por_limite(monkeypatch, fuente):
    """Es el orden lo que hace que la vista sirva, y es fácil de romper sin notarlo.

    De 6.620 vuelos en el aire, unos 72 son mexicanos: uno de cada noventa. Cortar
    a 40 primero y filtrar después devolvería cero casi siempre, y el tablero
    aparecería vacío sin un solo error en los registros.
    """
    monkeypatch.setenv("TABLERO_PAIS", "Mexico")
    fuente(
        [estado(f"UAL{i}", "United States") for i in range(10)]
        + [estado("AMX1", "Mexico"), estado("AMX2", "Mexico"), estado("VOI3", "Mexico")]
    )
    lote = osky.obtener_vuelos(limite=2)
    assert [v["callsign"] for v in lote.vuelos] == ["AMX1", "AMX2"]


def test_sin_pais_configurado_se_ve_el_mundo_entero(monkeypatch, fuente):
    """Volver al tablero mundial no tiene que costar un cambio de código."""
    monkeypatch.setenv("TABLERO_PAIS", "")
    fuente([estado("AMX404", "Mexico"), estado("UAL2087", "United States")])
    lote = osky.obtener_vuelos()
    assert [v["callsign"] for v in lote.vuelos] == ["AMX404", "UAL2087"]


def test_el_respaldo_tambien_se_filtra(monkeypatch):
    """Sin red el tablero sigue siendo el mismo tablero, no otro más grande.

    La instantánea local trae vuelos de once países. Si no se filtrara, quedarse
    sin internet cambiaría de qué habla la pantalla, que es peor que quedarse sin
    datos: nadie lo notaría.
    """
    monkeypatch.setenv("TABLERO_PAIS", "Mexico")

    def sin_red(*a, **k):
        raise RuntimeError("sin red")

    monkeypatch.setattr(osky.httpx, "get", sin_red)
    monkeypatch.setattr(osky.httpx, "post", sin_red)

    lote = osky.obtener_vuelos()
    assert lote.fuente == "respaldo"
    assert lote.vuelos, "el respaldo tiene que traer vuelos del país, no quedar vacío"
    assert all(v["pais"] == "Mexico" for v in lote.vuelos)
