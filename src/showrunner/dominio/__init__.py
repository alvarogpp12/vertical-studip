"""Núcleo de datos: los contratos ejecutables del proyecto.

`identidad` (ids y slugs) · `registro` (registry.json) · `shotlist` (shotlist.json)
· `serie` (proyecto.json y aprobaciones) · `eventos` (log append-only y presupuesto).
"""
from __future__ import annotations

from . import eventos, identidad, memoria, referencias, registro, serie, shotlist
from .identidad import IdPlano, Tag, id_episodio, slugify, tags_en_texto
from .registro import Asset, Referencia, Registro, TagDesconocido
from .serie import Aprobacion, Proyecto
from .shotlist import Plano, Shotlist

__all__ = [
    "Aprobacion",
    "Asset",
    "IdPlano",
    "Plano",
    "Proyecto",
    "Referencia",
    "Registro",
    "Shotlist",
    "Tag",
    "TagDesconocido",
    "eventos",
    "id_episodio",
    "identidad",
    "registro",
    "serie",
    "shotlist",
    "slugify",
    "tags_en_texto",
]
