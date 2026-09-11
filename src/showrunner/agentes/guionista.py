"""Agente 2 · guionista (incluye la planificación de planos): biblia → guion + shotlist.

Aquí viven R-09 («No music» siempre; el diálogo cabe a ~4 palabras/s + 1 s de cola) y
R-10 (escribir alrededor de las debilidades del modelo), que hasta ahora no tenían
dueño: el guion se escribía sin saber qué sabe rodar el modelo.

El agente **no inventa ids de plano**: propone un orden y el código asigna
`s01_ep01_shNNN`. Un id lo genera el código o no es fiable.
"""
from __future__ import annotations

from pathlib import Path

from ..dominio import memoria as mem
from ..dominio import registro as reg
from ..dominio import shotlist as sl
from ..dominio.identidad import IdPlano, parse_episodio
from ..dominio.serie import Proyecto
from ..valida.biblia import valida_salida_guionista
from .base import Agente, Contexto, bloque, preguntar_validando
from .cliente import ClienteLLM
from .contratos import SalidaGuionista, Sobre


def agente(cliente: ClienteLLM | None = None) -> Agente:
    kwargs = {"cliente": cliente} if cliente is not None else {}
    return Agente(nombre="guionista", skill="guionista", modelo="claude-opus-5",
                  effort="high", max_tokens=32000, **kwargs)


def fichas_de_assets(registro: reg.Registro) -> str:
    """Lo único que el guionista puede citar. Con descriptor: si no sabe qué es un
    `@tag`, lo coloca mal."""
    fichas = []
    for asset in registro.assets():
        linea = f"- {asset.id} ({asset.estado}): {asset.descriptor}"
        if asset.mapa:
            linea += f"\n    mapa: {asset.mapa}"
        fichas.append(linea)
    return "\n".join(fichas) or "- (ninguno)"


def _peticion(id_episodio: str, proyecto: Proyecto, sinopsis: str, registro: reg.Registro,
              recuerdo: str) -> str:
    return f"""
Escribe el episodio {id_episodio} de «{proyecto.titulo}».

{recuerdo}

Punto de partida (de la sinopsis): {sinopsis or "(libre, respetando la biblia)"}

Restricciones duras:
- Duración total {proyecto.duracion_objetivo_min}–{proyecto.duracion_objetivo_max} s. El primer
  plano es un máster de 1 s que fija la geografía (R-06).
- Gancho en los primeros 3 s y cliffhanger al final.
- Cada plano: UN solo movimiento de cámara (tilt, push-in, pull-back o fijo). Nada de
  travellings laterales, cámara en mano ni planos corales: es vertical.
- El diálogo de un plano cabe a 4 palabras por segundo más 1 segundo de cola limpia.
  Si no cabe, parte el plano.
- Sólo puedes usar los `@tag` de la sección «Assets registrados», escritos tal cual.
  Si el episodio necesita uno que no está, rechaza con `ASSET_INEXISTENTE`.
- Escribe alrededor de lo que el modelo hace mal: transformaciones fuera de cámara,
  cambios de estado en un barrido, nada de multitudes ni de rebobinados.

Devuelve los beats y la lista de planos numerada por `orden`, empezando en 1.
""".strip()


def escribir_episodio(biblia_md: str, estilo_md: str, registro: reg.Registro, *,
                      id_episodio: str, proyecto: Proyecto, sinopsis: str = "",
                      base: Path | None = None, cliente: ClienteLLM | None = None) -> Sobre:
    """Escribe un episodio.

    Lo que no cambia entre episodios —biblia, estilo, assets— va en el bloque
    cacheado. La memoria de la serie cambia en cada episodio, así que viaja en el
    mensaje: meterla en el prefijo invalidaría la caché en cada llamada.
    """
    recuerdo = mem.resumen(base, id_episodio) if base else ""
    contexto = Contexto(
        serie=proyecto.slug, episodio=id_episodio,
        estable=[bloque("Biblia de la serie", biblia_md),
                 bloque("Estilo (inmutable)", estilo_md),
                 bloque("Assets registrados · lo único que puedes citar",
                        fichas_de_assets(registro))],
    )
    validador = lambda salida: valida_salida_guionista(  # noqa: E731
        salida, duracion_min=proyecto.duracion_min,
        duracion_max=proyecto.duracion_objetivo_max)
    return preguntar_validando(
        agente(cliente), _peticion(id_episodio, proyecto, sinopsis, registro, recuerdo),
        SalidaGuionista, contexto, validador,
    )


def a_shotlist(salida: SalidaGuionista, id_episodio: str) -> sl.Shotlist:
    """Convierte la propuesta del agente en un shotlist con ids canónicos."""
    temporada, numero = parse_episodio(id_episodio)
    planos = []
    for posicion, propuesto in enumerate(sorted(salida.planos, key=lambda p: p.orden), start=1):
        planos.append(sl.Plano(
            id=str(IdPlano(temporada, numero, posicion)),
            beat=propuesto.beat,
            duracion=propuesto.duracion,
            tamano=propuesto.tamano,
            camara=propuesto.camara,
            refs=propuesto.refs,
            dialogo=propuesto.dialogo,
            nivel=propuesto.nivel,
            es_master=propuesto.es_master,
            orden_montaje=posicion,
            notas=propuesto.notas,
        ))
    return sl.Shotlist(episodio=id_episodio, planos=planos)


def a_guion_md(salida: SalidaGuionista, id_episodio: str) -> str:
    lineas = [f"# {id_episodio.upper()} · {salida.titulo}",
              f"> Gancho (0–3 s): {salida.gancho_3s}",
              f"> Cliffhanger: {salida.cliffhanger}", ""]
    for beat in sorted(salida.beats, key=lambda b: b.numero):
        lineas.append(f"## Beat {beat.numero} · {beat.funcion.upper()}")
        lineas.append(beat.texto)
        lineas.append("")
    return "\n".join(lineas)
