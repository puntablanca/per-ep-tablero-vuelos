from fastapi.testclient import TestClient

import app.main as main
from app.main import app
from app.opensky import Lote

cliente = TestClient(app)


def test_la_raiz_lleva_a_posicion():
    r = cliente.get("/", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"] == "/posicion"


def test_posicion_muestra_la_tabla():
    r = cliente.get("/posicion")
    assert r.status_code == 200
    assert "Vuelo" in r.text
    assert "vuelos en tierra" in r.text


def test_la_vista_trae_el_boton_de_actualizar():
    """El boton es la unica manera de refrescar: la pagina no se actualiza sola."""
    html = cliente.get("/posicion").text
    assert 'class="refresco"' in html, "falta el boton de actualizar"
    assert 'href="/posicion"' in html, "el boton tiene que apuntar a la ruta actual"


def _lote(vuelos: list[dict]):
    """Un lote fijo, para que la vista se pruebe sin depender de qué esté volando."""
    return Lote(vuelos=vuelos, fuente="respaldo", momento=None)


def _vuelo(callsign: str, altitud: float = 10000.0, en_tierra: bool = False) -> dict:
    return {
        "callsign": callsign, "pais": "Mexico", "longitud": -99.1, "latitud": 19.4,
        "altitud": altitud, "velocidad": 220.0, "en_tierra": en_tierra,
    }


def test_aerolineas_muestra_la_tabla():
    r = cliente.get("/aerolineas")
    assert r.status_code == 200
    assert "Aerolínea" in r.text
    assert "Altitud promedio" in r.text


def test_las_dos_vistas_se_enlazan_entre_si():
    """El criterio de operaciones: llegar sin escribir la dirección a mano.

    Se revisa en las dos porque el enlace vive en la plantilla base, y una base
    que solo sirva para la vista donde se probó no sirve para la siguiente.
    """
    assert 'href="/aerolineas"' in cliente.get("/posicion").text
    assert 'href="/posicion"' in cliente.get("/aerolineas").text


def test_la_tabla_pone_primero_la_aerolinea_con_mas_vuelos_en_tierra(monkeypatch):
    monkeypatch.setattr(main, "obtener_vuelos", lambda *a, **k: _lote([
        _vuelo("AMX1"), _vuelo("AMX2"), _vuelo("AMX3"),
        _vuelo("VOI1", en_tierra=True), _vuelo("VOI2", en_tierra=True),
    ]))
    html = cliente.get("/aerolineas").text
    assert html.index("VOI") < html.index("AMX"), "la peor tiene que salir arriba"


def test_una_aerolinea_sin_vuelos_en_ruta_no_reporta_altitud_cero(monkeypatch):
    """Cero metros sería un dato falso. Lo que hay ahí es ausencia de dato."""
    monkeypatch.setattr(main, "obtener_vuelos", lambda *a, **k: _lote([
        _vuelo("SLI1", altitud=0.0, en_tierra=True),
        _vuelo("SLI2", altitud=0.0, en_tierra=True),
    ]))
    html = cliente.get("/aerolineas").text
    assert "—" in html
    assert "0 m" not in html
