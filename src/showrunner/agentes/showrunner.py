"""Agente 1 · showrunner: idea → 3 conceptos → biblia.

`claude-opus-5` con effort `xhigh`: es trabajo largo, de una sola pasada y de mucho
valor —todo lo que viene después cuelga de aquí—. El coste en LLM es despreciable
frente al de un solo plano de vídeo.
"""
from __future__ import annotations

from ..config import ROOT
from ..dominio.serie import MINIMO_PLATAFORMA, Proyecto
from ..valida.biblia import valida_salida_showrunner
from .base import Agente, Contexto, bloque, leer, preguntar_validando
from .cliente import ClienteLLM
from .contratos import SalidaShowrunner, Sobre

CONOCIMIENTO = ROOT / "docs" / "conocimiento"


def agente(cliente: ClienteLLM | None = None) -> Agente:
    kwargs = {"cliente": cliente} if cliente is not None else {}
    return Agente(nombre="showrunner", skill="showrunner", modelo="claude-opus-5",
                  effort="xhigh", max_tokens=32000, **kwargs)


def _contexto() -> Contexto:
    return Contexto(estable=[
        bloque("Políticas de plataforma y monetización",
               leer(CONOCIMIENTO / "03_plataformas_y_monetizacion.md")),
        bloque("Qué sabe hacer y qué hace mal el modelo de vídeo",
               leer(CONOCIMIENTO / "00_investigacion_sistema.md")),
    ])


def _peticion(idea: str, titulo: str, proyecto: Proyecto, n_episodios: int) -> str:
    minimo = MINIMO_PLATAFORMA.get(proyecto.plataforma, 0.0)
    exigencia = f" (exige más de {minimo - 1:g} s por vídeo)" if minimo else ""
    return f"""
Idea de partida: {idea}
Título de trabajo: {titulo}
Plataforma principal: {proyecto.plataforma}{exigencia}
Duración por episodio: {proyecto.duracion_objetivo_min}–{proyecto.duracion_objetivo_max} s (9:16).

Trabajo:
1. Propón 3 conceptos distintos y puntúa su producibilidad con IA (máximo 3 personajes
   y 3 localizaciones; evita acción difícil y efectos).
2. Elige uno y explica por qué en una frase.
3. Escribe la biblia completa del elegido: descriptores congelados en inglés (se pegarán
   palabra por palabra en cada prompt), anclas de identidad, AUDIO LOCK por personaje,
   mapa espacial vertical por localización, y los riesgos de producción.
4. Escribe el STYLE PREFIX y los CONSTRAINTS, inmutables durante toda la serie.
5. Planifica {n_episodios} episodios y haz la prueba de estrés de al menos el primero.

Los nombres de personajes y localizaciones van dentro de un @tag: nombre propio, sin
espacios ni acentos.
""".strip()


def crear_biblia(idea: str, titulo: str, *, plataforma: str = "tiktok", n_episodios: int = 6,
                 cliente: ClienteLLM | None = None,
                 proyecto: Proyecto | None = None) -> Sobre:
    """Idea (1–3 frases) → conceptos, biblia, estilo, temporada y prueba de estrés."""
    proyecto = proyecto or Proyecto(slug="tmp", titulo=titulo, plataforma=plataforma)
    return preguntar_validando(
        agente(cliente),
        _peticion(idea, titulo, proyecto, n_episodios),
        SalidaShowrunner,
        Contexto(serie=proyecto.slug, estable=_contexto().estable),
        valida_salida_showrunner,
    )
