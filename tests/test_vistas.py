from fastapi.testclient import TestClient

from app.main import app

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
