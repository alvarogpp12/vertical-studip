from pathlib import Path

import httpx


def descargar(url: str, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", url, timeout=300, follow_redirects=True) as r:
        r.raise_for_status()
        with destino.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    return destino
