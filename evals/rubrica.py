"""Rúbrica de evaluación, extraída de `docs/conocimiento/`.

No es una sesión de puntuación manual: cada criterio es una comprobación que ya
existe en `showrunner.valida` o un umbral con su fuente escrita al lado. Lo que no
se puede comprobar así no se puntúa: se marca para el humano.
"""
from __future__ import annotations

from dataclasses import dataclass

from showrunner.valida.biblia import (
    MAX_LOCALIZACIONES,
    MAX_PERSONAJES,
    PRODUCIBILIDAD_MINIMA,
)
from showrunner.valida.toma import DELTA_E_MAXIMO, TOLERANCIA_9_16


@dataclass(frozen=True)
class Criterio:
    clave: str
    descripcion: str
    fuente: str


#: Umbrales duros. Cambiarlos aquí cambia la evaluación, no el código de producción.
UMBRALES = {
    "max_personajes": MAX_PERSONAJES,
    "max_localizaciones": MAX_LOCALIZACIONES,
    "producibilidad_minima": PRODUCIBILIDAD_MINIMA,
    "gancho_seg": 3,
    "duracion_min_seg": 61,
    "duracion_max_seg": 90,
    "delta_e_maximo": DELTA_E_MAXIMO,
    "tolerancia_9_16": TOLERANCIA_9_16,
    "acuerdo_minimo_juez": 0.80,
}

CRITERIOS: dict[str, list[Criterio]] = {
    "showrunner": [
        Criterio("producibilidad", f"≤{MAX_PERSONAJES} personajes y ≤{MAX_LOCALIZACIONES} "
                                   "localizaciones, sin acción difícil",
                 "01_objetivo_showrunner.md §A"),
        Criterio("descriptores", "descriptor congelado y AUDIO LOCK por personaje", "R-02"),
        Criterio("mapa", "mapa espacial vertical por localización", "R-06"),
        Criterio("estilo", "STYLE PREFIX con 9:16, CONSTRAINTS con «No music», paleta en hex",
                 "R-03, R-09"),
        Criterio("riesgos", "lista de planos que el modelo hará mal y cómo esquivarlos", "R-10"),
    ],
    "guionista": [
        Criterio("duracion", "61–90 s por episodio", "03_plataformas_y_monetizacion.md"),
        Criterio("gancho", "un beat de gancho en los primeros 3 s", "03_plataformas"),
        Criterio("cliffhanger", "un beat de cierre sin resolver", "03_plataformas"),
        Criterio("master", "el episodio abre con un máster que fija la geografía", "R-06"),
        Criterio("dialogo", "el diálogo cabe a 4 palabras/s + 1 s de cola", "R-09"),
        Criterio("camara", "un solo movimiento por plano, sin travelling lateral", "vertical"),
    ],
    "director": [
        Criterio("bloques", "STYLE PREFIX y CONSTRAINTS copiados palabra por palabra", "R-03"),
        Criterio("registro", "todo @tag existe en registry.json", "R-01"),
        Criterio("literal", "el descriptor congelado va palabra por palabra", "R-02"),
        Criterio("isla", "nada heredado de otro plano", "R-02"),
        Criterio("emocion", "tareas, no emociones", "R-07"),
        Criterio("limites", "los límites como «= failed take»", "R-08"),
        Criterio("audio", "«No music» siempre", "R-09"),
    ],
    "qc": [
        Criterio("acuerdo", f"acuerdo con el veredicto humano ≥ "
                            f"{UMBRALES['acuerdo_minimo_juez']:.0%}", "calibración del crítico"),
        Criterio("prudencia", "ante la duda, confianza baja y `requiere_humano`",
                 "qc-continuidad/SKILL.md"),
    ],
}
