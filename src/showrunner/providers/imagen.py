"""Generación de imágenes: hojas de personaje y localizaciones.

Espejo del contrato de vídeo de `base.py`. Sin esto, `registry.referencias[]` no se
puede llenar y ninguna etapa posterior a la biblia es ejecutable: era el bloqueo
duro del proyecto.

Reparto por coste (`02_proveedores_y_costes.md`):
* hojas de personaje → Nano Banana Pro (muchas referencias, consistencia de cara)
* localizaciones y volumen → Seedream 5.0 Pro (un orden de magnitud más barato)
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path

import httpx
from pydantic import BaseModel, Field

from ..config import cargar_modelos_imagen, env
from .descarga import descargar

QUEUE = "https://queue.fal.run"


class PeticionImagen(BaseModel):
    prompt: str
    referencias: list[str] = Field(default_factory=list)   # URLs públicas
    aspect_ratio: str = "1:1"
    n: int = 1
    seed: int | None = None


class ResultadoImagen(BaseModel):
    modelo: str
    urls: list[str] = Field(default_factory=list)
    rutas: list[Path] = Field(default_factory=list)
    seed: int | None = None
    bruto: dict = {}


class ProveedorImagen(ABC):
    def __init__(self, nombre_modelo: str, spec: dict):
        self.nombre = nombre_modelo
        self.spec = spec

    @abstractmethod
    def generar(self, peticion: PeticionImagen, destino: Path) -> ResultadoImagen: ...

    def comprobar(self) -> tuple[bool, str]:
        return True, "ok"


class FalImagen(ProveedorImagen):
    def _headers(self) -> dict:
        return {"Authorization": f"Key {env('FAL_KEY')}", "Content-Type": "application/json"}

    def comprobar(self) -> tuple[bool, str]:
        if not env("FAL_KEY"):
            return False, "Falta FAL_KEY en .env"
        return True, "FAL_KEY presente"

    def _input(self, p: PeticionImagen) -> dict:
        datos = {
            "prompt": p.prompt,
            "num_images": p.n,
            "aspect_ratio": p.aspect_ratio,
            "image_urls": p.referencias,
        }
        if p.seed is not None:
            datos["seed"] = p.seed
        return {k: v for k, v in datos.items() if v not in (None, [], "")}

    def generar(self, p: PeticionImagen, destino: Path) -> ResultadoImagen:
        endpoint = self.spec["endpoint"]
        with httpx.Client(timeout=60) as c:
            r = c.post(f"{QUEUE}/{endpoint}", headers=self._headers(), json=self._input(p))
            r.raise_for_status()
            job = r.json()
            t0 = time.time()
            while True:
                s = c.get(job["status_url"], headers=self._headers()).json()
                if s.get("status") == "COMPLETED":
                    break
                if s.get("status") in ("FAILED", "ERROR"):
                    raise RuntimeError(f"fal falló: {s}")
                if time.time() - t0 > 600:
                    raise TimeoutError("fal: más de 10 min esperando una imagen")
                time.sleep(3)
            out = c.get(job["response_url"], headers=self._headers()).json()
        urls = [img["url"] for img in out.get("images", [])]
        rutas = [
            descargar(url, destino.parent / f"{destino.stem}_{i + 1:02d}{destino.suffix or '.png'}")
            for i, url in enumerate(urls)
        ]
        return ResultadoImagen(modelo=self.nombre, urls=urls, rutas=rutas,
                               seed=out.get("seed"), bruto=out)


class MockImagen(ProveedorImagen):
    """Imágenes locales con ffmpeg, coste 0. Cierra la cadena sin gastar."""

    def generar(self, p: PeticionImagen, destino: Path) -> ResultadoImagen:
        import subprocess

        destino.parent.mkdir(parents=True, exist_ok=True)
        rutas = []
        for i in range(p.n):
            ruta = destino.parent / f"{destino.stem}_{i + 1:02d}{destino.suffix or '.png'}"
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                 "-i", f"color=c=gray:s=768x768:d=1,drawtext=text='{i + 1}':fontsize=96:"
                       "fontcolor=white:x=(w-tw)/2:y=(h-th)/2",
                 "-frames:v", "1", str(ruta)],
                check=True,
            )
            rutas.append(ruta)
        return ResultadoImagen(modelo=self.nombre, rutas=rutas, seed=p.seed)


CLASES_IMAGEN = {"fal": FalImagen, "mock": MockImagen}


def obtener_proveedor_imagen(nombre_modelo: str) -> ProveedorImagen:
    catalogo = cargar_modelos_imagen()
    if nombre_modelo not in catalogo:
        raise KeyError(f"Modelo de imagen desconocido: {nombre_modelo}. "
                       f"Disponibles: {list(catalogo)}")
    spec = catalogo[nombre_modelo]
    return CLASES_IMAGEN[spec["proveedor"]](nombre_modelo, spec)


def estimar_coste_imagen(nombre_modelo: str, p: PeticionImagen) -> float:
    spec = cargar_modelos_imagen()[nombre_modelo]
    extra = max(0, len(p.referencias) - 1) * float(spec.get("precio_ref_extra", 0.0))
    return round((float(spec["precio_img"]) + extra) * p.n, 4)


def elegir_modelo_imagen(uso: str, excluir_mock: bool = True) -> str:
    """El más barato declarado para ese uso (`hojas` | `localizaciones`) y configurado."""
    candidatos = []
    for nombre, spec in cargar_modelos_imagen().items():
        if excluir_mock and spec["proveedor"] == "mock":
            continue
        if uso not in spec.get("usos", []):
            continue
        ok, _ = obtener_proveedor_imagen(nombre).comprobar()
        if ok:
            candidatos.append((float(spec["precio_img"]), nombre))
    if not candidatos:
        raise LookupError(f"Ningún modelo de imagen configurado para uso={uso}")
    return sorted(candidatos)[0][1]
