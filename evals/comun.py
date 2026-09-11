"""Arnés de evaluación: sin frameworks, un script por agente.

Dos números distintos y no intercambiables:

* **Rúbrica** — cuántos casos pasan las comprobaciones deterministas. Es barato y
  objetivo, pero sólo mide lo que una máquina sabe ver.
* **Acuerdo juez–humano** — cuánto coincide el veredicto automático con el tuyo.
  Hasta que este número sea alto, el juez automático no decide nada: informa.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

AQUI = Path(__file__).resolve().parent
CASOS = AQUI / "casos"


@dataclass
class Caso:
    id: str
    datos: dict[str, Any] = field(default_factory=dict)

    @property
    def etiqueta(self) -> str | None:
        """Etiqueta humana, si la hay. `None` = sin etiquetar todavía."""
        return self.datos.get("etiqueta")


def cargar_casos(nombre: str) -> list[Caso]:
    ruta = CASOS / nombre
    if not ruta.exists():
        return []
    casos = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("//"):
            continue
        datos = json.loads(linea)
        casos.append(Caso(id=datos["id"], datos=datos))
    return casos


def aplicar_mutacion(texto: str, mutacion: dict | None) -> str:
    """Las variantes del golden set se describen como mutaciones del caso base.

    Así cada caso dice en una línea qué regla rompe, en vez de repetir el prompt
    entero veinticuatro veces.
    """
    if not mutacion:
        return texto
    for quitar in mutacion.get("quitar", []):
        texto = texto.replace(quitar, "")
    for de, a in mutacion.get("sustituir", []):
        texto = texto.replace(de, a)
    if mutacion.get("anadir"):
        texto = texto + "\n" + mutacion["anadir"] + "\n"
    return texto


@dataclass
class Resultado:
    caso: str
    esperado: str | None
    obtenido: str
    ok: bool
    detalle: str = ""


@dataclass
class Marcador:
    agente: str
    resultados: list[Resultado] = field(default_factory=list)

    def anota(self, caso: str, esperado: str | None, obtenido: str, ok: bool,
              detalle: str = "") -> None:
        self.resultados.append(Resultado(caso, esperado, obtenido, ok, detalle))

    @property
    def etiquetados(self) -> list[Resultado]:
        return [r for r in self.resultados if r.esperado is not None]

    def acuerdo(self) -> dict[str, Any]:
        """Acuerdo con el etiquetado humano, con kappa de Cohen.

        La exactitud sola engaña cuando una clase domina: si el 90 % de las tomas
        son buenas, decir «buena» siempre da 0,90 y no sirve de nada. Kappa
        descuenta el acuerdo por azar.
        """
        pares = [(r.esperado, r.obtenido) for r in self.etiquetados]
        n = len(pares)
        if n == 0:
            return {"n": 0, "exactitud": None, "kappa": None,
                    "nota": "sin casos etiquetados: no se puede medir el acuerdo"}
        coincidencias = sum(1 for a, b in pares if a == b)
        po = coincidencias / n
        clases = {c for par in pares for c in par}
        pe = sum(
            (sum(1 for a, _ in pares if a == c) / n) * (sum(1 for _, b in pares if b == c) / n)
            for c in clases
        )
        kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
        return {"n": n, "coincidencias": coincidencias, "exactitud": round(po, 3),
                "kappa": round(kappa, 3)}

    def resumen(self) -> dict[str, Any]:
        total = len(self.resultados)
        pasan = sum(1 for r in self.resultados if r.ok)
        return {
            "agente": self.agente,
            "casos": total,
            "pasan": pasan,
            "tasa": round(pasan / total, 3) if total else None,
            "acuerdo_juez_humano": self.acuerdo(),
            "fallos": [{"caso": r.caso, "esperado": r.esperado, "obtenido": r.obtenido,
                        "detalle": r.detalle} for r in self.resultados if not r.ok],
        }

    def imprimir(self) -> dict[str, Any]:
        resumen = self.resumen()
        print(json.dumps(resumen, indent=2, ensure_ascii=False))
        acuerdo = resumen["acuerdo_juez_humano"]
        if acuerdo["n"] == 0:
            print("\n⚠️  Sin etiquetado humano: la rúbrica mide lo comprobable, no el criterio.\n"
                  "    Etiqueta los casos antes de dejar que el juez automático decida nada.")
        return resumen


def guardar(resumen: dict, destino: Path | None) -> None:
    if destino:
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(resumen, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
        print(f"\nInforme en {destino}")
