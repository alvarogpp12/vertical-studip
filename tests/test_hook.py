"""El hook `PreToolUse`: el linter vale también trabajando a mano en Claude Code."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from showrunner import proyecto

RAIZ = Path(__file__).resolve().parents[1]
HOOK = RAIZ / "scripts" / "hook_lint_prompt.py"
PROMPT_MALO = "SCENE: @char_hook-test_Fantasma_v1 looks sad.\n"


@pytest.fixture
def serie_en_el_repo():
    """El hook resuelve rutas contra la raíz del repo, así que la serie va ahí."""
    destino = RAIZ / "proyectos" / "hook-test"
    assert not destino.exists(), "proyectos/hook-test ya existe; bórralo"
    try:
        yield proyecto.crear("hook test")
    finally:
        shutil.rmtree(destino, ignore_errors=True)


def _lanza(evento: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(evento), text=True,
                          capture_output=True, cwd=RAIZ)


def test_hook_ignora_lo_que_no_es_una_generacion():
    assert _lanza({"tool_name": "Bash", "tool_input": {"command": "ls -la"}}).returncode == 0


def test_hook_ignora_entradas_rotas():
    r = subprocess.run([sys.executable, str(HOOK)], input="no es json", text=True,
                       capture_output=True, cwd=RAIZ)
    assert r.returncode == 0


def test_hook_bloquea_un_prompt_invalido(serie_en_el_repo):
    """Un prompt sin STYLE PREFIX y con un tag inventado no debe llegar a la red."""
    prompt = serie_en_el_repo / "prompt_malo.md"
    prompt.write_text(PROMPT_MALO, encoding="utf-8")
    r = _lanza({"tool_name": "Bash",
                "tool_input": {"command": f"uv run showrunner generar {prompt} "
                                          "--salida x.mp4 --serie hook-test"}})
    assert r.returncode == 2
    assert "TAG_NO_REGISTRADO" in r.stderr and "VOCABULARIO_EMOCION" in r.stderr


def test_hook_bloquea_una_escritura_en_prompts(serie_en_el_repo):
    destino = serie_en_el_repo / "episodios" / "ep01" / "prompts" / "sh001.md"
    r = _lanza({"tool_name": "Write",
                "tool_input": {"file_path": str(destino), "content": PROMPT_MALO}})
    assert r.returncode == 2 and "TAG_NO_REGISTRADO" in r.stderr
