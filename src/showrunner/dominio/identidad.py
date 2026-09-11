"""Identificadores canónicos: planos, episodios, tags de asset y slugs.

Decisión de la fase A: **una sola convención de id de plano**, `s01_ep01_sh003`
(con temporada). La convención corta `ep01_sh001` que usaban las plantillas queda
retirada: dos convenciones incompatibles hacían imposible cruzar el shotlist con
el ledger.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

TipoAsset = Literal["char", "loc", "prop", "voz"]
TIPOS_ASSET: tuple[str, ...] = ("char", "loc", "prop", "voz")

SECCION_POR_TIPO: dict[str, str] = {
    "char": "personajes",
    "loc": "localizaciones",
    "prop": "props",
    "voz": "voces",
}
TIPO_POR_SECCION: dict[str, str] = {v: k for k, v in SECCION_POR_TIPO.items()}

RE_PLANO = re.compile(r"^s(?P<temporada>\d{2})_ep(?P<episodio>\d{2})_sh(?P<plano>\d{3})$")
RE_EPISODIO = re.compile(r"^s(?P<temporada>\d{2})_ep(?P<episodio>\d{2})$")
RE_TAG = re.compile(
    r"^@(?P<tipo>char|loc|prop|voz)_(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)"
    r"_(?P<nombre>[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)_v(?P<version>\d+)$"
)
#: Busca tags dentro de un texto libre (un prompt). Deliberadamente laxo: captura
#: también los tags mal formados para poder señalarlos como error.
RE_TAG_EN_TEXTO = re.compile(r"@[A-Za-z][A-Za-z0-9_\-]*")


class IdInvalido(ValueError):
    """Un identificador no cumple la convención del proyecto."""


def sin_acentos(texto: str) -> str:
    """ASCII equivalente, conservando mayúsculas: «Cañón» → `Canon`."""
    plano = unicodedata.normalize("NFKD", texto)
    plano = "".join(c for c in plano if not unicodedata.combining(c))
    return plano.encode("ascii", "ignore").decode("ascii")


def slugify(texto: str) -> str:
    """Slug ASCII estable. Normaliza Unicode: «Cañón Rojo» → `canon-rojo`."""
    s = re.sub(r"[^a-z0-9]+", "-", sin_acentos(texto).lower()).strip("-")
    return s or "serie"


@dataclass(frozen=True, order=True)
class IdPlano:
    """`s01_ep01_sh003` descompuesto y validado."""

    temporada: int
    episodio: int
    plano: int

    def __post_init__(self) -> None:
        for campo, valor, tope in (
            ("temporada", self.temporada, 99),
            ("episodio", self.episodio, 99),
            ("plano", self.plano, 999),
        ):
            if not 1 <= valor <= tope:
                raise IdInvalido(f"{campo}={valor} fuera de rango (1–{tope})")

    @classmethod
    def parse(cls, texto: str) -> IdPlano:
        m = RE_PLANO.match(texto.strip())
        if not m:
            raise IdInvalido(
                f"«{texto}» no es un id de plano. Formato: s01_ep01_sh003 "
                "(la convención corta ep01_sh001 está retirada)."
            )
        return cls(int(m["temporada"]), int(m["episodio"]), int(m["plano"]))

    def __str__(self) -> str:
        return f"s{self.temporada:02d}_ep{self.episodio:02d}_sh{self.plano:03d}"

    @property
    def id_episodio(self) -> str:
        return f"s{self.temporada:02d}_ep{self.episodio:02d}"

    @property
    def carpeta_episodio(self) -> str:
        """Nombre de carpeta en disco: `proyectos/<serie>/episodios/ep01/`."""
        return f"ep{self.episodio:02d}"

    def siguiente(self) -> IdPlano:
        return IdPlano(self.temporada, self.episodio, self.plano + 1)


def id_episodio(temporada: int, episodio: int) -> str:
    if not 1 <= temporada <= 99 or not 1 <= episodio <= 99:
        raise IdInvalido(f"temporada/episodio fuera de rango: {temporada}/{episodio}")
    return f"s{temporada:02d}_ep{episodio:02d}"


def parse_episodio(texto: str) -> tuple[int, int]:
    m = RE_EPISODIO.match(texto.strip())
    if not m:
        raise IdInvalido(f"«{texto}» no es un id de episodio. Formato: s01_ep01")
    return int(m["temporada"]), int(m["episodio"])


@dataclass(frozen=True, order=True)
class Tag:
    """`@char_cañon-rojo_Nadia_v1` descompuesto y validado."""

    tipo: str
    slug: str
    nombre: str
    version: int

    @classmethod
    def parse(cls, texto: str) -> Tag:
        m = RE_TAG.match(texto.strip())
        if not m:
            raise IdInvalido(
                f"«{texto}» no es un tag válido. Formato: @tipo_slugserie_Nombre_vN "
                f"con tipo en {TIPOS_ASSET}."
            )
        return cls(m["tipo"], m["slug"], m["nombre"], int(m["version"]))

    @classmethod
    def nuevo(cls, tipo: str, serie: str, nombre: str, version: int = 1) -> Tag:
        if tipo not in TIPOS_ASSET:
            raise IdInvalido(f"tipo de asset desconocido: {tipo}")
        limpio = re.sub(r"[^A-Za-z0-9]+", "", sin_acentos(nombre))
        if not limpio:
            raise IdInvalido(f"nombre de asset vacío tras normalizar: {nombre!r}")
        return cls(tipo, slugify(serie), limpio, version)

    def __str__(self) -> str:
        return f"@{self.tipo}_{self.slug}_{self.nombre}_v{self.version}"

    @property
    def seccion(self) -> str:
        return SECCION_POR_TIPO[self.tipo]

    def con_version(self, version: int) -> Tag:
        """R-01: un estado nuevo es un asset nuevo, no una edición del anterior."""
        return Tag(self.tipo, self.slug, self.nombre, version)


def tags_en_texto(texto: str) -> list[str]:
    """Todos los `@algo` que aparecen en un texto, en orden y sin repetir."""
    vistos: dict[str, None] = {}
    for bruto in RE_TAG_EN_TEXTO.findall(texto):
        vistos.setdefault(bruto, None)
    return list(vistos)
