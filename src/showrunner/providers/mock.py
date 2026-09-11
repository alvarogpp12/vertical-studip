"""Proveedor de prueba: crea un clip vertical local con ffmpeg (coste 0)."""
from __future__ import annotations

import subprocess
from pathlib import Path

from .base import PeticionVideo, Proveedor, ResultadoVideo

TAMANOS = {"480p": "480x854", "720p": "720x1280", "1080p": "1080x1920"}


class MockProveedor(Proveedor):
    def generar(self, p: PeticionVideo, destino: Path) -> ResultadoVideo:
        destino.parent.mkdir(parents=True, exist_ok=True)
        size = TAMANOS.get(p.resolucion, "480x854")
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
             "-i", f"testsrc2=size={size}:rate=24:duration={p.duracion}",
             "-f", "lavfi", "-i", f"sine=frequency=440:duration={p.duracion}",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(destino)],
            check=True,
        )
        return ResultadoVideo(modelo=self.nombre, ruta_local=destino, task_id="mock")
