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
    assert datos["fuente"] in ("opensky", "respaldo")


def test_cada_vuelo_trae_los_campos_que_la_vista_usa():
    vuelos = cliente.get("/api/vuelos?limite=3").json()["vuelos"]
    assert vuelos, "sin vuelos no se puede probar nada"
    for v in vuelos:
        for campo in ("callsign", "pais", "latitud", "longitud",
                      "altitud", "velocidad", "en_tierra"):
            assert campo in v, f"falta {campo}"
