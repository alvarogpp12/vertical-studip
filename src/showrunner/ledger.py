"""Compatibilidad: el ledger vive ahora en `dominio.eventos` (SQLite).

`runs/ledger.jsonl` se sustituye por `runs/eventos.sqlite`. Este módulo mantiene la
API antigua para no romper llamadas existentes; lo nuevo debe usar
`dominio.eventos` directamente, que además registra fallos y cierra el TOCTOU del
presupuesto.
"""
from __future__ import annotations

from .config import ROOT
from .dominio.eventos import (  # noqa: F401  (re-exportado a propósito)
    PresupuestoExcedido,
    cerrar,
    comprobar_presupuesto,
    gasto_hoy,
    migrar_jsonl,
    reservar,
)

LEDGER_ANTIGUO = ROOT / "runs" / "ledger.jsonl"


def registrar(**campos) -> dict:
    """Alta directa de una generación ya cerrada (ruta antigua, sin reserva previa)."""
    from .dominio import eventos

    coste = float(campos.pop("coste_usd", 0) or 0)
    plano = campos.pop("plano", "") or ""
    veredicto = campos.pop("veredicto", None)
    solicitud = eventos.registrar(
        "generacion_solicitada", plano=plano, intento=1, coste_estimado=coste,
        **{k: campos.get(k) for k in ("modelo", "prompt", "imagenes", "duracion", "resolucion")},
    )
    eventos.cerrar(solicitud, ok=True, coste_real=coste,
                   **{k: campos.get(k) for k in ("salida", "task_id", "seed", "tecnico")})
    return {"solicitud": solicitud, "plano": plano, "coste_usd": coste, "veredicto": veredicto}
