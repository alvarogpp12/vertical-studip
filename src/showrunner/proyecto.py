"""Crea la carpeta de una serie nueva a partir de la plantilla.

Antes se copiaban las plantillas tal cual: los marcadores `{TÍTULO}`/`{SLUG}`
quedaban sin sustituir y `registry.serie` vacío, así que ninguna serie recién
creada pasaba una validación. Ahora la plantilla se rellena de verdad y se escribe
`proyecto.json` con la plataforma de destino y el rastro de aprobaciones.
"""
from __future__ import annotations

from pathlib import Path

from .config import ROOT
from .dominio import registro as reg
from .dominio import serie as ser
from .dominio.identidad import slugify

PLANTILLA = ROOT / "templates" / "proyecto"
#: Extensiones donde tiene sentido sustituir marcadores.
TEXTO = {".md", ".json", ".txt", ".yaml", ".yml"}


def _sustituir(texto: str, titulo: str, slug: str) -> str:
    for marcador in ("{TÍTULO}", "{TITULO}", "{título}", "{titulo}"):
        texto = texto.replace(marcador, titulo)
    for marcador in ("{SLUG}", "{slug}"):
        texto = texto.replace(marcador, slug)
    return texto


def crear(nombre: str, idea: str = "", plataforma: str = "tiktok") -> Path:
    """Crea `proyectos/<slug>/` con las plantillas ya rellenadas."""
    slug = slugify(nombre)
    destino = ROOT / "proyectos" / slug
    if destino.exists():
        raise FileExistsError(f"Ya existe {destino}")

    destino.mkdir(parents=True)
    for origen in sorted(PLANTILLA.rglob("*")):
        relativo = origen.relative_to(PLANTILLA)
        final = destino / relativo
        if origen.is_dir():
            final.mkdir(parents=True, exist_ok=True)
            continue
        final.parent.mkdir(parents=True, exist_ok=True)
        if origen.suffix.lower() in TEXTO:
            final.write_text(
                _sustituir(origen.read_text(encoding="utf-8"), nombre, slug), encoding="utf-8"
            )
        else:
            final.write_bytes(origen.read_bytes())

    # registry.json necesita saber de qué serie es: los tags llevan el slug dentro.
    registro = reg.cargar(destino / "registry.json")
    registro.serie = slug
    reg.guardar(registro, destino / "registry.json")

    proyecto = ser.Proyecto(slug=slug, titulo=nombre, idea=idea, plataforma=plataforma)
    ser.guardar(proyecto, destino / "proyecto.json")
    (destino / "idea.md").write_text(f"# {nombre}\n\n{idea}\n", encoding="utf-8")
    return destino


def ruta(slug_o_nombre: str) -> Path:
    """Carpeta de una serie ya creada."""
    candidata = ROOT / "proyectos" / slug_o_nombre
    if candidata.is_dir():
        return candidata
    candidata = ROOT / "proyectos" / slugify(slug_o_nombre)
    if candidata.is_dir():
        return candidata
    raise FileNotFoundError(f"No existe la serie «{slug_o_nombre}» en proyectos/")


def cargar(slug_o_nombre: str) -> tuple[ser.Proyecto, reg.Registro]:
    base = ruta(slug_o_nombre)
    return ser.cargar(base / "proyecto.json"), reg.cargar(base / "registry.json")
