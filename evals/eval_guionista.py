#!/usr/bin/env python3
"""Evaluación del agente guionista: biblia + episodio → guion + shotlist.

Mide lo comprobable: duración 61–90 s, gancho, cliffhanger, máster de geografía,
que el diálogo quepa en la duración (R-09) y que la cámara sea legal en vertical.

* `existentes` (por defecto, gratis) — puntúa los `guion.json` que ya hay.
* `generar` — escribe episodios de verdad para una serie. Cuesta dinero.

Uso:
    uv run python evals/eval_guionista.py
    uv run python evals/eval_guionista.py --modo generar --serie canon-rojo --episodios 2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "src"))
sys.path.insert(0, str(AQUI))

from comun import Marcador, guardar
from rubrica import CRITERIOS

from showrunner.agentes.contratos import SalidaGuionista
from showrunner.agentes.guionista import a_shotlist
from showrunner.config import ROOT
from showrunner.dominio import registro as reg
from showrunner.dominio import serie as ser
from showrunner.valida import valida_shotlist
from showrunner.valida.biblia import valida_salida_guionista


def puntua(marcador: Marcador, nombre: str, salida: SalidaGuionista, id_episodio: str,
           proyecto: ser.Proyecto, registro: reg.Registro) -> None:
    informe = valida_salida_guionista(salida, duracion_min=proyecto.duracion_min,
                                      duracion_max=proyecto.duracion_objetivo_max)
    # El shotlist convertido pasa además por el validador de planos: R-01 y R-09.
    informe.unir(valida_shotlist(a_shotlist(salida, id_episodio), registro=registro,
                                 duracion_min=proyecto.duracion_min,
                                 duracion_max=proyecto.duracion_objetivo_max))
    codigos = [i.codigo for i in informe.errores]
    marcador.anota(nombre, None, "bueno" if informe.ok else codigos[0], informe.ok,
                   detalle=f"códigos={codigos}")


def _proyecto_y_registro(carpeta: Path) -> tuple[ser.Proyecto, reg.Registro]:
    return ser.cargar(carpeta / "proyecto.json"), reg.cargar(carpeta / "registry.json")


def evalua_existentes() -> Marcador:
    marcador = Marcador("guionista")
    for ruta in sorted((ROOT / "proyectos").glob("*/episodios/*/guion.json")):
        carpeta_serie = ruta.parents[2]
        proyecto, registro = _proyecto_y_registro(carpeta_serie)
        numero = int(ruta.parent.name.removeprefix("ep"))
        id_episodio = f"s{proyecto.temporada:02d}_ep{numero:02d}"
        salida = SalidaGuionista.model_validate(json.loads(ruta.read_text(encoding="utf-8")))
        puntua(marcador, f"{carpeta_serie.name}/{id_episodio}", salida, id_episodio,
               proyecto, registro)
    return marcador


def evalua_generando(slug: str, cuantos: int) -> Marcador:
    from showrunner import proyecto as proy
    from showrunner.agentes import guionista

    marcador = Marcador("guionista")
    carpeta = proy.ruta(slug)
    proyecto, registro = _proyecto_y_registro(carpeta)
    biblia = (carpeta / "biblia.md").read_text(encoding="utf-8")
    estilo = (carpeta / "style.md").read_text(encoding="utf-8")
    for numero in range(1, cuantos + 1):
        id_episodio = f"s{proyecto.temporada:02d}_ep{numero:02d}"
        sobre = guionista.escribir_episodio(biblia, estilo, registro, id_episodio=id_episodio,
                                            proyecto=proyecto)
        if not sobre.ok:
            marcador.anota(id_episodio, None, sobre.rechazo.motivo_codigo, False,
                           sobre.rechazo.detalle)
            continue
        puntua(marcador, id_episodio, sobre.resultado, id_episodio, proyecto, registro)
    return marcador


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--modo", choices=["existentes", "generar"], default="existentes")
    p.add_argument("--serie", default="")
    p.add_argument("--episodios", type=int, default=1)
    p.add_argument("--informe", type=Path, default=None)
    args = p.parse_args()

    if args.modo == "generar":
        if not args.serie:
            p.error("el modo generar necesita --serie")
        print("⚠️  Este modo llama al modelo y cuesta dinero.\n")
        marcador = evalua_generando(args.serie, args.episodios)
    else:
        marcador = evalua_existentes()

    if not marcador.resultados:
        print(json.dumps({"agente": "guionista", "casos": 0,
                          "nota": "no hay ningún guion.json en proyectos/."},
                         indent=2, ensure_ascii=False))
        return 1
    print("Criterios:", ", ".join(c.clave for c in CRITERIOS["guionista"]))
    resumen = marcador.imprimir()
    guardar(resumen, args.informe)
    return 0 if resumen["tasa"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
