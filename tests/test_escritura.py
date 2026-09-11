"""El puente agentes → archivos de la serie: la biblia acaba en `registry.json`."""
from __future__ import annotations

import json

import factorias as f

from showrunner.agentes import escritura
from showrunner.dominio import registro as reg
from showrunner.dominio import shotlist as sl
from showrunner.valida import valida_prompt, valida_shotlist


def test_guardar_biblia_escribe_los_cinco_archivos(serie):
    escritos = escritura.guardar_biblia(serie, f.salida_showrunner())
    assert set(escritos) == {"biblia.json", "biblia.md", "style.md", "voces.md",
                             "temporada.json", "registry.json"}
    biblia = (serie / "biblia.md").read_text(encoding="utf-8")
    assert "@char_canon-rojo_Nadia_v1" in biblia and "{TÍTULO}" not in biblia
    temporada = json.loads((serie / "temporada.json").read_text(encoding="utf-8"))
    assert temporada["episodios"][0]["id"] == "s01_ep01"


def test_la_biblia_deja_los_assets_registrados_y_pendientes(serie):
    """R-01 es comprobable desde el minuto uno: el tag existe antes del casting."""
    escritura.guardar_biblia(serie, f.salida_showrunner())
    registro = reg.cargar(serie / "registry.json")
    asset = registro.resolver("@char_canon-rojo_Nadia_v1")
    assert asset.descriptor == f.DESCRIPTOR_NADIA
    assert asset.estado == "pendiente" and asset.referencias == []
    assert registro.existe("@loc_canon-rojo_Despacho_v1")


def test_guardar_biblia_no_pisa_un_asset_con_referencias(serie):
    escritura.guardar_biblia(serie, f.salida_showrunner())
    registro = reg.cargar(serie / "registry.json")
    asset = registro.resolver("@char_canon-rojo_Nadia_v1")
    asset.referencias.append(reg.Referencia(url="https://x/cara.png", tipo="cara"))
    asset.estado = "aprobado"
    reg.guardar(registro, serie / "registry.json")

    escritura.guardar_biblia(serie, f.salida_showrunner())
    vuelto = reg.cargar(serie / "registry.json").resolver("@char_canon-rojo_Nadia_v1")
    assert vuelto.estado == "aprobado" and len(vuelto.referencias) == 1


def test_el_style_md_generado_sirve_para_el_linter(serie):
    """Lo que escribe el showrunner tiene que valer como bloque inmutable del director."""
    escritura.guardar_biblia(serie, f.salida_showrunner())
    style_md = (serie / "style.md").read_text(encoding="utf-8")
    registro = reg.cargar(serie / "registry.json")
    informe = valida_prompt(f.prompt_valido(), style_md=style_md, registro=registro)
    assert informe.ok, informe.resumen()


def test_guardar_episodio_deja_un_shotlist_valido(serie):
    escritura.guardar_biblia(serie, f.salida_showrunner())
    escritos = escritura.guardar_episodio(serie, f.salida_guionista(), "s01_ep01")
    lista = sl.cargar(escritos["shotlist.json"])
    assert next(p.id for p in lista.planos) == "s01_ep01_sh001"
    assert "GANCHO" in escritos["guion.md"].read_text(encoding="utf-8")
    assert escritos["guion.json"].exists()
    informe = valida_shotlist(lista, registro=reg.cargar(serie / "registry.json"))
    assert informe.ok, informe.resumen()
