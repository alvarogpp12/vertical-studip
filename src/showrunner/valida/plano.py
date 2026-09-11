"""Validación de un plano del shotlist, antes de escribir su prompt.

R-09 vive aquí: si el diálogo no cabe en la duración, el modelo lo recorta o lo
acelera, y la toma sale mal sin que el QC sepa por qué.
"""
from __future__ import annotations

import re

from ..config import cargar_modelos
from ..dominio.eventos import EstadoPlano
from ..dominio.registro import Registro
from ..dominio.shotlist import PALABRAS_POR_SEGUNDO, Plano, Shotlist
from .resultado import Resultado

#: Gramática de cámara admitida en vertical (00_investigacion_sistema.md).
MOVIMIENTOS = {
    "push-in": r"push[- ]?in|acercamiento|avance",
    "pull-back": r"pull[- ]?back|retroceso|alejamiento",
    "tilt": r"\btilt\b|cabeceo",
    "fijo": r"\bfijo\b|static|locked|tripode|trípode",
}
#: Lo que no se traslada al vertical.
PROHIBIDOS = {
    "travelling lateral": r"travell?ing lateral|lateral track|dolly lateral|pan(?:eo)? lateral",
    "cámara en mano": r"c[aá]mara en mano|handheld|shaky",
    "grúa": r"\bcrane\b|gr[uú]a",
}
NIVELES_ORDEN = {"borrador": 0, "trabajo": 1, "clave": 2}


def _movimientos_en(camara: str) -> list[str]:
    texto = camara.lower()
    return [n for n, patron in MOVIMIENTOS.items() if re.search(patron, texto)]


def valida_plano(plano: Plano, *, registro: Registro | None = None, modelo: str = "",
                 estado: EstadoPlano | None = None) -> Resultado:
    r = Resultado()

    # R-09 · el diálogo cabe a ~4 palabras/s + 1 s de cola limpia
    if not plano.cabe_el_dialogo:
        r.error("DIALOGO_NO_CABE",
                f"{plano.palabras_dialogo} palabras necesitan "
                f"{plano.duracion_minima:.1f} s "
                f"(a {PALABRAS_POR_SEGUNDO:g} palabras/s + 1 s de cola) "
                f"y el plano dura {plano.duracion} s",
                "R-09")

    # Un solo movimiento de cámara, y de los que funcionan en vertical
    movimientos = _movimientos_en(plano.camara)
    if len(movimientos) > 1:
        r.error("CAMARA_MULTIPLE",
                f"más de un movimiento de cámara en el mismo plano: {movimientos}", "vertical")
    for nombre, patron in PROHIBIDOS.items():
        if re.search(patron, plano.camara.lower()):
            r.error("CAMARA_PROHIBIDA",
                    f"«{nombre}» no se traslada al vertical; usa tilt o push-in", "vertical")

    # R-06 · el máster fija geografía: corto y sin diálogo
    if plano.es_master:
        if plano.duracion > 2:
            r.aviso("MASTER_LARGO", f"el máster de geografía dura {plano.duracion} s; 1 s basta",
                    "R-06")
        if plano.dialogo.strip():
            r.error("MASTER_CON_DIALOGO", "el máster fija la geografía, no lleva diálogo", "R-06")

    # R-01 · toda referencia del plano tiene que estar registrada
    if registro is not None:
        for tag in plano.refs:
            if not registro.existe(tag):
                r.error("TAG_NO_REGISTRADO", f"{tag} no está en registry.json", "R-01")
            elif registro.resolver(tag).estado != "aprobado":
                r.aviso("ASSET_NO_APROBADO",
                        f"{tag} está en estado «{registro.resolver(tag).estado}»", "R-01")

    # La duración tiene que caber en el modelo elegido
    if modelo:
        spec = cargar_modelos().get(modelo)
        if spec is None:
            r.error("MODELO_DESCONOCIDO", f"{modelo} no está en config/modelos.yaml")
        else:
            if plano.duracion > spec["max_duracion"]:
                r.error("DURACION_SOBRE_MODELO",
                        f"{modelo} genera como mucho {spec['max_duracion']} s "
                        f"y el plano pide {plano.duracion} s")
            if spec["nivel"] != plano.nivel:
                r.aviso("NIVEL_DISTINTO",
                        f"el plano pide nivel «{plano.nivel}» y {modelo} es de nivel "
                        f"«{spec['nivel']}»")
            refs = spec["referencias"]
            if len(plano.refs) > refs["imagenes"]:
                r.error("DEMASIADAS_REFERENCIAS",
                        f"{modelo} admite {refs['imagenes']} imágenes de referencia y el plano "
                        f"usa {len(plano.refs)} tags")

    # Nivel «clave» sólo con una toma ya aprobada en borrador
    aprobado_en_borrador = estado is not None and estado.estado in ("aceptado", "empalmable")
    if plano.nivel == "clave" and estado is not None and not aprobado_en_borrador:
        r.error("CLAVE_SIN_BORRADOR",
                "no se sube a nivel «clave» sin una toma aprobada en borrador", "R-12")

    # R-11 · cortacircuitos de intentos
    if estado is not None and estado.agotado:
        r.error("INTENTOS_AGOTADOS",
                f"{estado.intentos} intentos sin toma válida: cambia el plano o escala al humano",
                "R-11")
    return r


def valida_shotlist(shotlist: Shotlist, *, registro: Registro | None = None,
                    duracion_min: float = 61.0, duracion_max: float = 90.0) -> Resultado:
    r = Resultado()
    for plano in shotlist.planos:
        r.unir(valida_plano(plano, registro=registro))
    total = shotlist.duracion_total
    if total < duracion_min:
        r.error("EPISODIO_CORTO",
                f"el shotlist suma {total} s y el mínimo es {duracion_min:g} s", "plataformas")
    if total > duracion_max:
        r.aviso("EPISODIO_LARGO", f"el shotlist suma {total} s (objetivo ≤ {duracion_max:g} s)")
    if shotlist.planos and not any(p.es_master for p in shotlist.planos):
        r.aviso("SIN_MASTER",
                "ningún plano marcado como máster: la geografía va antes que la acción", "R-06")
    return r
