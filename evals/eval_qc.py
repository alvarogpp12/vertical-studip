#!/usr/bin/env python3
"""Evaluación del agente QC: ¿coincide su veredicto con el tuyo?

Esta es la única evaluación del proyecto donde el número que importa **no** es la
rúbrica: es el **acuerdo juez–humano**. Hasta que suba del umbral de
`rubrica.UMBRALES["acuerdo_minimo_juez"]`, el QC automático informa pero no decide:
rechazar una toma buena cuesta un reintento, y aceptar una mala cuesta el episodio.

El golden set (`casos/veredictos.jsonl`) lo rellenas tú a medida que revisas tomas:

    {"id": "v01", "fotogramas": ["proyectos/x/.../f0.png"], "tags": ["@char_x_A_v1"],
     "serie": "x", "duracion": 5, "etiqueta": "rechazada"}

Uso:
    uv run python evals/eval_qc.py --serie canon-rojo
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
from rubrica import UMBRALES

from showrunner.config import ROOT
from showrunner.dominio import registro as reg


def evalua(limite: int) -> Marcador:
    from showrunner.agentes import qc

    marcador = Marcador("qc")
    registros: dict[str, reg.Registro] = {}
    for caso in cargar_casos("veredictos.jsonl")[:limite]:
        slug = caso.datos.get("serie", "")
        if slug not in registros:
            registros[slug] = reg.cargar(ROOT / "proyectos" / slug / "registry.json")
        fotogramas = [ROOT / f for f in caso.datos["fotogramas"]]
        faltan = [f for f in fotogramas if not f.exists()]
        if faltan:
            marcador.anota(caso.id, caso.etiqueta, "SIN_FOTOGRAMAS", False,
                           f"no existen: {[str(f) for f in faltan]}")
            continue
        sobre = qc.revisar(fotogramas, registros[slug], caso.datos.get("tags", []),
                           duracion=float(caso.datos.get("duracion", 5)),
                           serie=slug, plano=caso.datos.get("plano", ""))
        if not sobre.ok:
            marcador.anota(caso.id, caso.etiqueta, sobre.rechazo.motivo_codigo, False,
                           sobre.rechazo.detalle)
            continue
        veredicto = sobre.resultado
        marcador.anota(caso.id, caso.etiqueta, veredicto.veredicto,
                       veredicto.veredicto == caso.etiqueta,
                       detalle=f"{veredicto.motivo_codigo} · confianza={veredicto.confianza} "
                               f"· requiere_humano={veredicto.requiere_humano}")
    return marcador


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--limite", type=int, default=30)
    p.add_argument("--informe", type=Path, default=None)
    args = p.parse_args()

    casos = cargar_casos("veredictos.jsonl")
    if not casos:
        print(json.dumps({
            "agente": "qc", "casos": 0,
            "acuerdo_juez_humano": {"n": 0, "exactitud": None, "kappa": None},
            "nota": "casos/veredictos.jsonl está vacío. Sin veredictos humanos no hay "
                    "acuerdo que medir, y sin acuerdo medido el QC automático no debe "
                    "decidir nada.",
        }, indent=2, ensure_ascii=False))
        return 1

    print("⚠️  Esta evaluación llama al modelo y cuesta dinero.\n")
    resumen = evalua(args.limite).imprimir()
    guardar(resumen, args.informe)
    acuerdo = resumen["acuerdo_juez_humano"]
    umbral = UMBRALES["acuerdo_minimo_juez"]
    if acuerdo["n"] and acuerdo["exactitud"] is not None:
        veredicto = "✅" if acuerdo["exactitud"] >= umbral else "❌"
        print(f"\n{veredicto} Acuerdo {acuerdo['exactitud']:.0%} (umbral {umbral:.0%}), "
              f"kappa {acuerdo['kappa']}")
        return 0 if acuerdo["exactitud"] >= umbral else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
