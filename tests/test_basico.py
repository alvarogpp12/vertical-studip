import json
from pathlib import Path

import pytest

from showrunner import ledger
from showrunner.providers import PeticionVideo, estimar_coste, obtener_proveedor
from showrunner.providers.byteplus import BytePlusProveedor
from showrunner.qc import escenas, fotogramas, paleta, sonda


def test_catalogo_y_coste():
    p = PeticionVideo(prompt="x", duracion=10, resolucion="720p")
    assert estimar_coste("seedance-2.5@byteplus", p) == pytest.approx(2.31)
    assert estimar_coste("kling-3.0-standard@fal", p) == pytest.approx(1.26)


def test_presupuesto_por_tarea(monkeypatch):
    monkeypatch.setenv("BUDGET_MAX_PER_JOB", "1")
    with pytest.raises(ledger.PresupuestoExcedido):
        ledger.comprobar_presupuesto(2.0)


def test_cuerpo_byteplus(monkeypatch):
    monkeypatch.setenv("ARK_MODEL_SEEDANCE_25", "modelo-test")
    prov = obtener_proveedor("seedance-2.5@byteplus")
    assert isinstance(prov, BytePlusProveedor)
    body = prov._body(PeticionVideo(prompt="hola", imagenes=["https://x/a.png"], duracion=5))
    assert body["model"] == "modelo-test" and body["ratio"] == "9:16"
    assert body["content"][1]["role"] == "reference_image"


def test_mock_genera_vertical_y_qc(tmp_path: Path):
    salida = tmp_path / "clip.mp4"
    res = obtener_proveedor("mock").generar(PeticionVideo(prompt="x", duracion=2), salida)
    info = sonda.sondear(res.ruta_local)
    assert info["vertical_9_16"] and info["audio"] and info["duracion"] == pytest.approx(2, abs=0.2)
    frames = fotogramas.extraer(salida, tmp_path / "qc", cada_seg=1)
    assert len(frames) >= 2
    assert paleta.paleta(frames[0])[0][0].startswith("#")
    assert paleta.delta_e_medio(frames[0], frames[0]) == 0
    assert isinstance(escenas.cortes(salida), list)


def test_extraer_no_falla_con_duracion_multiplo_de_cada_seg(tmp_path: Path):
    """La rejilla de instantes no debe pedir un fotograma en el segundo exacto del final."""
    salida = tmp_path / "clip.mp4"
    obtener_proveedor("mock").generar(PeticionVideo(prompt="x", duracion=4), salida)
    frames = fotogramas.extraer(salida, tmp_path / "qc")  # cada_seg=2.0 por defecto, 4 % 2 == 0
    assert len(frames) >= 3


def test_extraer_con_audio_mas_largo_que_el_video(tmp_path: Path):
    """Seedance devuelve clips cuyo audio dura más que el vídeo: el contenedor miente.

    ffmpeg con "-ss T" antes de "-i" descarta los fotogramas con PTS < T, así que
    ningún instante puede pasar del PTS del último fotograma de vídeo.
    """
    import subprocess

    salida = tmp_path / "clip.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "lavfi", "-i", "testsrc=duration=5:size=96x160:rate=24",
         "-f", "lavfi", "-i", "sine=duration=5.5",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(salida)],
        check=True)
    info = sonda.sondear(salida)
    assert info["duracion"] > info["duracion_video"], "el contenedor debe durar más que el vídeo"
    frames = fotogramas.extraer(salida, tmp_path / "qc")
    assert len(frames) >= 3
