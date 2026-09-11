"""`proyecto.json`: plataforma de destino, duración objetivo y aprobaciones humanas.

Hasta ahora la aprobación de la biblia era una línea de texto libre
(«Aprobada por: —»). Los tres controles humanos del flujo —biblia, casting y visto
bueno final— pasan a ser estados con rastro auditable: quién, cuándo y sobre qué
versión. Es también el argumento de «dirección editorial demostrable» que piden
las políticas de las plataformas.
"""
from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .identidad import slugify

Plataforma = Literal["tiktok", "youtube", "meta"]
TipoAprobacion = Literal["biblia", "casting", "episodio"]

#: Duración mínima real que impone cada plataforma.
#: TikTok Creator Rewards exige más de 60 s; el resto no fija mínimo, pero el
#: proyecto trabaja siempre en 61–90 s (ver `duracion_min`).
MINIMO_PLATAFORMA: dict[str, float] = {"tiktok": 61.0, "youtube": 0.0, "meta": 0.0}

#: Todas exigen declarar el contenido realista generado con IA.
ETIQUETA_IA_OBLIGATORIA: dict[str, bool] = {"tiktok": True, "youtube": True, "meta": True}


def _hoy() -> str:
    return date.today().isoformat()


class Aprobacion(BaseModel):
    """Un control humano superado, con firma, fecha y versión del material."""

    model_config = ConfigDict(extra="forbid")

    tipo: TipoAprobacion
    por: str
    fecha: str = Field(default_factory=_hoy)
    version: str = "0.1"
    referencia: str = ""     # id de episodio cuando tipo == "episodio"
    notas: str = ""


class Proyecto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    titulo: str
    idea: str = ""
    plataforma: Plataforma = "tiktok"
    plataformas_secundarias: list[Plataforma] = Field(default_factory=list)
    temporada: int = 1
    duracion_objetivo_min: int = 61
    duracion_objetivo_max: int = 90
    fps: int = 24
    resolucion_final: str = "1080x1920"
    creado: str = Field(default_factory=lambda: datetime.now(UTC).isoformat(timespec="seconds"))
    aprobaciones: list[Aprobacion] = Field(default_factory=list)

    @model_validator(mode="after")
    def _rango_coherente(self) -> Proyecto:
        if self.duracion_objetivo_min > self.duracion_objetivo_max:
            raise ValueError("duracion_objetivo_min no puede superar a duracion_objetivo_max")
        return self

    @property
    def plataformas(self) -> list[str]:
        return [self.plataforma, *self.plataformas_secundarias]

    @property
    def duracion_min(self) -> float:
        """Mínimo efectivo: el más exigente entre plataformas y objetivo del proyecto."""
        return max(
            [float(self.duracion_objetivo_min)]
            + [MINIMO_PLATAFORMA.get(p, 0.0) for p in self.plataformas]
        )

    @property
    def exige_etiqueta_ia(self) -> bool:
        return any(ETIQUETA_IA_OBLIGATORIA.get(p, True) for p in self.plataformas)

    def aprobacion(self, tipo: TipoAprobacion, referencia: str = "") -> Aprobacion | None:
        for a in reversed(self.aprobaciones):
            if a.tipo == tipo and (not referencia or a.referencia == referencia):
                return a
        return None

    def aprobado(self, tipo: TipoAprobacion, referencia: str = "") -> bool:
        return self.aprobacion(tipo, referencia) is not None

    def aprobar(self, tipo: TipoAprobacion, por: str, version: str = "0.1",
                referencia: str = "", notas: str = "") -> Aprobacion:
        ap = Aprobacion(tipo=tipo, por=por, version=version, referencia=referencia, notas=notas)
        self.aprobaciones.append(ap)
        return ap


def nuevo(titulo: str, idea: str = "", plataforma: Plataforma = "tiktok") -> Proyecto:
    return Proyecto(slug=slugify(titulo), titulo=titulo, idea=idea, plataforma=plataforma)


def cargar(ruta: Path) -> Proyecto:
    return Proyecto.model_validate_json(Path(ruta).read_text(encoding="utf-8"))


def guardar(proyecto: Proyecto, ruta: Path) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(proyecto.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return ruta
