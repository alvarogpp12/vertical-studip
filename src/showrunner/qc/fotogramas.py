"""Extrae fotogramas clave (inicio, medio, final + cada N s) para revisión visual."""
from __future__ import annotations

import subprocess
from pathlib import Path

from .sonda import sondear


def extraer(video: Path, carpeta: Path, cada_seg: float = 2.0) -> list[Path]:
    carpeta.mkdir(parents=True, exist_ok=True)
    dur = sondear(video)["duracion"]
    fin = max(dur - 0.05, 0.0)  # el ultimo fotograma esta antes de dur; pedir dur exacto no devuelve nada
    tiempos = sorted({0.0, round(dur / 2, 2), fin}
                     | {min(round(t * cada_seg, 2), fin) for t in range(int(dur // cada_seg) + 1)})
    rutas = []
    for t in tiempos:
        ruta = carpeta / f"{video.stem}_{t:06.2f}s.jpg"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", str(video),
                        "-frames:v", "1", "-q:v", "2", str(ruta)], check=True)
        if ruta.exists():
            rutas.append(ruta)
    return rutas
