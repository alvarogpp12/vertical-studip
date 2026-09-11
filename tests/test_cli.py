"""La CLI: el linter corta antes de la red y el estado se pliega desde los eventos."""
from __future__ import annotations

import pytest
from typer.testing import CliRunner

from showrunner import cli
from showrunner.dominio import eventos as ev

runner = CliRunner()

PROMPT_MALO = "SCENE: @char_canon-rojo_Fantasma_v1 looks sad and angry.\n"


def test_modelos_lista_video_e_imagen():
    r = runner.invoke(cli.app, ["modelos"])
    assert r.exit_code == 0 and "seedance-2.5@byteplus" in r.stdout and "mock-imagen" in r.stdout


def test_generar_no_toca_la_red_si_el_lint_falla(serie, monkeypatch):
    """Verificación de la fase B: se rechaza antes de cualquier llamada."""
    monkeypatch.setattr(cli.proyecto, "ruta", lambda _: serie)
    monkeypatch.setattr(cli, "obtener_proveedor",
                        lambda _: pytest.fail("no debería llegar al proveedor"))
    prompt = serie / "prompt.md"
    prompt.write_text(PROMPT_MALO, encoding="utf-8")
    r = runner.invoke(cli.app, ["generar", str(prompt), "--salida", str(serie / "x.mp4"),
                                "--serie", "canon-rojo", "--plano", "s01_ep01_sh001",
                                "--modelo", "mock"])
    assert r.exit_code == 2
    assert "TAG_NO_REGISTRADO" in r.stdout
    assert ev.leer() == []          # no se ha reservado presupuesto


def test_generar_con_mock_registra_el_evento(serie, monkeypatch, tmp_path):
    monkeypatch.setattr(cli.proyecto, "ruta", lambda _: serie)
    salida = tmp_path / "toma.mp4"
    prompt = serie / "prompt.md"
    prompt.write_text("No music — diegetic sound only.\n", encoding="utf-8")
    r = runner.invoke(cli.app, ["generar", str(prompt), "--salida", str(salida),
                                "--plano", "s01_ep01_sh001", "--modelo", "mock",
                                "--duracion", "2"])
    assert r.exit_code == 0, r.stdout
    assert salida.exists()
    estado = ev.plegar()["s01_ep01_sh001"]
    assert estado.estado == "qc_pendiente" and estado.intentos == 1


def test_estado_muestra_las_metricas():
    s = ev.reservar(0.1, serie="canon-rojo", plano="s01_ep01_sh001", intento=1)
    ev.cerrar(s, ok=True, coste_real=0.1, salida="a.mp4")
    r = runner.invoke(cli.app, ["estado", "--serie", "canon-rojo"])
    assert r.exit_code == 0
    assert '"planos": 1' in r.stdout and '"intentos_totales": 1' in r.stdout
