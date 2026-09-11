"""Contratos del núcleo de datos: ids, registro, shotlist y proyecto."""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from showrunner.dominio import registro as reg
from showrunner.dominio import serie as ser
from showrunner.dominio import shotlist as sl
from showrunner.dominio.identidad import IdInvalido, IdPlano, Tag, slugify, tags_en_texto


def test_slugify_normaliza_acentos():
    """«Cañón Rojo» daba `ca-n-rojo` sin normalizar Unicode."""
    assert slugify("Cañón Rojo") == "canon-rojo"
    assert slugify("Ángel Caído") == "angel-caido"
    assert slugify("¡¿!") == "serie"


def test_id_de_plano_unico():
    pid = IdPlano.parse("s01_ep01_sh003")
    assert (pid.temporada, pid.episodio, pid.plano) == (1, 1, 3)
    assert str(pid) == "s01_ep01_sh003"
    assert pid.id_episodio == "s01_ep01" and pid.carpeta_episodio == "ep01"
    assert str(pid.siguiente()) == "s01_ep01_sh004"


def test_convencion_corta_rechazada():
    """`ep01_sh001` convivía con `s01_ep01_sh003` y hacía imposible cruzar datos."""
    with pytest.raises(IdInvalido):
        IdPlano.parse("ep01_sh001")


def test_tag_exige_version():
    tag = Tag.parse("@char_canon-rojo_Nadia_v1")
    assert (tag.tipo, tag.version, tag.seccion) == ("char", 1, "personajes")
    assert str(tag.con_version(2)) == "@char_canon-rojo_Nadia_v2"
    with pytest.raises(IdInvalido):
        Tag.parse("@char_canon-rojo_Nadia")


def test_tags_en_texto():
    assert tags_en_texto("usa @char_x_A_v1 y @loc_x_B_v1 y otra vez @char_x_A_v1") == [
        "@char_x_A_v1", "@loc_x_B_v1"
    ]


def _registro_de_prueba() -> reg.Registro:
    r = reg.Registro(serie="canon-rojo")
    r.anadir(reg.Asset(
        id="@char_canon-rojo_Nadia_v1", descriptor="Woman, 40s, scar on left brow.",
        estado="aprobado",
        referencias=[reg.Referencia(url="https://x/cara.png", tipo="cara"),
                     reg.Referencia(url="https://x/hoja.png", tipo="hoja")]))
    return r


def test_registro_resuelve_y_rechaza():
    r = _registro_de_prueba()
    assert r.descriptor("@char_canon-rojo_Nadia_v1").startswith("Woman")
    assert r.urls("@char_canon-rojo_Nadia_v1") == ["https://x/cara.png", "https://x/hoja.png"]
    with pytest.raises(reg.TagDesconocido):
        r.resolver("@char_canon-rojo_Otra_v1")
    assert r.existe("@char_canon-rojo_Nadia_v1") and not r.existe("no-es-un-tag")


def test_cara_nace_congelada():
    """R-05: el primer plano original de la cara no se regenera."""
    asset = _registro_de_prueba().resolver("@char_canon-rojo_Nadia_v1")
    assert asset.cara_congelada is not None and asset.cara_congelada.congelada


def test_registro_rechaza_clave_incoherente():
    with pytest.raises(ValidationError):
        reg.Registro.model_validate({
            "personajes": {"@char_x_A_v1": {"id": "@char_x_B_v1", "version": 1}}
        })


def test_registro_rechaza_version_incoherente():
    """R-01: un estado nuevo es un asset nuevo, no un campo editado."""
    with pytest.raises(ValidationError):
        reg.Asset(id="@char_x_A_v1", version=2)


def test_registro_va_y_vuelve_de_json(tmp_path):
    ruta = reg.guardar(_registro_de_prueba(), tmp_path / "registry.json")
    assert reg.cargar(ruta).model_dump() == _registro_de_prueba().model_dump()
    assert json.loads(ruta.read_text())["serie"] == "canon-rojo"


def test_plano_calcula_el_hueco_del_dialogo():
    """R-09: ~4 palabras/s + 1 s de cola limpia."""
    p = sl.Plano(id="s01_ep01_sh001", duracion=5, dialogo="No pienso firmar ese papel hoy")
    assert p.palabras_dialogo == 6
    assert p.duracion_minima == pytest.approx(2.5)
    assert p.cabe_el_dialogo
    assert not sl.Plano(id="s01_ep01_sh001", duracion=2, dialogo=p.dialogo).cabe_el_dialogo


def test_shotlist_rechaza_planos_de_otro_episodio():
    with pytest.raises(ValidationError):
        sl.Shotlist(episodio="s01_ep01", planos=[sl.Plano(id="s01_ep02_sh001")])


def test_shotlist_rechaza_ids_repetidos():
    with pytest.raises(ValidationError):
        sl.Shotlist(episodio="s01_ep01",
                    planos=[sl.Plano(id="s01_ep01_sh001"), sl.Plano(id="s01_ep01_sh001")])


def test_proyecto_guarda_las_aprobaciones_con_firma():
    """Antes la aprobación era «Aprobada por: —» en texto libre dentro de biblia.md."""
    p = ser.nuevo("Cañón Rojo", plataforma="tiktok")
    assert not p.aprobado("biblia")
    ap = p.aprobar("biblia", por="alvaro", version="1.0")
    assert p.aprobado("biblia") and ap.fecha and p.aprobacion("biblia").por == "alvaro"


def test_minimo_de_tiktok():
    """Creator Rewards exige más de 60 s."""
    assert ser.nuevo("X", plataforma="tiktok").duracion_min == 61.0
    p = ser.Proyecto(slug="x", titulo="X", plataforma="meta", duracion_objetivo_min=45)
    assert p.duracion_min == 45.0
    p.plataformas_secundarias = ["tiktok"]
    assert p.duracion_min == 61.0
