"""Validación técnica de una toma generada. Los umbrales dejan de estar en prosa.

La tolerancia del 9:16 era 0,01 y dejaba fuera 496×864, que es una de las
resoluciones nativas de Seedance 2.5 (496/864 = 0,5741 frente a 0,5625). Con 0,02
entran las nativas y siguen fuera los recortes de 16:9.
"""
from __future__ import annotations

from .resultado import Resultado

TOLERANCIA_9_16 = 0.02
DELTA_E_MAXIMO = 15.0
FPS_OBJETIVO = 24
TOLERANCIA_DURACION_SEG = 0.35


def es_vertical(ancho: int, alto: int, tolerancia: float = TOLERANCIA_9_16) -> bool:
    return abs(ancho / alto - 9 / 16) < tolerancia


def valida_toma(tecnico: dict, *, duracion_pedida: float | None = None,
                delta_e: float | list[float] | None = None, cortes: list | None = None,
                fps_objetivo: int = FPS_OBJETIVO) -> Resultado:
    """`tecnico` es la salida de `qc.sonda.sondear`."""
    r = Resultado()
    ancho, alto = int(tecnico["ancho"]), int(tecnico["alto"])
    if not es_vertical(ancho, alto):
        r.error("NO_ES_VERTICAL",
                f"{ancho}×{alto} no es 9:16 (tolerancia {TOLERANCIA_9_16})", "vertical")
    if round(float(tecnico["fps"])) != fps_objetivo:
        r.error("FPS_DISTINTO", f"{tecnico['fps']} fps; el proyecto trabaja a {fps_objetivo}")
    if not tecnico.get("audio"):
        r.aviso("SIN_PISTA_DE_AUDIO", "la toma no trae pista de audio")

    if duracion_pedida is not None:
        real = float(tecnico.get("duracion_video") or tecnico["duracion"])
        if abs(real - duracion_pedida) > TOLERANCIA_DURACION_SEG:
            r.error("DURACION_DISTINTA",
                    f"se pidieron {duracion_pedida:g} s y el vídeo dura {real:.2f} s")

    if delta_e is not None:
        valores = [delta_e] if isinstance(delta_e, (int, float)) else list(delta_e)
        peor = max(valores) if valores else 0.0
        if peor >= DELTA_E_MAXIMO:
            r.error("DERIVA_DE_COLOR",
                    f"ΔE máximo {peor:.1f} frente a la referencia (límite {DELTA_E_MAXIMO:g})",
                    "qc")

    if cortes is not None and len(cortes) > 1:
        r.error("CORTES_INTERNOS",
                f"{len(cortes)} escenas detectadas; un plano es una escena continua", "qc")
    return r
