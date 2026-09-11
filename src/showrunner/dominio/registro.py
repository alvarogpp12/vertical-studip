"""`registry.json` como contrato ejecutable.

Hasta ahora el registro era honor system: ningún código lo leía ni lo escribía, así
que R-01 («nada se rueda sin estar en el registro») y R-02 («descriptores palabra
por palabra») no se podían aplicar. Este módulo es el árbitro: resuelve `@tag` →
descriptor y URLs, y rechaza lo que no está registrado.
"""
from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .identidad import SECCION_POR_TIPO, IdInvalido, Tag

TipoReferencia = Literal["cara", "hoja", "localizacion", "prop", "movimiento", "voz"]
EstadoAsset = Literal["pendiente", "aprobado", "retirado"]


class TagDesconocido(KeyError):
    """Se ha pedido un asset que no está en el registro (R-01)."""

    def __init__(self, tag: str, disponibles: list[str] | None = None):
        self.tag = tag
        extra = f" Disponibles: {sorted(disponibles)}" if disponibles else ""
        super().__init__(f"{tag} no está en registry.json (R-01).{extra}")


class Referencia(BaseModel):
    """Una imagen o vídeo que el modelo recibe como referencia.

    `tipo` importa: R-05 prohíbe regenerar el primer plano original de la cara, así
    que las referencias `cara` nacen congeladas.
    """

    model_config = ConfigDict(extra="forbid")

    url: str
    tipo: TipoReferencia
    congelada: bool = False
    creada_con: str = ""
    notas: str = ""

    @model_validator(mode="after")
    def _cara_congelada(self) -> Referencia:
        if self.tipo == "cara":
            self.congelada = True  # R-05
        return self


class Asset(BaseModel):
    """Personaje, localización, prop o voz. El descriptor está congelado (R-02)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    descriptor: str = ""
    referencias: list[Referencia] = Field(default_factory=list)
    estado: EstadoAsset = "pendiente"
    version: int = 1
    creado_con: str = ""
    voz_lock: str = ""
    mapa: str = ""
    notas: str = ""

    @model_validator(mode="after")
    def _coherencia(self) -> Asset:
        tag = Tag.parse(self.id)
        if tag.version != self.version:
            raise ValueError(
                f"{self.id} declara version={self.version} pero el id dice v{tag.version}. "
                "Un estado nuevo es un asset nuevo (R-01)."
            )
        return self

    @property
    def tag(self) -> Tag:
        return Tag.parse(self.id)

    @property
    def urls(self) -> list[str]:
        return [r.url for r in self.referencias]

    def referencias_de(self, tipo: TipoReferencia) -> list[Referencia]:
        return [r for r in self.referencias if r.tipo == tipo]

    @property
    def cara_congelada(self) -> Referencia | None:
        """R-05: la cara original, que no se vuelve a generar."""
        caras = self.referencias_de("cara")
        return caras[0] if caras else None


class Registro(BaseModel):
    """El `registry.json` completo de una serie."""

    model_config = ConfigDict(extra="forbid")

    version: int = 1
    serie: str = ""
    personajes: dict[str, Asset] = Field(default_factory=dict)
    localizaciones: dict[str, Asset] = Field(default_factory=dict)
    props: dict[str, Asset] = Field(default_factory=dict)
    voces: dict[str, Asset] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _claves_coherentes(self) -> Registro:
        for tipo, seccion in SECCION_POR_TIPO.items():
            for clave, asset in getattr(self, seccion).items():
                if clave != asset.id:
                    raise ValueError(f"la clave «{clave}» no coincide con el id «{asset.id}»")
                if asset.tag.tipo != tipo:
                    raise ValueError(
                        f"«{clave}» está en {seccion} pero es de tipo {asset.tag.tipo}")
        return self

    # -- lectura -----------------------------------------------------------
    def assets(self) -> Iterator[Asset]:
        for seccion in SECCION_POR_TIPO.values():
            yield from getattr(self, seccion).values()

    @property
    def tags(self) -> list[str]:
        return [a.id for a in self.assets()]

    def existe(self, tag: str) -> bool:
        try:
            self.resolver(tag)
        except (TagDesconocido, IdInvalido):
            return False
        return True

    def resolver(self, tag: str) -> Asset:
        """`@tag` → Asset. Lanza `TagDesconocido` si no está registrado (R-01)."""
        try:
            parsed = Tag.parse(tag)
        except IdInvalido:
            raise TagDesconocido(tag, self.tags) from None
        seccion: dict[str, Asset] = getattr(self, parsed.seccion)
        if tag not in seccion:
            raise TagDesconocido(tag, self.tags)
        return seccion[tag]

    def descriptor(self, tag: str) -> str:
        """El texto que hay que pegar palabra por palabra en el prompt (R-02)."""
        return self.resolver(tag).descriptor

    def urls(self, *tags: str) -> list[str]:
        """URLs de referencia de varios tags, sin repetir y en orden."""
        vistas: dict[str, None] = {}
        for tag in tags:
            for url in self.resolver(tag).urls:
                vistas.setdefault(url, None)
        return list(vistas)

    def aprobados(self) -> list[Asset]:
        return [a for a in self.assets() if a.estado == "aprobado"]

    # -- escritura ---------------------------------------------------------
    def anadir(self, asset: Asset) -> Asset:
        """Alta o reemplazo de un asset en su sección."""
        seccion: dict[str, Asset] = getattr(self, asset.tag.seccion)
        seccion[asset.id] = asset
        return asset

    def retirar(self, tag: str) -> Asset:
        asset = self.resolver(tag)
        asset.estado = "retirado"
        return asset


def cargar(ruta: Path) -> Registro:
    return Registro.model_validate_json(Path(ruta).read_text(encoding="utf-8"))


def guardar(registro: Registro, ruta: Path) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(registro.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return ruta
