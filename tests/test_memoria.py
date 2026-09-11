"""Memoria de la serie: sin esto cada episodio se escribe como si fuera el primero."""
from __future__ import annotations

import factorias as f

from showrunner.agentes import escritura
from showrunner.dominio import memoria


def test_el_primer_episodio_no_finge_pasado(serie):
    resumen = memoria.resumen(serie, "s01_ep01")
    assert "Ninguno: este es el primero" in resumen


def test_lo_escrito_manda_sobre_lo_planificado(serie):
    """La temporada dice «El sobre»; el guion escrito dice qué pasó de verdad."""
    escritura.guardar_biblia(serie, f.salida_showrunner())
    escritura.guardar_episodio(serie, f.salida_guionista(), "s01_ep01")
    episodios = memoria.episodios(serie)
    primero = next(e for e in episodios if e.numero == 1)
    assert primero.escrito
    assert primero.cliffhanger == "alguien más tiene una copia"
    assert primero.giro == "La firma es suya."


def test_el_resumen_señala_el_cliffhanger_abierto_y_los_ya_usados(serie):
    escritura.guardar_biblia(serie, f.salida_showrunner())
    escritura.guardar_episodio(serie, f.salida_guionista(), "s01_ep01")
    resumen = memoria.resumen(serie, "s01_ep02")
    assert "Cliffhanger que quedó abierto" in resumen
    assert "alguien más tiene una copia" in resumen
    assert "no los repitas" in resumen


def test_un_guion_corrupto_no_rompe_la_memoria(serie):
    escritura.guardar_biblia(serie, f.salida_showrunner())
    escritura.guardar_episodio(serie, f.salida_guionista(), "s01_ep01")
    (serie / "episodios" / "ep01" / "guion.json").write_text("{roto", encoding="utf-8")
    resumen = memoria.resumen(serie, "s01_ep02")
    assert "Episodios anteriores" in resumen      # cae de vuelta a temporada.json
