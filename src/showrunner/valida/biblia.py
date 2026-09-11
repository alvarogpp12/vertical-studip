"""Validación determinista de la biblia y del guion que produce un agente.

Los umbrales salen de `docs/conocimiento/`: producibilidad (≤3 personajes, ≤3
localizaciones), gancho en 0–3 s, 61–90 s por episodio, «No music» en CONSTRAINTS,
paleta en hex. No es una opinión sobre la historia: es lo que se puede comprobar.
"""
from __future__ import annotations

import re

from ..agentes.contratos import Biblia, Estilo, SalidaGuionista, SalidaShowrunner
from ..dominio.identidad import IdInvalido, Tag, slugify
from .resultado import Resultado

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
MAX_PERSONAJES = 3
MAX_LOCALIZACIONES = 3
PRODUCIBILIDAD_MINIMA = 6


def valida_estilo(estilo: Estilo) -> Resultado:
    r = Resultado()
    if "9:16" not in estilo.style_prefix:
        r.error("STYLE_SIN_VERTICAL", "el STYLE PREFIX no declara composición 9:16", "R-03")
    if not re.search(r"\bno\s+music\b", estilo.constraints, re.IGNORECASE):
        r.error("SIN_NO_MUSIC", 'CONSTRAINTS no incluye literalmente "No music"', "R-09")
    for campo in ("dominante", "secundaria", "acento_reservado"):
        valor = getattr(estilo.paleta, campo)
        if not HEX.match(valor):
            r.error("PALETA_NO_HEX", f"paleta.{campo} = «{valor}» no es un hex #RRGGBB", "R-03")
    return r


def valida_biblia(biblia: Biblia, serie: str = "serie") -> Resultado:
    r = Resultado()
    if len(biblia.personajes) > MAX_PERSONAJES:
        r.error("DEMASIADOS_PERSONAJES",
                f"{len(biblia.personajes)} personajes; el máximo producible es {MAX_PERSONAJES}",
                "producibilidad")
    if len(biblia.localizaciones) > MAX_LOCALIZACIONES:
        r.error("DEMASIADAS_LOCALIZACIONES",
                f"{len(biblia.localizaciones)} localizaciones; el máximo es {MAX_LOCALIZACIONES}",
                "producibilidad")
    if not biblia.personajes:
        r.error("SIN_PERSONAJES", "la biblia no define ningún personaje", "R-01")
    if biblia.producibilidad < PRODUCIBILIDAD_MINIMA:
        r.aviso("PRODUCIBILIDAD_BAJA",
                f"producibilidad {biblia.producibilidad}/10: cada plano costará varios intentos")

    for personaje in biblia.personajes:
        _valida_nombre_de_tag(r, "char", serie, personaje.nombre)
        if not personaje.descriptor_congelado.strip():
            r.error("DESCRIPTOR_VACIO", f"{personaje.nombre} no tiene descriptor congelado", "R-02")
        if not personaje.voz_lock.strip():
            r.error("SIN_VOZ_LOCK", f"{personaje.nombre} no tiene AUDIO LOCK", "R-02")
        if not personaje.anclas_identidad:
            r.error("SIN_ANCLAS", f"{personaje.nombre} no tiene anclas de identidad", "R-05")
    for local in biblia.localizaciones:
        _valida_nombre_de_tag(r, "loc", serie, local.nombre)
        if not local.mapa_vertical.strip():
            r.error("SIN_MAPA", f"{local.nombre} no tiene mapa espacial vertical", "R-06")
    if not biblia.riesgos_de_produccion:
        r.aviso("SIN_RIESGOS",
                "la biblia no lista planos que el modelo hará mal; es donde se pierde el dinero",
                "R-10")
    return r


def _valida_nombre_de_tag(r: Resultado, tipo: str, serie: str, nombre: str) -> None:
    try:
        Tag.nuevo(tipo, serie or "serie", nombre)
    except IdInvalido:
        r.error("NOMBRE_NO_ETIQUETABLE",
                f"«{nombre}» no sirve para un @tag: usa un nombre propio sin espacios", "R-01")


def valida_salida_showrunner(salida: SalidaShowrunner) -> Resultado:
    r = Resultado()
    serie = slugify(salida.biblia.titulo)
    r.unir(valida_biblia(salida.biblia, serie)).unir(valida_estilo(salida.estilo))
    if not 1 <= salida.concepto_elegido <= len(salida.conceptos):
        r.error("CONCEPTO_FUERA_DE_RANGO",
                f"concepto_elegido={salida.concepto_elegido} con {len(salida.conceptos)} conceptos")
    numeros = [e.numero for e in salida.temporada]
    if len(set(numeros)) != len(numeros):
        r.error("EPISODIOS_REPETIDOS", f"la temporada repite números: {numeros}")
    if not salida.stress_test:
        r.error("SIN_STRESS_TEST", "falta la prueba de estrés de al menos un episodio")
    return r


def valida_salida_guionista(salida: SalidaGuionista, *, duracion_min: float = 61.0,
                            duracion_max: float = 90.0) -> Resultado:
    """Comprobaciones que no dependen del registro; el resto las hace `valida_shotlist`."""
    r = Resultado()
    total = sum(p.duracion for p in salida.planos)
    if total != salida.duracion_total:
        r.error("DURACION_INCOHERENTE",
                f"declara {salida.duracion_total} s y los planos suman {total} s")
    if total < duracion_min:
        r.error("EPISODIO_CORTO", f"{total} s; el mínimo es {duracion_min:g} s", "plataformas")
    if total > duracion_max:
        r.aviso("EPISODIO_LARGO", f"{total} s por encima del objetivo ({duracion_max:g} s)")
    ordenes = [p.orden for p in salida.planos]
    if sorted(ordenes) != list(range(1, len(ordenes) + 1)):
        r.error("ORDEN_INCOMPLETO", f"el orden de los planos no es 1..N: {sorted(ordenes)}")
    if not any(b.funcion == "gancho" for b in salida.beats):
        r.error("SIN_GANCHO", "ningún beat cumple la función de gancho (0–3 s)", "plataformas")
    if not any(b.funcion == "cliffhanger" for b in salida.beats):
        r.error("SIN_CLIFFHANGER", "ningún beat cierra con cliffhanger", "plataformas")
    if not any(p.es_master for p in salida.planos):
        r.error("SIN_MASTER", "ningún plano fija la geografía antes de la acción", "R-06")
    primeros = [p for p in salida.planos if p.orden == 1]
    if primeros and not primeros[0].es_master:
        r.aviso("MASTER_NO_ES_EL_PRIMERO", "el máster debería abrir el episodio", "R-06")
    return r
