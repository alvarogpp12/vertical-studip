#!/usr/bin/env python3
"""Evaluación del agente director (y de su linter).

Dos modos:

* `linter` (por defecto, gratis, sin red) — pasa el golden set de 24 prompts por
  `valida_prompt` y mide si cada uno recibe la etiqueta que le corresponde. Es la
  rúbrica del director: R-01, R-02, R-03, R-07, R-08 y R-09.
* `agente` — hace que el director escriba prompts de verdad para los planos del
  shotlist y los puntúa con la misma rúbrica. Cuesta dinero y necesita clave.

Uso:
    uv run python evals/eval_director.py
    uv run python evals/eval_director.py --informe runs/eval_director.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "src"))
sys.path.insert(0, str(AQUI))

from comun import CASOS, Marcador, aplicar_mutacion, cargar_casos, guardar

from showrunner.dominio import registro as reg
from showrunner.valida import valida_prompt


def clasifica(codigos: list[str]) -> str:
    return codigos[0] if codigos else "valido"


def evalua_linter() -> Marcador:
    marcador = Marcador("director")
    base = (CASOS / "prompt_base.md").read_text(encoding="utf-8")
    style = (CASOS / "style.md").read_text(encoding="utf-8")
    registro = reg.cargar(CASOS / "registro.json")

    for caso in cargar_casos("prompts.jsonl"):
        prompt = aplicar_mutacion(base, caso.datos.get("mutacion"))
        informe = valida_prompt(prompt, style_md=style, registro=registro)
        codigos = [i.codigo for i in informe.errores]
        esperado = caso.etiqueta
        # Un prompt roto suele disparar varios códigos a la vez. Se da por acertado
        # si el esperado está entre ellos; si no, se anota el primero, que es el que
        # verá quien lea el informe.
        acierta = (esperado == "valido" and not codigos) or (esperado in codigos)
        marcador.anota(caso.id, esperado, esperado if acierta else clasifica(codigos),
                       acierta, detalle=caso.datos.get("nota", "") + f" · códigos={codigos}")
    return marcador


def evalua_agente(serie: str, episodio: str, limite: int) -> Marcador:
    from showrunner import proyecto
    from showrunner.agentes import director
    from showrunner.dominio import shotlist as sl
    from showrunner.dominio.identidad import IdPlano

    marcador = Marcador("director")
    ruta = proyecto.ruta(serie)
    registro = reg.cargar(ruta / "registry.json")
    estilo = (ruta / "style.md").read_text(encoding="utf-8")
    biblia = (ruta / "biblia.md").read_text(encoding="utf-8")
    carpeta = IdPlano.parse(f"{episodio}_sh001").carpeta_episodio
    lista = sl.cargar(ruta / "episodios" / carpeta / "shotlist.json")

    for plano in lista.en_orden[:limite]:
        sobre = director.escribir_prompt(plano, registro, biblia_md=biblia, estilo_md=estilo,
                                         serie=serie)
        if sobre.ok:
            marcador.anota(plano.id, "valido", "valido", True)
        else:
            marcador.anota(plano.id, "valido", sobre.rechazo.motivo_codigo, False,
                           sobre.rechazo.detalle)
    return marcador


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--modo", choices=["linter", "agente"], default="linter")
    p.add_argument("--serie", default="", help="Slug de la serie (modo agente)")
    p.add_argument("--episodio", default="s01_ep01")
    p.add_argument("--limite", type=int, default=5, help="Planos a evaluar (modo agente)")
    p.add_argument("--informe", type=Path, default=None)
    args = p.parse_args()

    if args.modo == "agente":
        if not args.serie:
            p.error("el modo agente necesita --serie")
        print("⚠️  Este modo llama al modelo y cuesta dinero.\n")
        marcador = evalua_agente(args.serie, args.episodio, args.limite)
    else:
        marcador = evalua_linter()

    resumen = marcador.imprimir()
    guardar(resumen, args.informe)
    return 0 if resumen["casos"] and resumen["tasa"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
