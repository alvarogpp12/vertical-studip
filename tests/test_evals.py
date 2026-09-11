"""El arnés de evaluación: mutaciones, acuerdo juez–humano y el golden set del linter."""
from __future__ import annotations

import pytest
from comun import Marcador, aplicar_mutacion, cargar_casos
from eval_director import evalua_linter
from rubrica import CRITERIOS, UMBRALES


def test_las_mutaciones_describen_el_caso():
    base = "uno dos tres"
    assert aplicar_mutacion(base, None) == base
    assert aplicar_mutacion(base, {"quitar": ["dos "]}) == "uno tres"
    assert aplicar_mutacion(base, {"sustituir": [["dos", "DOS"]]}) == "uno DOS tres"
    assert aplicar_mutacion(base, {"anadir": "cuatro"}) == "uno dos tres\ncuatro\n"


def test_sin_etiquetas_no_se_inventa_un_acuerdo():
    """El QC no debe decidir nada hasta que se haya medido su acuerdo contigo."""
    m = Marcador("qc")
    m.anota("v01", None, "aceptada", True)
    acuerdo = m.acuerdo()
    assert acuerdo["n"] == 0 and acuerdo["exactitud"] is None and "nota" in acuerdo


def test_kappa_descuenta_el_acuerdo_por_azar():
    """Con una clase dominante, la exactitud engaña y kappa no."""
    perfecto = Marcador("qc")
    for i in range(10):
        etiqueta = "aceptada" if i < 9 else "rechazada"
        perfecto.anota(f"v{i}", etiqueta, etiqueta, True)
    assert perfecto.acuerdo() == {"n": 10, "coincidencias": 10, "exactitud": 1.0, "kappa": 1.0}

    perezoso = Marcador("qc")
    for i in range(10):
        perezoso.anota(f"v{i}", "aceptada" if i < 9 else "rechazada", "aceptada", i < 9)
    acuerdo = perezoso.acuerdo()
    assert acuerdo["exactitud"] == pytest.approx(0.9)
    assert acuerdo["kappa"] == pytest.approx(0.0)     # decir siempre lo mismo no vale nada


def test_el_golden_set_del_director_esta_equilibrado():
    casos = cargar_casos("prompts.jsonl")
    assert len(casos) >= 20
    validos = [c for c in casos if c.etiqueta == "valido"]
    assert 4 <= len(validos) <= len(casos) - 4, "hacen falta casos buenos y malos"
    assert len({c.id for c in casos}) == len(casos)


def test_el_linter_reproduce_el_golden_set():
    """La rúbrica del director, sin red y sin coste."""
    resumen = evalua_linter().resumen()
    assert resumen["casos"] >= 20
    assert resumen["tasa"] == 1.0, resumen["fallos"]


def test_la_rubrica_cita_su_fuente():
    for agente, criterios in CRITERIOS.items():
        assert criterios, agente
        for criterio in criterios:
            assert criterio.fuente, f"{agente}/{criterio.clave} sin fuente"
    assert UMBRALES["duracion_min_seg"] == 61     # TikTok exige más de 60 s
