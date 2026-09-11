#!/usr/bin/env python3
"""Hook `PreToolUse`: no dejar salir un prompt inválido, tampoco a mano.

`00_investigacion_sistema.md` pide un linter antes de cada llamada por el fallo
conocido del LLM: «se cree director» y añade detalles o cambia el encuadre. El
comando `showrunner generar` ya valida; este hook cubre el otro camino, el de
trabajar interactivamente en Claude Code.

Bloquea (código de salida 2) si:
  * un `showrunner generar … --serie <slug>` lleva un prompt con errores de lint;
  * se escribe un archivo dentro de `proyectos/<serie>/…/prompts/` que no pasa el lint.

Ante la duda deja pasar: un hook que se rompe no puede parar el trabajo.
"""
from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))


def _valida(texto: str, serie: str) -> tuple[bool, str]:
    from showrunner import proyecto
    from showrunner.dominio import registro as reg
    from showrunner.valida import valida_prompt

    base = proyecto.ruta(serie)
    style = base / "style.md"
    informe = valida_prompt(
        texto,
        style_md=style.read_text(encoding="utf-8") if style.exists() else "",
        registro=reg.cargar(base / "registry.json"),
    )
    return informe.ok, informe.resumen()


def _de_bash(comando: str) -> tuple[Path, str] | None:
    if "showrunner" not in comando or " generar" not in comando:
        return None
    try:
        partes = shlex.split(comando)
    except ValueError:
        return None
    serie = ""
    for i, parte in enumerate(partes):
        if parte in ("--serie", "--serie=") and i + 1 < len(partes):
            serie = partes[i + 1]
        elif parte.startswith("--serie="):
            serie = parte.split("=", 1)[1]
    if not serie:
        return None
    i = partes.index("generar")
    for parte in partes[i + 1:]:
        if not parte.startswith("-") and re.search(r"\.(md|txt)$", parte):
            return Path(parte), serie
    return None


def _de_escritura(entrada: dict) -> tuple[str, str] | None:
    ruta = entrada.get("file_path") or entrada.get("path") or ""
    if "/prompts/" not in ruta.replace("\\", "/"):
        return None
    partes = Path(ruta).parts
    if "proyectos" not in partes:
        return None
    serie = partes[partes.index("proyectos") + 1]
    contenido = entrada.get("content") or entrada.get("new_string") or ""
    return (contenido, serie) if contenido else None


def main() -> int:
    try:
        evento = json.load(sys.stdin)
    except Exception:
        return 0
    herramienta = evento.get("tool_name", "")
    entrada = evento.get("tool_input", {}) or {}
    try:
        if herramienta == "Bash":
            objetivo = _de_bash(entrada.get("command", ""))
            if not objetivo:
                return 0
            archivo, serie = objetivo
            archivo = archivo if archivo.is_absolute() else RAIZ / archivo
            if not archivo.exists():
                return 0
            ok, resumen = _valida(archivo.read_text(encoding="utf-8"), serie)
            fuente = str(archivo)
        elif herramienta in ("Write", "Edit"):
            objetivo = _de_escritura(entrada)
            if not objetivo:
                return 0
            contenido, serie = objetivo
            ok, resumen = _valida(contenido, serie)
            fuente = entrada.get("file_path", "")
        else:
            return 0
    except Exception:
        return 0  # el linter nunca bloquea por un fallo suyo

    if ok:
        return 0
    print(f"Linter de prompts · {fuente}\n{resumen}\n"
          "Corrige el prompt antes de gastar (reglas R-01…R-09).", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
