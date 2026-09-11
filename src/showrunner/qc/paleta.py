"""Paleta dominante (hex) y distancia de color ΔE entre una toma y su referencia de estilo."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def paleta(imagen: Path, k: int = 5) -> list[tuple[str, float]]:
    img = cv2.imread(str(imagen))
    if img is None:
        raise FileNotFoundError(imagen)
    img = cv2.resize(img, (160, 160))
    px = img.reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centros = cv2.kmeans(px, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    cuentas = np.bincount(labels.flatten(), minlength=k) / len(labels)
    orden = np.argsort(-cuentas)
    res = []
    for i in orden:
        b, g, r = [int(x) for x in centros[i]]
        res.append((f"#{r:02x}{g:02x}{b:02x}", round(float(cuentas[i]), 3)))
    return res


def delta_e_medio(a: Path, b: Path) -> float:
    """ΔE (CIE76) entre los colores medios en Lab.

    <5 muy parecido · 5–15 deriva visible · >15 otro look.
    """
    def lab_medio(p: Path):
        img = cv2.imread(str(p))
        lab = cv2.cvtColor(cv2.resize(img, (160, 160)), cv2.COLOR_BGR2LAB).astype(np.float32)
        lab[..., 0] *= 100 / 255
        lab[..., 1:] -= 128
        return lab.reshape(-1, 3).mean(axis=0)
    return round(float(np.linalg.norm(lab_medio(a) - lab_medio(b))), 2)
