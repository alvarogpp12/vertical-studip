"""Crea la carpeta de una serie nueva a partir de la plantilla."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from .config import ROOT

PLANTILLA = ROOT / "templates" / "proyecto"


def slugify(texto: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")
    return s or "serie"


def crear(nombre: str, idea: str = "") -> Path:
    destino = ROOT / "proyectos" / slugify(nombre)
    if destino.exists():
        raise FileExistsError(f"Ya existe {destino}")
    shutil.copytree(PLANTILLA, destino)
    (destino / "idea.md").write_text(f"# {nombre}\n\n{idea}\n", encoding="utf-8")
    return destino
