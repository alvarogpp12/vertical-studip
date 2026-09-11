from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, Field


class PeticionVideo(BaseModel):
    prompt: str
    #: Sólo lo usan los modelos que tienen el campo (Kling). Seedance no lo tiene y
    #: sus negativos van dentro del prompt. Ver docs/conocimiento/04_apis_y_prompting.md.
    negative_prompt: str = ""
    duracion: int = Field(5, ge=1, le=30)
    resolucion: str = "480p"
    aspect_ratio: str = "9:16"
    imagenes: list[str] = []      # URLs públicas de referencias
    videos: list[str] = []
    audios: list[str] = []
    primer_fotograma: str | None = None
    audio: bool = True
    seed: int | None = None


class ResultadoVideo(BaseModel):
    modelo: str
    url: str | None = None
    ruta_local: Path | None = None
    task_id: str | None = None
    seed: int | None = None
    bruto: dict = {}


class Proveedor(ABC):
    def __init__(self, nombre_modelo: str, spec: dict):
        self.nombre = nombre_modelo
        self.spec = spec

    @abstractmethod
    def generar(self, peticion: PeticionVideo, destino: Path) -> ResultadoVideo: ...

    def comprobar(self) -> tuple[bool, str]:
        """Comprobación sin coste: claves e IDs presentes."""
        return True, "ok"
