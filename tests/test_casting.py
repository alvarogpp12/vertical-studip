"""Preproducción: plantillas rellenadas, registro escrito y cadena imagen→vídeo."""
from __future__ import annotations

import json

import pytest

from showrunner import casting, proyecto
from showrunner.dominio import eventos as ev
from showrunner.dominio import registro as reg
from showrunner.dominio import serie as ser
from showrunner.dominio import shotlist as sl


def test_crear_serie_rellena_las_plantillas(serie):
    """Antes se copiaban tal cual: `{TÍTULO}` y `registry.serie` quedaban sin rellenar."""
    biblia = (serie / "biblia.md").read_text(encoding="utf-8")
    assert "{TÍTULO}" not in biblia and "Cañón Rojo" in biblia
    registro = reg.cargar(serie / "registry.json")
    assert registro.serie == "canon-rojo"
    proy = ser.cargar(serie / "proyecto.json")
    assert proy.titulo == "Cañón Rojo" and proy.plataforma == "tiktok"
    assert not proy.aprobado("biblia")
    lista = sl.cargar(serie / "episodios" / "ep01" / "shotlist.json")
    assert lista.episodio == "s01_ep01" and lista.planos[0].es_master


def test_crear_serie_dos_veces_falla(serie):
    with pytest.raises(FileExistsError):
        proyecto.crear("Cañón Rojo")


def test_casting_escribe_el_registro(serie, monkeypatch):
    """Es el primer código del proyecto que toca registry.json."""
    monkeypatch.setenv("BUDGET_MAX_PER_DAY", "10")
    asset = casting.crear_personaje(serie, "Nadia", "a woman in her 40s with a scarred brow,",
                                    modelo="mock-imagen", subir=False)
    assert asset.id == "@char_canon-rojo_Nadia_v1"
    tipos = [r.tipo for r in asset.referencias]
    assert tipos == ["cara", "hoja"]
    assert asset.cara_congelada.congelada          # R-05

    guardado = json.loads((serie / "registry.json").read_text(encoding="utf-8"))
    assert asset.id in guardado["personajes"]
    assert reg.cargar(serie / "registry.json").existe(asset.id)


def test_la_cara_original_no_se_regenera(serie, monkeypatch):
    """R-05: sobre un personaje ya registrado se añade hoja, nunca una cara nueva."""
    monkeypatch.setenv("BUDGET_MAX_PER_DAY", "10")
    descriptor = "a woman in her 40s with a scarred brow,"
    primera = casting.crear_personaje(serie, "Nadia", descriptor, modelo="mock-imagen", subir=False)
    url_cara = primera.cara_congelada.url
    segunda = casting.crear_personaje(serie, "Nadia", descriptor, modelo="mock-imagen", subir=False)
    assert segunda.cara_congelada.url == url_cara
    assert [r.tipo for r in segunda.referencias] == ["cara", "hoja", "hoja"]


def test_cambiar_el_descriptor_exige_version_nueva(serie, monkeypatch):
    monkeypatch.setenv("BUDGET_MAX_PER_DAY", "10")
    casting.crear_personaje(serie, "Nadia", "descriptor uno,", modelo="mock-imagen", subir=False)
    with pytest.raises(casting.CaraCongelada):
        casting.crear_personaje(serie, "Nadia", "descriptor dos,", modelo="mock-imagen",
                                subir=False)


def test_casting_registra_el_gasto(serie, monkeypatch):
    monkeypatch.setenv("BUDGET_MAX_PER_DAY", "10")
    casting.crear_personaje(serie, "Nadia", "descriptor,", modelo="mock-imagen", subir=False)
    tipos = [e["tipo"] for e in ev.leer()]
    assert tipos.count("generacion_solicitada") == 2 and tipos.count("generacion_ok") == 2


def test_prueba_en_movimiento_cierra_la_cadena(serie, monkeypatch):
    """R-12 y verificación de la fase C: imagen → registro → vídeo, sin gastar."""
    monkeypatch.setenv("BUDGET_MAX_PER_DAY", "10")
    tag = casting.crear_personaje(serie, "Nadia", "descriptor,", modelo="mock-imagen",
                                  subir=False).id
    informe, ruta = casting.prueba_en_movimiento(serie, tag, duracion=3, modelo="mock")
    assert ruta.exists() and informe.ok, informe.resumen()
    estado = ev.plegar()[f"{tag}:movimiento"]
    assert estado.estado == "aceptado"


def test_aprobar_casting_deja_rastro(serie, monkeypatch):
    monkeypatch.setenv("BUDGET_MAX_PER_DAY", "10")
    tag = casting.crear_personaje(serie, "Nadia", "descriptor,", modelo="mock-imagen",
                                  subir=False).id
    asset = casting.aprobar(serie, tag, por="alvaro")
    assert asset.estado == "aprobado"
    assert reg.cargar(serie / "registry.json").resolver(tag).estado == "aprobado"
    aprobaciones = [e for e in ev.leer() if e["tipo"] == "aprobacion_humana"]
    assert aprobaciones[0]["payload"]["por"] == "alvaro"
