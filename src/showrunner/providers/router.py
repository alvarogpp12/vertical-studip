from __future__ import annotations

from ..config import cargar_modelos
from .base import PeticionVideo, Proveedor
from .byteplus import BytePlusProveedor
from .fal import FalProveedor
from .mock import MockProveedor

CLASES = {"fal": FalProveedor, "byteplus": BytePlusProveedor, "mock": MockProveedor}


def obtener_proveedor(nombre_modelo: str) -> Proveedor:
    modelos = cargar_modelos()
    if nombre_modelo not in modelos:
        raise KeyError(f"Modelo desconocido: {nombre_modelo}. Disponibles: {list(modelos)}")
    spec = modelos[nombre_modelo]
    return CLASES[spec["proveedor"]](nombre_modelo, spec)


def estimar_coste(nombre_modelo: str, p: PeticionVideo) -> float:
    spec = cargar_modelos()[nombre_modelo]
    precios = spec["precio_seg"]
    if p.resolucion not in precios:
        raise ValueError(f"{nombre_modelo} no tiene precio para {p.resolucion}: {list(precios)}")
    return round(precios[p.resolucion] * p.duracion, 4)


def elegir_modelo(nivel: str, p: PeticionVideo, excluir_mock: bool = True) -> str:
    """El más barato del nivel que cumpla resolución, duración y nº de referencias.

    Sólo considera modelos configurados (con su clave y su id presentes).
    """
    candidatos = []
    for nombre, spec in cargar_modelos().items():
        if excluir_mock and spec["proveedor"] == "mock":
            continue
        if spec["nivel"] != nivel or p.resolucion not in spec["precio_seg"]:
            continue
        if p.duracion > spec["max_duracion"]:
            continue
        refs = spec["referencias"]
        if len(p.imagenes) > refs["imagenes"] or len(p.videos) > refs["videos"]:
            continue
        ok, _ = obtener_proveedor(nombre).comprobar()
        if ok:
            candidatos.append((spec["precio_seg"][p.resolucion], nombre))
    if not candidatos:
        raise LookupError(
            f"Ningún modelo configurado para nivel={nivel}, {p.resolucion}, {p.duracion}s")
    return sorted(candidatos)[0][1]
