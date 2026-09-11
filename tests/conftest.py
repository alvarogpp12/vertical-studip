"""Aislamiento: ningún test escribe en `runs/` ni en `proyectos/` del repo."""
from __future__ import annotations

import pytest

from showrunner import proyecto
from showrunner.dominio import eventos as ev


@pytest.fixture(autouse=True)
def bd_aislada(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOWRUNNER_EVENTOS", str(tmp_path / "eventos.sqlite"))
    return ev.ruta_bd()


@pytest.fixture
def raiz_aislada(tmp_path, monkeypatch):
    """`proyectos/` en un directorio temporal, con las plantillas reales."""
    (tmp_path / "proyectos").mkdir()
    monkeypatch.setattr(proyecto, "ROOT", tmp_path)
    return tmp_path


@pytest.fixture
def serie(raiz_aislada):
    return proyecto.crear("Cañón Rojo", idea="Una jueza descubre que su hija miente.")
