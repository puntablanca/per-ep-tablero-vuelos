from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_salud_responde_ok():
    r = cliente.get("/salud")
    assert r.status_code == 200
    assert r.json()["estado"] == "ok"


def test_api_vuelos_devuelve_lista():
    r = cliente.get("/api/vuelos?limite=5")
    assert r.status_code == 200
    datos = r.json()
    assert datos["total"] == len(datos["vuelos"]) <= 5
    assert datos["fuente"] in ("opensky", "opensky-anonimo", "respaldo")


def test_cada_vuelo_trae_los_campos_que_la_vista_usa():
    vuelos = cliente.get("/api/vuelos?limite=3").json()["vuelos"]
    assert vuelos, "sin vuelos no se puede probar nada"
    for v in vuelos:
        for campo in ("callsign", "pais", "latitud", "longitud",
                      "altitud", "velocidad", "en_tierra"):
            assert campo in v, f"falta {campo}"


def test_la_respuesta_dice_de_cuando_es_el_dato():
    d = cliente.get("/api/vuelos?limite=2").json()
    for campo in ("momento", "hora", "antiguedad_s"):
        assert campo in d, f"falta {campo}"
    if d["fuente"] == "respaldo":
        # El respaldo es una instantánea guardada: no tiene hora, y eso es el dato.
        assert d["momento"] is None
        assert d["hora"] is None
    else:
        assert isinstance(d["momento"], (int, float))
        assert d["antiguedad_s"] >= 0, "un dato del futuro sería un reloj mal puesto"


def test_el_respaldo_no_inventa_una_hora(monkeypatch):
    import app.opensky as osky

    def sin_red(*a, **k):
        raise RuntimeError("sin red")

    monkeypatch.setattr(osky.httpx, "get", sin_red)
    monkeypatch.setattr(osky.httpx, "post", sin_red)
    d = cliente.get("/api/vuelos?limite=2").json()
    assert d["fuente"] == "respaldo"
    assert d["momento"] is None and d["hora"] is None
