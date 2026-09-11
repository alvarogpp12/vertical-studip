"""Registro de cada generación (prompt, refs, modelo, coste, veredicto) + control de gasto."""
from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

from .config import ROOT, presupuesto

LEDGER = ROOT / "runs" / "ledger.jsonl"


class PresupuestoExcedido(RuntimeError):
    pass


def gasto_hoy() -> float:
    if not LEDGER.exists():
        return 0.0
    hoy = date.today().isoformat()
    total = 0.0
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("fecha", "").startswith(hoy):
            total += float(row.get("coste_usd", 0))
    return total


def comprobar_presupuesto(coste_estimado: float) -> None:
    max_job, max_dia = presupuesto()
    if coste_estimado > max_job:
        raise PresupuestoExcedido(
            f"Coste estimado {coste_estimado:.2f} $ supera el límite por tarea ({max_job} $)."
        )
    if gasto_hoy() + coste_estimado > max_dia:
        raise PresupuestoExcedido(
            f"Se superaría el límite diario ({max_dia} $). Gastado hoy: {gasto_hoy():.2f} $."
        )


def registrar(**campos) -> dict:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    row = {"fecha": time.strftime("%Y-%m-%dT%H:%M:%S"), **campos}
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row
