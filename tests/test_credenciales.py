"""Las credenciales de OpenSky, y que la aplicación corra igual sin ellas.

Ninguna de estas pruebas sale a la red: el cliente de OpenSky se reemplaza por uno
falso. Una prueba que depende de internet no es una prueba, es una apuesta.
"""
import pytest

import app.opensky as osky


def _olvidar_token() -> None:
    osky._token_guardado["valor"] = None
    osky._token_guardado["vence"] = 0.0


class _RespuestaDeToken:
    """Lo que contesta el servidor de auth de OpenSky cuando le gusta el cliente."""

    status_code = 200
    headers: dict = {}

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return {"access_token": "abc123", "expires_in": 1800}


@pytest.mark.parametrize(
    "cliente, secreto",
    [
        ("", ""),           # sin nada
        ("solo-cliente", ""),   # el .env a medio llenar
        ("", "solo-secreto"),
    ],
)
def test_las_credenciales_van_de_dos_en_dos(monkeypatch, cliente, secreto):
    """Con una sola no se intenta autenticar: se manda un secreto vacío y da 401."""
    monkeypatch.setenv("OPENSKY_CLIENT_ID", cliente)
    monkeypatch.setenv("OPENSKY_CLIENT_SECRET", secreto)
    _olvidar_token()
    assert osky.credenciales() is None
    assert osky._token() is None


def test_el_token_se_guarda_y_no_se_vuelve_a_pedir(monkeypatch):
    monkeypatch.setenv("OPENSKY_CLIENT_ID", "cliente")
    monkeypatch.setenv("OPENSKY_CLIENT_SECRET", "secreto")
    _olvidar_token()

    idas = []
    monkeypatch.setattr(
        osky.httpx, "post",
        lambda *a, **k: (idas.append(1), _RespuestaDeToken())[1],
    )

    assert osky._token() == "abc123"
    assert osky._token() == "abc123"
    assert len(idas) == 1, "el segundo token tenía que salir del caché, no de la red"

    # Y con `forzar` sí vuelve a pedirlo, que es lo que pasa tras un 401.
    assert osky._token(forzar=True) == "abc123"
    assert len(idas) == 2


def test_si_no_contesta_nadie_cae_al_respaldo(monkeypatch):
    def sin_red(*a, **k):
        raise RuntimeError("sin red")

    monkeypatch.setattr(osky.httpx, "get", sin_red)
    monkeypatch.setattr(osky.httpx, "post", sin_red)
    _olvidar_token()

    lote = osky.obtener_vuelos(3)
    assert lote.fuente == "respaldo"
    assert lote.momento is None, "el respaldo no tiene hora, y eso es a propósito"
    assert len(lote.vuelos) == 3, "el respaldo tiene que alcanzar para lo que se le pida"
