from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

CONFIG = ROOT / "config"


def env(name: str, default: str | None = None) -> str | None:
    val = os.getenv(name, default)
    return val if val not in ("", None) else default


@lru_cache(maxsize=1)
def _catalogo() -> dict:
    with open(CONFIG / "modelos.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def cargar_modelos() -> dict:
    """Catálogo de modelos de vídeo. Cacheado: se lee en cada estimación y ruteo."""
    return _catalogo()["modelos"]


def cargar_modelos_imagen() -> dict:
    """Catálogo de modelos de imagen (hojas de personaje y localizaciones)."""
    return _catalogo().get("modelos_imagen", {})


def cargar_modelos_llm() -> dict:
    """Catálogo de modelos de lenguaje: los que mueven a los agentes."""
    return _catalogo().get("modelos_llm", {})


def recargar_catalogo() -> None:
    _catalogo.cache_clear()


@lru_cache(maxsize=1)
def cargar_denylist() -> dict:
    """Vocabulario prohibido en prompts: filtros de los modelos y políticas de plataforma."""
    ruta = CONFIG / "denylist.yaml"
    if not ruta.exists():
        return {}
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def presupuesto() -> tuple[float, float]:
    """(máximo por tarea, máximo por día) en USD.

    El tope diario por defecto (60 $) tiene que caber por encima del coste objetivo
    de un episodio (30–45 $); con los 25 $ anteriores, un episodio se autobloqueaba
    a mitad de producción.
    """
    return float(env("BUDGET_MAX_PER_JOB", "3")), float(env("BUDGET_MAX_PER_DAY", "60"))
