"""Referencias locales → URL pública.

Los modelos de vídeo sólo aceptan referencias por URL. Se daba por hecho que hacía
falta montar R2 (issue #5); `fal_client.upload_file()` resuelve lo mismo con cero
infraestructura, y las imágenes que genera fal ya vienen como URL de `fal.media`.

R2 sigue teniendo sentido para archivo canónico versionado o si se llama a
BytePlus ModelArk directo sin pasar por fal. No se implementa aquí.
"""
from __future__ import annotations

from pathlib import Path

from ..config import env

PREFIJOS_URL = ("http://", "https://")


class SubidaNoDisponible(RuntimeError):
    pass


def es_url(valor: str | Path) -> bool:
    return str(valor).startswith(PREFIJOS_URL)


def subir(ruta: Path | str) -> str:
    """Sube un archivo local y devuelve su URL pública."""
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(ruta)
    if not env("FAL_KEY"):
        raise SubidaNoDisponible(
            "Falta FAL_KEY en .env: sin ella no hay dónde publicar las referencias."
        )
    try:
        import fal_client
    except ImportError as e:  # pragma: no cover - depende del entorno
        raise SubidaNoDisponible(
            "Falta el paquete fal-client (`uv sync`) para subir referencias."
        ) from e
    return fal_client.upload_file(str(ruta))


def subir_muchos(rutas: list[Path | str]) -> list[str]:
    return [subir(r) for r in rutas]


def asegurar_url(valor: Path | str) -> str:
    """Devuelve `valor` si ya es una URL; si es un archivo local, lo sube."""
    return str(valor) if es_url(valor) else subir(valor)
