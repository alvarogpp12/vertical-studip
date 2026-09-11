"""BytePlus ModelArk (API oficial de ByteDance) — tareas asíncronas de generación de vídeo.

VERIFICAR con la primera llamada real: el formato sigue la API de tareas de ModelArk
(POST /contents/generations/tasks, GET /contents/generations/tasks/{id}).
Documentación: https://docs.byteplus.com/en/docs/ModelArk/1520757
"""
from __future__ import annotations

import time
from pathlib import Path

import httpx

from ..config import env
from .base import PeticionVideo, Proveedor, ResultadoVideo
from .descarga import descargar


class BytePlusProveedor(Proveedor):
    @property
    def model_id(self) -> str | None:
        return env(self.spec["model_env"])

    def _headers(self):
        return {"Authorization": f"Bearer {env('ARK_API_KEY')}", "Content-Type": "application/json"}

    def comprobar(self):
        if not env("ARK_API_KEY"):
            return False, "Falta ARK_API_KEY en .env"
        if not self.model_id:
            return False, f"Falta {self.spec['model_env']} (ID del modelo en la consola ModelArk)"
        return True, f"clave e ID presentes ({self.model_id})"

    def _body(self, p: PeticionVideo) -> dict:
        content: list[dict] = [{"type": "text", "text": p.prompt}]
        if p.primer_fotograma:
            content.append({"type": "image_url", "image_url": {"url": p.primer_fotograma},
                            "role": "first_frame"})
        for url in p.imagenes:
            content.append({"type": "image_url", "image_url": {"url": url},
                            "role": "reference_image"})
        for url in p.videos:
            content.append({"type": "video_url", "video_url": {"url": url},
                            "role": "reference_video"})
        for url in p.audios:
            content.append({"type": "audio_url", "audio_url": {"url": url},
                            "role": "reference_audio"})
        body = {
            "model": self.model_id,
            "content": content,
            "resolution": p.resolucion,
            "ratio": p.aspect_ratio,
            "duration": p.duracion,
            "generate_audio": p.audio,
            "watermark": False,
        }
        if p.seed is not None:
            body["seed"] = p.seed
        return body

    def generar(self, p: PeticionVideo, destino: Path) -> ResultadoVideo:
        base = env("ARK_BASE_URL", "https://ark.ap-southeast.bytepluses.com/api/v3")
        with httpx.Client(timeout=60) as c:
            r = c.post(f"{base}/contents/generations/tasks", headers=self._headers(),
                       json=self._body(p))
            if r.status_code >= 400:
                raise RuntimeError(f"ModelArk {r.status_code}: {r.text}")
            task_id = r.json()["id"]
            t0 = time.time()
            while True:
                s = c.get(f"{base}/contents/generations/tasks/{task_id}",
                          headers=self._headers()).json()
                estado = s.get("status")
                if estado == "succeeded":
                    break
                if estado in ("failed", "cancelled", "expired"):
                    raise RuntimeError(f"ModelArk tarea {estado}: {s.get('error')}")
                if time.time() - t0 > 900:
                    raise TimeoutError("ModelArk: más de 15 min esperando")
                time.sleep(5)
        url = s["content"]["video_url"]
        return ResultadoVideo(modelo=self.nombre, url=url, ruta_local=descargar(url, destino),
                              task_id=task_id, seed=s.get("seed"), bruto=s)
