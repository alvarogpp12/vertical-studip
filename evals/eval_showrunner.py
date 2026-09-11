#!/usr/bin/env python3
"""Evaluación del agente showrunner: idea → biblia.

Dos modos:

* `existentes` (por defecto, gratis) — puntúa los `biblia.json` que ya hay en
  `proyectos/` contra la rúbrica de `evals/rubrica.py`.
* `ideas` — corre el agente sobre `casos/ideas.jsonl`. Cuesta dinero y necesita
  `ANTHROPIC_API_KEY`.

El acuerdo juez–humano sólo se calcula sobre casos con `etiqueta` puesta a mano en
`ideas.jsonl`. Mientras no la pongas, el informe lo dice en vez de fingir un número.

Uso:
    uv run python evals/eval_showrunner.py
    uv run python evals/eval_showrunner.py --modo ideas --limite 1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "src"))
sys.path.insert(0, str(AQUI))

from comun import Marcador, cargar_casos, guardar
from rubrica import CRITERIOS

from showrunner.agentes.contratos import SalidaShowrunner
from showrunner.config import ROOT
from showrunner.valida.biblia import valida_salida_showrunner


def puntua(marcador: Marcador, nombre: str, salida: SalidaShowrunner,
           etiqueta: str | None = None) -> None:
    informe = valida_salida_showrunner(salida)
    codigos = [i.codigo for i in informe.errores]
    obtenido = "buena" if informe.ok else codigos[0]
    marcador.anota(nombre, etiqueta, obtenido, informe.ok,
                   detalle=f"códigos={codigos} · avisos="
                           f"{[i.codigo for i in informe.avisos]}")


def evalua_existentes() -> Marcador:
    marcador = Marcador("showrunner")
    for ruta in sorted((ROOT / "proyectos").glob("*/biblia.json")):
        salida = SalidaShowrunner.model_validate(json.loads(ruta.read_text(encoding="utf-8")))
        puntua(marcador, ruta.parent.name, salida)
    return marcador


def evalua_ideas(limite: int, n_episodios: int) -> Marcador:
    from showrunner.agentes import showrunner

    marcador = Marcador("showrunner")
    for caso in cargar_casos("ideas.jsonl")[:limite]:
        sobre = showrunner.crear_biblia(caso.datos["idea"], caso.datos["titulo"],
                                        plataforma=caso.datos.get("plataforma", "tiktok"),
                                        n_episodios=n_episodios)
        if not sobre.ok:
            marcador.anota(caso.id, caso.etiqueta, sobre.rechazo.motivo_codigo, False,
                           sobre.rechazo.detalle)
            continue
        puntua(marcador, caso.id, sobre.resultado, caso.etiqueta)
    return marcador


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--modo", choices=["existentes", "ideas"], default="existentes")
    p.add_argument("--limite", type=int, default=3)
    p.add_argument("--episodios", type=int, default=6)
    p.add_argument("--informe", type=Path, default=None)
    args = p.parse_args()

    if args.modo == "ideas":
        print("⚠️  Este modo llama al modelo y cuesta dinero.\n")
        marcador = evalua_ideas(args.limite, args.episodios)
    else:
        marcador = evalua_existentes()

    if not marcador.resultados:
        print(json.dumps({"agente": "showrunner", "casos": 0,
                          "nota": "no hay ningún biblia.json en proyectos/. Crea una serie "
                                  "con `showrunner biblia` o usa --modo ideas."},
                         indent=2, ensure_ascii=False))
        return 1
    print("Criterios:", ", ".join(c.clave for c in CRITERIOS["showrunner"]))
    resumen = marcador.imprimir()
    guardar(resumen, args.informe)
    return 0 if resumen["tasa"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
