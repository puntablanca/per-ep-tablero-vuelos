"""El centinela del centinela: que el número del CI siga siendo el real.

El workflow revisa que corra un mínimo de pruebas, para atrapar el caso de que la suite
se vacíe sin que nadie se entere. Pero un mínimo viejo no se nota: el CI sigue en verde
y ya no protege nada. Esta prueba hace que quedarse atrás sea un fallo, con el número
exacto que hay que poner.

Mismo criterio que tests/test_centinela.py de int-01-agente-de-whatsapp, de donde sale
este patrón.
"""
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
WORKFLOW = RAIZ / ".github" / "workflows" / "tests.yml"


def _minimo_del_ci() -> int:
    """El valor de `MINIMO=N` tal como lo lee bash en el workflow."""
    m = re.search(r"^\s*MINIMO=(\d+)\s*$", WORKFLOW.read_text(encoding="utf-8"), re.M)
    assert m is not None, f"no se encontró MINIMO= en {WORKFLOW}"
    return int(m.group(1))


def _contar_suite() -> int:
    """Cuenta con una colección real de pytest en un subproceso, sin ejecutar nada.

    Se cuenta así y no buscando `def test_` en los archivos porque este repositorio usa
    @pytest.mark.parametrize: contar funciones da menos de las que corren, y una cuenta
    que no cierra es peor que no tener cuenta.
    """
    # `-o addopts=` anula el `-q` que trae el pyproject, y es obligatorio.
    # Comprobado el 2026-08-31: con el `-q` del proyecto MAS un `-q` propio, pytest
    # entra en doble silencio, imprime una cuenta por archivo y NO imprime la linea
    # del total. El regex no encontraba nada y esta prueba fallaba por una razon que
    # no tenia que ver con la suite. Es exactamente el fallo silencioso que este
    # archivo existe para atajar, y le paso al centinela mismo.
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only",
         "-o", "addopts=", "-p", "no:cacheprovider", "tests/"],
        cwd=RAIZ, capture_output=True, text=True,
    )
    m = re.search(r"(\d+)(?:/\d+)? tests? collected", r.stdout)
    assert m is not None, (
        f"no se pudo contar la suite:\n{r.stdout[-500:]}\n{r.stderr[-500:]}"
    )
    return int(m.group(1))


def test_el_minimo_del_ci_es_la_cuenta_real():
    """MINIMO tiene que ser IGUAL a la cantidad de pruebas, no un piso holgado.

    Sin números escritos acá a propósito: se quedan viejos en el próximo commit que
    agregue pruebas, y en un comentario nadie los actualiza.
    """
    minimo = _minimo_del_ci()
    real = _contar_suite()
    assert minimo == real, (
        f"MINIMO del workflow está en {minimo} y la suite tiene {real} pruebas. "
        f"Poner MINIMO={real} en .github/workflows/tests.yml."
    )


def test_el_workflow_no_lleva_secretos():
    """Un CI sin credenciales es un CI que no puede filtrarlas.

    Si algún día hace falta desplegar desde el CI, el camino es Workload Identity
    Federation, no una llave de cuenta de servicio en un secreto de GitHub. Esta prueba
    obliga a que ese cambio sea deliberado y no se cuele en un commit de otra cosa.
    """
    texto = WORKFLOW.read_text(encoding="utf-8")
    # Se busca el uso real, `${{ secrets.ALGO }}`, no la palabra en un comentario.
    usos = re.findall(r"\$\{\{\s*secrets\.[A-Z_]+\s*\}\}", texto)
    assert not usos, f"el workflow usa secretos: {usos}"
