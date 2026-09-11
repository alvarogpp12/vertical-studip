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


def ficha(registro: reg.Registro, tag: str) -> str:
    """Todo lo que hace falta para juzgar continuidad de ese asset.

    El descriptor solo no basta: las **anclas de identidad** (cicatriz, anillo) son
    lo que de verdad se comprueba, y el mapa es lo que dice si el eje está roto.
    """
    asset = registro.resolver(tag)
    lineas = [f"### {tag}", asset.descriptor]
    if asset.notas:
        lineas.append(asset.notas)          # las anclas se guardan aquí al registrar
    if asset.voz_lock:
        lineas.append(f"VOZ: {asset.voz_lock}")
    if asset.mapa:
        lineas.append(f"MAPA ESPACIAL: {asset.mapa}")
    congelada = asset.cara_congelada
    if congelada:
        lineas.append(f"Cara de referencia (congelada, R-05): {congelada.url}")
    return "\n".join(lineas)


def fichas(registro: reg.Registro, tags: list[str]) -> str:
    presentes = [t for t in tags if registro.existe(t)]
    return "\n\n".join(ficha(registro, t) for t in presentes) or "(ninguna)"


def _imagen(ruta: Path) -> dict:
    ruta = Path(ruta)
    media = TIPO_MIME.get(ruta.suffix.lower(), "image/png")
    datos = base64.standard_b64encode(ruta.read_bytes()).decode("ascii")
    return {"type": "image", "source": {"type": "base64", "media_type": media, "data": datos}}


def _peticion(fotogramas: list[Path], tecnico: Resultado | None,
              duracion: float) -> list[dict]:
    bloques: list[dict] = []
    for indice, ruta in enumerate(fotogramas):
        bloques.append({"type": "text", "text": f"Fotograma {indice}:"})
        bloques.append(_imagen(ruta))
    incidencias = tecnico.resumen() if tecnico is not None else "sin incidencias técnicas"
    bloques.append({"type": "text", "text": f"""
Juzga esta toma de {duracion:g} s contra las fichas de referencia que tienes arriba.

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
    peticion = _peticion(fotogramas, tecnico, duracion)
    contexto = Contexto(
        serie=serie, plano=plano, intento=intento,
        estable=[bloque("Fichas de referencia de los assets de esta toma",
                        fichas(registro, tags))])

    sobre = agente(cliente).preguntar(peticion, SalidaQC, contexto)
    if not sobre.ok:
        return sobre
    veredicto: SalidaQC = sobre.resultado
    if veredicto.confianza >= confianza_minima:
        return sobre
    # Poca confianza: repetir con el modelo grande antes de decidir nada caro.
    return agente(cliente, modelo="claude-opus-5").preguntar(peticion, SalidaQC, contexto)
