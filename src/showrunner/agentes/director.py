"""Agente 3 · director: plano + registro + estilo → prompt de generación.

`claude-sonnet-5` con effort `medium`: es el fan-out (50–200 planos por episodio) y
es donde paga la caché de prompt —biblia, estilo y registro son el mismo bloque en
cada llamada— y donde tiene sentido la Batch API (−50 %) cuando se escriben todos
los prompts de un episodio de una vez.

El prompt que devuelve pasa por `valida_prompt` antes de salir. Ese linter es el
antídoto del fallo conocido: el LLM «se cree director» y añade detalles o cambia el
encuadre.
"""
from __future__ import annotations

from ..dominio import registro as reg
from ..dominio.shotlist import Plano
from ..valida import valida_prompt
from ..valida.resultado import Resultado
from .base import Agente, Contexto, bloque, preguntar_validando
from .cliente import ClienteLLM
from .contratos import SalidaDirector, Sobre


def agente(cliente: ClienteLLM | None = None) -> Agente:
    kwargs = {"cliente": cliente} if cliente is not None else {}
    return Agente(nombre="director", skill="director-vertical", modelo="claude-sonnet-5",
                  effort="medium", max_tokens=8000, **kwargs)


def contexto_estable(biblia_md: str, estilo_md: str, registro: reg.Registro) -> list[str]:
    """El bloque que se repite en cada plano. Se cachea entero (1 h)."""
    fichas = []
    for asset in registro.assets():
        lineas = [f"## {asset.id}  ({asset.estado})", asset.descriptor]
        if asset.voz_lock:
            lineas.append(f"AUDIO LOCK: {asset.voz_lock}")
        if asset.mapa:
            lineas.append(f"MAPA: {asset.mapa}")
        fichas.append("\n".join(lineas))
    return [
        bloque("Biblia de la serie", biblia_md),
        bloque("Estilo · copia estos bloques palabra por palabra", estilo_md),
        bloque("Registro de assets · descriptores congelados", "\n\n".join(fichas)),
    ]


def _peticion(plano: Plano, registro: reg.Registro) -> str:
    refs = "\n".join(f"- {t}: {registro.descriptor(t)}" for t in plano.refs
                     if registro.existe(t)) or "- (ninguna)"
    dialogo = plano.dialogo or "(sin diálogo)"
    return f"""
Escribe el prompt del plano {plano.id}.

- Tamaño: {plano.tamano}
- Cámara: {plano.camara}   (un solo movimiento)
- Duración: {plano.duracion} s
- Máster de geografía: {"sí" if plano.es_master else "no"}
- Diálogo: {dialogo}
- Referencias activas (cópialas palabra por palabra):
{refs}

Recuerda: el prompt es una isla (nada heredado de otro plano), el STYLE PREFIX y los
CONSTRAINTS van copiados literalmente, el audio dice "No music", y los límites se
escriben como condición de toma fallida, no como prohibiciones sueltas.
""".strip()


def escribir_prompt(plano: Plano, registro: reg.Registro, *, biblia_md: str, estilo_md: str,
                    serie: str = "", intento: int = 1,
                    cliente: ClienteLLM | None = None) -> Sobre:
    """Un plano → un prompt validado, o un rechazo con su código."""
    contexto = Contexto(serie=serie, episodio=plano.id_plano.id_episodio, plano=plano.id,
                        intento=intento,
                        estable=contexto_estable(biblia_md, estilo_md, registro))

    def validador(salida: SalidaDirector) -> Resultado:
        return valida_prompt(salida.prompt, style_md=estilo_md, registro=registro, plano=plano)

    return preguntar_validando(agente(cliente), _peticion(plano, registro), SalidaDirector,
                               contexto, validador)
