"""fal.ai vía API de cola REST (https://queue.fal.run)."""
from __future__ import annotations

import time
from pathlib import Path

import httpx

from ..config import env
from .base import PeticionVideo, Proveedor, ResultadoVideo
from .descarga import descargar

QUEUE = "https://queue.fal.run"


class FalProveedor(Proveedor):
    def _headers(self) -> dict:
        return {"Authorization": f"Key {env('FAL_KEY')}", "Content-Type": "application/json"}

    def comprobar(self):
        if not env("FAL_KEY"):
            return False, "Falta FAL_KEY en .env"
        return True, "FAL_KEY presente"

    def _input(self, p: PeticionVideo) -> dict:
        ep = self.spec["endpoint"]
        if "seedance" in ep:
            data = {
                "prompt": p.prompt,
                "resolution": p.resolucion,
                "duration": str(p.duracion),
                "aspect_ratio": p.aspect_ratio,
                "generate_audio": p.audio,
                "image_urls": p.imagenes,
                "video_urls": p.videos,
                "audio_urls": p.audios,
            }
        else:  # Kling y otros image-to-video
            data = {
                "prompt": p.prompt,
                "duration": str(p.duracion),
                # El endpoint lo llama start_image_url y es obligatorio.
                "start_image_url": p.primer_fotograma or (p.imagenes[0] if p.imagenes else None),
                "generate_audio": p.audio,
            }
            if p.negative_prompt:
                data["negative_prompt"] = p.negative_prompt
        if p.seed is not None:
            data["seed"] = p.seed
        return {k: v for k, v in data.items() if v not in (None, [], "")}

    def generar(self, p: PeticionVideo, destino: Path) -> ResultadoVideo:
        ep = self.spec["endpoint"]
        with httpx.Client(timeout=60) as c:
            r = c.post(f"{QUEUE}/{ep}", headers=self._headers(), json=self._input(p))
            r.raise_for_status()
            job = r.json()
            status_url, response_url = job["status_url"], job["response_url"]
            t0 = time.time()
            while True:
                s = c.get(status_url, headers=self._headers()).json()
                if s.get("status") == "COMPLETED":
                    break
                if s.get("status") in ("FAILED", "ERROR"):
                    raise RuntimeError(f"fal falló: {s}")
                if time.time() - t0 > 900:
                    raise TimeoutError("fal: más de 15 min esperando")
                time.sleep(5)
            out = c.get(response_url, headers=self._headers()).json()
        url = out["video"]["url"]
        return ResultadoVideo(
            modelo=self.nombre, url=url, ruta_local=descargar(url, destino),
            task_id=job.get("request_id"), seed=out.get("seed"), bruto=out,
        )
