"""Cómo se citan las referencias dentro del prompt.

Hallazgo del 2026-09-11 (`docs/conocimiento/04_apis_y_prompting.md`): Seedance no
conoce nuestros `@tag`. Su contrato dice, literalmente, «Refer to them in the prompt
as **@Image1, @Image2**, etc.»: las referencias se citan **por posición** en la lista
que se manda en `image_urls`.

Mandábamos las URLs sin citarlas nunca. Es decir: pagábamos por subir hojas de
personaje que el modelo podía estar ignorando.

Este módulo es la traducción entre las dos numeraciones, y **la usan tanto el director
(para escribir el prompt) como el proveedor (para mandar las URLs)**. Si cada uno
calculara el orden por su cuenta, `@Image2` apuntaría a otra imagen y nadie se daría
cuenta.
"""
from __future__ import annotations

from dataclasses import dataclass

from .registro import Registro
from .shotlist import Plano


@dataclass(frozen=True)
class Ranura:
    """Una referencia, con el número por el que el modelo la conoce."""

    indice: int          # empieza en 1
    tag: str
    tipo: str
    url: str

    @property
    def cita(self) -> str:
        return f"@Image{self.indice}"


def ranuras(registro: Registro, tags: list[str], *, maximo: int = 30) -> list[Ranura]:
    """Orden determinista: por tag del plano y, dentro de cada uno, por referencia.

    Se descartan las URLs repetidas —un mismo archivo no ocupa dos ranuras— y las que
    no son públicas, porque el modelo no las puede leer.
    """
    salida: list[Ranura] = []
    vistas: set[str] = set()
    for tag in tags:
        if not registro.existe(tag):
            continue
        for referencia in registro.resolver(tag).referencias:
            if not referencia.url.startswith(("http://", "https://")):
                continue
            if referencia.url in vistas or len(salida) >= maximo:
                continue
            vistas.add(referencia.url)
            salida.append(Ranura(len(salida) + 1, tag, referencia.tipo, referencia.url))
    return salida


def de_plano(registro: Registro, plano: Plano, *, maximo: int = 30) -> list[Ranura]:
    return ranuras(registro, plano.refs, maximo=maximo)


def urls(lista: list[Ranura]) -> list[str]:
    """Lo que va en `image_urls`, en el mismo orden que las citas."""
    return [r.url for r in lista]


def mapa(lista: list[Ranura], registro: Registro) -> str:
    """La tabla que el director necesita para citar bien.

    La guía de terceros insiste en que la etiqueta va **pegada a un sustantivo**
    (`the woman in @Image1`), no suelta.
    """
    if not lista:
        return "(este plano no lleva referencias)"
    filas = []
    for ranura in lista:
        descriptor = registro.descriptor(ranura.tag)
        filas.append(f"- **{ranura.cita}** = {ranura.tag} ({ranura.tipo}): {descriptor}")
    return "\n".join(filas)


def citas_esperadas(lista: list[Ranura]) -> list[str]:
    return [r.cita for r in lista]
