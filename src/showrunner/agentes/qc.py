"""Agente 4 · QC: fotogramas + referencias → veredicto de continuidad.

Mucha entrada (imágenes) y poco razonamiento: `claude-sonnet-5` de base. Escala a
`claude-opus-5` cuando el veredicto llega con poca confianza — que es justo el caso
donde los modelos con visión fallan, los artefactos finos.

Lo técnico (9:16, fps, duración, ΔE, cortes) ya lo ha decidido `valida_toma` antes
de llegar aquí: este agente sólo juzga lo que una máquina no puede.
"""
from __future__ import annotations

import base64
from pathlib import Path

from ..dominio import registro as reg
from ..valida.resultado import Resultado
from .base import Agente, Contexto, bloque
from .cliente import ClienteLLM
from .contratos import SalidaQC, Sobre

#: Por debajo de esto, el veredicto se repite con el modelo grande.
CONFIANZA_MINIMA = 0.7
TIPO_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
             ".webp": "image/webp", ".gif": "image/gif"}


def agente(cliente: ClienteLLM | None = None, modelo: str = "claude-sonnet-5") -> Agente:
    kwargs = {"cliente": cliente} if cliente is not None else {}
    return Agente(nombre="qc", skill="qc-continuidad", modelo=modelo,
                  effort="medium", max_tokens=4000, **kwargs)


def _imagen(ruta: Path) -> dict:
    ruta = Path(ruta)
    media = TIPO_MIME.get(ruta.suffix.lower(), "image/png")
    datos = base64.standard_b64encode(ruta.read_bytes()).decode("ascii")
    return {"type": "image", "source": {"type": "base64", "media_type": media, "data": datos}}


def _peticion(fotogramas: list[Path], descriptores: str, tecnico: Resultado | None,
              duracion: float) -> list[dict]:
    bloques: list[dict] = []
    for indice, ruta in enumerate(fotogramas):
        bloques.append({"type": "text", "text": f"Fotograma {indice}:"})
        bloques.append(_imagen(ruta))
    incidencias = tecnico.resumen() if tecnico is not None else "sin incidencias técnicas"
    bloques.append({"type": "text", "text": f"""
Juzga esta toma de {duracion:g} s contra sus referencias.

Referencias activas:
{descriptores}

El validador técnico ya ha comprobado formato, fps, duración, deriva de color y cortes:
{incidencias}

Revisa UNA dimensión cada vez: identidad · vestuario · props y su estado · geografía y
eje · artefactos (manos, caras, morphing) · zona segura vertical · interpretación.
Los artefactos finos se detectan mal: si dudas, baja la confianza y marca
`requiere_humano`. Más vale una mirada humana que quemar crédito en un reintento.
""".strip()})
    return bloques


def revisar(fotogramas: list[Path], registro: reg.Registro, tags: list[str], *,
            duracion: float, tecnico: Resultado | None = None, serie: str = "",
            plano: str = "", intento: int = 1, cliente: ClienteLLM | None = None,
            confianza_minima: float = CONFIANZA_MINIMA) -> Sobre:
    """Veredicto de continuidad. Escala al modelo grande si la confianza es baja."""
    descriptores = "\n".join(
        f"- {t}: {registro.descriptor(t)}" for t in tags if registro.existe(t)
    ) or "- (ninguna)"
    peticion = _peticion(fotogramas, descriptores, tecnico, duracion)
    contexto = Contexto(serie=serie, plano=plano, intento=intento,
                        estable=[bloque("Referencias de la serie", descriptores)])

    sobre = agente(cliente).preguntar(peticion, SalidaQC, contexto)
    if not sobre.ok:
        return sobre
    veredicto: SalidaQC = sobre.resultado
    if veredicto.confianza >= confianza_minima:
        return sobre
    # Poca confianza: repetir con el modelo grande antes de decidir nada caro.
    return agente(cliente, modelo="claude-opus-5").preguntar(peticion, SalidaQC, contexto)
