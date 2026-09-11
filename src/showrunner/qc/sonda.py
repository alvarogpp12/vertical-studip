"""Datos técnicos reales de un clip (resolución, fps, duración, audio)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


def sondear(video: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(video)],
        check=True, capture_output=True, text=True,
    ).stdout
    data = json.loads(out)
    v = next(s for s in data["streams"] if s["codec_type"] == "video")
    num, den = (v.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
    ancho, alto = int(v["width"]), int(v["height"])
    # El contenedor puede durar más que el vídeo si el audio es más largo (pasa con Seedance).
    dur_contenedor = float(data["format"]["duration"])
    try:
        dur_video = float(v["duration"])
    except (KeyError, TypeError, ValueError):
        dur_video = dur_contenedor
    return {
        "ancho": ancho,
        "alto": alto,
        "vertical_9_16": abs(ancho / alto - 9 / 16) < 0.01,
        "fps": round(int(num) / max(int(den), 1), 3),
        "duracion": dur_contenedor,
        "duracion_video": dur_video,
        "codec": v["codec_name"],
        "audio": any(s["codec_type"] == "audio" for s in data["streams"]),
    }
