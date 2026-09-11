"""Detecta cortes dentro de un clip (útil para saber si el modelo metió planos no pedidos)."""
from __future__ import annotations

from pathlib import Path

from scenedetect import ContentDetector, detect


def cortes(video: Path, umbral: float = 27.0) -> list[tuple[float, float]]:
    escenas = detect(str(video), ContentDetector(threshold=umbral))
    return [(round(a.get_seconds(), 2), round(b.get_seconds(), 2)) for a, b in escenas]
