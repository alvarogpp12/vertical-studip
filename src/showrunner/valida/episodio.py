"""Validación del episodio montado: lo último antes de publicar.

`03_plataformas_y_monetizacion.md` fija dos condiciones que hasta ahora no
comprobaba nadie: más de 60 s para los Creator Rewards de TikTok y la etiqueta de
contenido generado con IA.
"""
from __future__ import annotations

from ..dominio.serie import Proyecto
from .resultado import Resultado
from .toma import es_vertical


def valida_episodio(tecnico: dict, *, proyecto: Proyecto, etiqueta_ia: bool = False,
                    cortes_esperados: int | None = None) -> Resultado:
    """El episodio montado: duración mínima de plataforma y etiqueta de IA.

    TikTok Creator Rewards exige más de 60 s; por eso el proyecto trabaja en 61–90 s.
    La etiqueta de IA es obligatoria en las tres plataformas y la exige además el
    AI Act art. 50 desde el 02-08-2026.
    """
    r = Resultado()
    ancho, alto = int(tecnico["ancho"]), int(tecnico["alto"])
    if not es_vertical(ancho, alto):
        r.error("NO_ES_VERTICAL", f"{ancho}×{alto} no es 9:16", "vertical")
    if f"{ancho}x{alto}" != proyecto.resolucion_final:
        r.aviso("RESOLUCION_FINAL",
                f"{ancho}×{alto}; el máster final del proyecto es {proyecto.resolucion_final}")
    if round(float(tecnico["fps"])) != proyecto.fps:
        r.error("FPS_DISTINTO", f"{tecnico['fps']} fps; el proyecto entrega a {proyecto.fps}")

    duracion = float(tecnico["duracion"])
    if duracion < proyecto.duracion_min:
        r.error("EPISODIO_CORTO",
                f"{duracion:.1f} s; {proyecto.plataforma} exige un mínimo efectivo de "
                f"{proyecto.duracion_min:g} s", "plataformas")
    if duracion > proyecto.duracion_objetivo_max:
        r.aviso("EPISODIO_LARGO",
                f"{duracion:.1f} s por encima del objetivo ({proyecto.duracion_objetivo_max} s)")

    if proyecto.exige_etiqueta_ia and not etiqueta_ia:
        r.error("SIN_ETIQUETA_IA",
                "falta la declaración de contenido generado con IA "
                "(obligatoria en la plataforma y en el AI Act art. 50)", "plataformas")
    if cortes_esperados is not None:
        detectados = int(tecnico.get("cortes", cortes_esperados))
        if detectados != cortes_esperados:
            r.aviso("CORTES_INESPERADOS",
                    f"{detectados} cortes detectados, {cortes_esperados} esperados")
    return r
