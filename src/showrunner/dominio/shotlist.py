"""`shotlist.json` como contrato ejecutable: qué se rueda, no qué ha pasado.

Separación deliberada:

* `Plano` es **intención** y se persiste. Es el contrato entre el guionista y el
  director: duración, referencias activas, diálogo, nivel de generación.
* El **estado** de un plano (intentos, coste acumulado, veredicto, toma aprobada)
  NO vive aquí: se pliega desde el log de eventos (`dominio.eventos.plegar`). Un
  campo `estado` guardado a mano puede mentir; un log append-only no.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .identidad import IdPlano, id_episodio, parse_episodio

Nivel = Literal["borrador", "trabajo", "clave"]

#: R-09: el diálogo cabe a ~4 palabras por segundo y el plano acaba con 1 s limpio.
PALABRAS_POR_SEGUNDO = 4.0
COLA_SILENCIO_SEG = 1.0


class Plano(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    beat: int = 1
    duracion: int = Field(5, ge=1, le=30)
    tamano: str = ""
    camara: str = ""
    refs: list[str] = Field(default_factory=list)
    dialogo: str = ""
    nivel: Nivel = "borrador"
    es_master: bool = False          # R-06: máster de 1 s que fija la geografía
    orden_montaje: int = 0
    prompt_path: str | None = None
    seed: int | None = None
    notas: str = ""

    @model_validator(mode="after")
    def _id_valido(self) -> Plano:
        IdPlano.parse(self.id)
        return self

    @property
    def id_plano(self) -> IdPlano:
        return IdPlano.parse(self.id)

    @property
    def palabras_dialogo(self) -> int:
        return len(re.findall(r"[\wÀ-ÿ'’-]+", self.dialogo))

    @property
    def duracion_minima(self) -> float:
        """R-09: palabras/4 + 1 s de cola limpia."""
        if not self.palabras_dialogo:
            return 1.0
        return self.palabras_dialogo / PALABRAS_POR_SEGUNDO + COLA_SILENCIO_SEG

    @property
    def cabe_el_dialogo(self) -> bool:
        return self.duracion >= self.duracion_minima


class Shotlist(BaseModel):
    model_config = ConfigDict(extra="forbid")

    episodio: str                     # s01_ep01
    planos: list[Plano] = Field(default_factory=list)

    @model_validator(mode="after")
    def _coherencia(self) -> Shotlist:
        temporada, numero = parse_episodio(self.episodio)
        vistos: set[str] = set()
        ordenes: set[int] = set()
        for plano in self.planos:
            pid = plano.id_plano
            if (pid.temporada, pid.episodio) != (temporada, numero):
                raise ValueError(f"{plano.id} no pertenece al episodio {self.episodio}")
            if plano.id in vistos:
                raise ValueError(f"id de plano repetido: {plano.id}")
            vistos.add(plano.id)
            if plano.orden_montaje:
                if plano.orden_montaje in ordenes:
                    raise ValueError(f"orden_montaje repetido: {plano.orden_montaje}")
                ordenes.add(plano.orden_montaje)
        return self

    @property
    def duracion_total(self) -> int:
        return sum(p.duracion for p in self.planos)

    @property
    def en_orden(self) -> list[Plano]:
        return sorted(self.planos, key=lambda p: (p.orden_montaje or p.id_plano.plano))

    def plano(self, id_: str) -> Plano:
        for p in self.planos:
            if p.id == id_:
                return p
        raise KeyError(f"{id_} no está en el shotlist de {self.episodio}")

    def tags_usados(self) -> list[str]:
        vistos: dict[str, None] = {}
        for p in self.planos:
            for tag in p.refs:
                vistos.setdefault(tag, None)
        return list(vistos)


def cargar(ruta: Path) -> Shotlist:
    return Shotlist.model_validate_json(Path(ruta).read_text(encoding="utf-8"))


def guardar(shotlist: Shotlist, ruta: Path) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(shotlist.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return ruta


def vacio(temporada: int, episodio: int) -> Shotlist:
    return Shotlist(episodio=id_episodio(temporada, episodio))
