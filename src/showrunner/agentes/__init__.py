"""Los cuatro agentes que deciden.

| Agente     | Entrada → salida                    | Modelo          | Por qué |
|------------|-------------------------------------|-----------------|---------|
| showrunner | idea → conceptos → biblia+temporada | opus-5 · xhigh  | pasada larga, mucho valor |
| guionista  | biblia + episodio → guion+shotlist  | opus-5 · high   | aquí viven R-09 y R-10 |
| director   | plano + registro + estilo → prompt  | sonnet-5 · med. | fan-out: caché y batch |
| qc         | fotogramas + refs → veredicto       | sonnet-5 → opus | mucha entrada, poco razonar |

Casting, montaje y publicación no llevan agente: son código determinista.
"""
from __future__ import annotations

from .base import Agente, Contexto, cargar_skill, rechazo
from .cliente import ClienteAnthropic, ClienteFalso, ClienteLLM, LLMNoDisponible
from .contratos import Rechazo, Sobre

#: Los submódulos de agente NO se importan aquí a propósito: cada uno depende de
#: `showrunner.valida`, que a su vez lee los contratos de este paquete. Importarlos
#: en el __init__ crea un ciclo. `from showrunner.agentes import director` funciona
#: igual: Python importa el submódulo cuando el atributo no existe.
__all__ = [
    "Agente",
    "ClienteAnthropic",
    "ClienteFalso",
    "ClienteLLM",
    "Contexto",
    "LLMNoDisponible",
    "Rechazo",
    "Sobre",
    "cargar_skill",
    "rechazo",
]
