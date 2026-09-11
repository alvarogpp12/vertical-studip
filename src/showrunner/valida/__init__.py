"""Validadores deterministas: sin LLM, sin coste, antes de cada llamada cara.

Es el linter que pide `00_investigacion_sistema.md` («Claude se cree director →
linter/hook antes de cada llamada»). Cuatro familias:

* `prompt`   · lo que se le manda al modelo   (R-01, R-02, R-03, R-07, R-08, R-09)
* `plano`    · lo que dice el shotlist        (R-06, R-09, R-11, R-12, vertical)
* `toma`     · lo que ha devuelto el modelo   (9:16, fps, duración, ΔE, cortes)
* `episodio` · lo que se va a publicar        (≥ 61 s, etiqueta de IA)
"""
from __future__ import annotations

from .episodio import valida_episodio
from .plano import valida_plano, valida_shotlist
from .prompt import bloques_de_estilo, valida_prompt
from .resultado import Incidencia, Resultado
from .toma import es_vertical, valida_toma

__all__ = [
    "Incidencia",
    "Resultado",
    "bloques_de_estilo",
    "es_vertical",
    "valida_episodio",
    "valida_plano",
    "valida_prompt",
    "valida_shotlist",
    "valida_toma",
]
