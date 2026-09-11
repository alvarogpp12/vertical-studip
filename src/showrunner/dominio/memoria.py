"""Memoria de la serie: qué ha pasado ya, para que el episodio siguiente encaje.

Sin esto, cada episodio se escribe como si fuera el primero: se repiten cliffhangers,
se resuelve dos veces lo mismo y el arco de temporada no avanza. Es el «vuelve a la
sala de guion» de `01_objetivo_showrunner.md`, en la parte que no depende de la
analítica.

Se construye leyendo lo que ya está en disco (`temporada.json` y los `guion.json`
escritos), no de un resumen que alguien tenga que mantener a mano.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .identidad import parse_episodio


@dataclass
class Episodio:
    id: str
    numero: int
    titulo: str = ""
    gancho: str = ""
    giro: str = ""
    cliffhanger: str = ""
    escrito: bool = False

    def como_linea(self) -> str:
        estado = "escrito" if self.escrito else "planificado"
        partes = [f"- {self.id} «{self.titulo or 'sin título'}» ({estado})"]
        for etiqueta, valor in (("gancho", self.gancho), ("giro", self.giro),
                                ("cliffhanger", self.cliffhanger)):
            if valor:
                partes.append(f"    {etiqueta}: {valor}")
        return "\n".join(partes)


def _de_temporada(base: Path) -> dict[int, Episodio]:
    ruta = Path(base) / "temporada.json"
    if not ruta.exists():
        return {}
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    episodios: dict[int, Episodio] = {}
    for fila in datos.get("episodios", []):
        try:
            _, numero = parse_episodio(fila["id"])
        except Exception:
            continue
        episodios[numero] = Episodio(id=fila["id"], numero=numero,
                                     titulo=fila.get("titulo", ""),
                                     gancho=fila.get("gancho", ""), giro=fila.get("giro", ""),
                                     cliffhanger=fila.get("cliffhanger", ""))
    return episodios


def _de_guiones(base: Path, episodios: dict[int, Episodio]) -> None:
    """Lo escrito manda sobre lo planificado: un guion ya existente es el hecho."""
    for ruta in sorted(Path(base).glob("episodios/*/guion.json")):
        try:
            numero = int(ruta.parent.name.removeprefix("ep"))
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except (ValueError, json.JSONDecodeError):
            continue
        episodio = episodios.setdefault(numero, Episodio(id=f"s01_ep{numero:02d}", numero=numero))
        episodio.titulo = datos.get("titulo") or episodio.titulo
        episodio.gancho = datos.get("gancho_3s") or episodio.gancho
        episodio.cliffhanger = datos.get("cliffhanger") or episodio.cliffhanger
        giros = [b.get("texto", "") for b in datos.get("beats", []) if b.get("funcion") == "giro"]
        episodio.giro = giros[0] if giros else episodio.giro
        episodio.escrito = True


def episodios(base: Path) -> list[Episodio]:
    lista = _de_temporada(base)
    _de_guiones(base, lista)
    return [lista[n] for n in sorted(lista)]


def resumen(base: Path, hasta: str) -> str:
    """Qué hay que saber para escribir `hasta`, en texto para el prompt del guionista."""
    _, numero = parse_episodio(hasta)
    anteriores = [e for e in episodios(base) if e.numero < numero]
    actual = next((e for e in episodios(base) if e.numero == numero), None)

    partes = []
    if anteriores:
        escritos = [e for e in anteriores if e.escrito]
        partes.append("## Episodios anteriores\n" + "\n".join(e.como_linea() for e in anteriores))
        abierto = next((e.cliffhanger for e in reversed(escritos) if e.cliffhanger), "")
        if abierto:
            partes.append(f"## Cliffhanger que quedó abierto\n{abierto}\n"
                          "Recógelo en los primeros 10 segundos.")
        usados = [e.cliffhanger for e in escritos if e.cliffhanger]
        if usados:
            partes.append("## Cliffhangers ya usados (no los repitas)\n"
                          + "\n".join(f"- {c}" for c in usados))
    else:
        partes.append("## Episodios anteriores\nNinguno: este es el primero de la serie.")
    if actual and (actual.titulo or actual.gancho or actual.giro or actual.cliffhanger):
        partes.append(f"## Lo que la temporada planifica para {hasta}\n{actual.como_linea()}")
    return "\n\n".join(partes)
