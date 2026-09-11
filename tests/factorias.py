"""Salidas de agente de mentira, válidas, para los tests y las evaluaciones."""
from __future__ import annotations

from showrunner.agentes.contratos import (
    Beat,
    Biblia,
    Concepto,
    EpisodioPlaneado,
    Estilo,
    FormulaEpisodio,
    Localizacion,
    Paleta,
    PerfilActuacion,
    Personaje,
    PlanoPropuesto,
    SalidaDirector,
    SalidaGuionista,
    SalidaQC,
    SalidaShowrunner,
    Sobre,
    StressTest,
)

DESCRIPTOR_NADIA = ("Woman in her early forties, short black hair, a thin scar through the left "
                    "eyebrow, grey wool coat over a dark green shirt.")
DESCRIPTOR_DESPACHO = ("A narrow municipal office: grey filing cabinets along the left wall, a "
                       "steel desk under a tall window, cold north light on scuffed linoleum.")
STYLE_PREFIX = ("Style: gritty 90s film look, vertical 9:16 composition, hard key light from a "
                "single window, palette #101010 #8A8F98 #B3372B, fine grain, 85mm lens, tripod, "
                "tilts and push-ins only.")
CONSTRAINTS = ("Photoreal live-action. Identities, hair and wardrobe match their @tag references "
               "in every shot. Faces blink and breathe; eyes wet and alive with catch-lights. "
               "Only scripted lines are spoken, about four words per second, one second of clean "
               "silence at the end. No music — diegetic sound only. Location references control "
               "geometry, materials and light only. Subject kept inside the vertical safe zone: "
               "eyes on the upper third, lower fifth clear for subtitles.")


def personaje(nombre: str = "Nadia") -> Personaje:
    return Personaje(
        nombre=nombre,
        descriptor_congelado=DESCRIPTOR_NADIA,
        anclas_identidad=["cicatriz en la ceja izquierda", "anillo de sello"],
        voz_lock="AUDIO LOCK: voz grave, tempo lento, frases cortas, acento del norte.",
        perfil=PerfilActuacion(mascara_publica="jueza impecable",
                               que_la_rompe="que le mientan sus hijos",
                               habitos_fisicos="alinea los papeles cuando duda",
                               forma_de_caminar="pasos cortos, hombros altos"),
        objetivo_temporada="proteger a su hija sin romper la ley",
    )


def biblia(titulo: str = "Cañón Rojo", personajes: int = 1, localizaciones: int = 1) -> Biblia:
    return Biblia(
        titulo=titulo,
        logline="Una jueza descubre que la coartada de su hija la incrimina a ella.",
        genero_y_tono="thriller doméstico, seco",
        publico_y_plataforma="25–45, TikTok",
        promesa_del_formato="cada episodio revela una mentira nueva",
        producibilidad=8,
        motivo_producibilidad="dos personajes, un despacho, nada de acción",
        formula=FormulaEpisodio(gancho="un sobre con su propia firma falsificada",
                                giro="la firma es real",
                                cliffhanger="alguien más tiene una copia"),
        epoca_y_lugar="una capital de provincia, hoy",
        reglas_del_mundo=["nadie puede salir del edificio", "los archivos son de papel"],
        regla_visual_narrativa="el rojo sólo aparece cuando alguien miente",
        personajes=[personaje(n) for n in ["Nadia", "Marta", "Iker", "Bruno"][:personajes]],
        localizaciones=[
            Localizacion(nombre=n, descriptor_congelado=DESCRIPTOR_DESPACHO,
                         mapa_vertical="Nadia a la izquierda del escritorio de acero, la ventana "
                                       "al fondo; la cámara mira al norte.",
                         estados=["día", "noche"])
            for n in ["Despacho", "Archivo", "Pasillo", "Garaje"][:localizaciones]
        ],
        props=[],
        riesgos_de_produccion=["nada de manos escribiendo en primer plano",
                               "el cambio de vestuario se hace fuera de cámara"],
    )


def biblia_sin_mapa() -> Biblia:
    """Biblia construible pero inválida: la localización no trae mapa vertical (R-06)."""
    b = biblia()
    b.localizaciones[0].mapa_vertical = ""
    return b


def estilo() -> Estilo:
    return Estilo(style_prefix=STYLE_PREFIX, constraints=CONSTRAINTS,
                  paleta=Paleta(dominante="#101010", secundaria="#8A8F98",
                                acento_reservado="#B3372B",
                                significado_del_acento="aparece sólo cuando alguien miente"))


def concepto(titulo: str) -> Concepto:
    return Concepto(titulo=titulo, logline="x", mundo="y", motor_de_temporada="z",
                    personajes=2, localizaciones=2, producibilidad=8,
                    motivo_producibilidad="pocos elementos", riesgo_principal="ninguno")


def salida_showrunner(**cambios) -> SalidaShowrunner:
    datos: dict = {
        "conceptos": [concepto("A"), concepto("B"), concepto("C")],
        "concepto_elegido": 1,
        "motivo_eleccion": "es el más barato de rodar",
        "biblia": biblia(),
        "estilo": estilo(),
        "temporada": [EpisodioPlaneado(numero=1, titulo="El sobre", gancho="g", giro="t",
                                       cliffhanger="c")],
        "stress_test": [StressTest(episodio=1, objetivo="o", obstaculo="ob", tactica="t",
                                   giro="g", cambio_de_valor="v",
                                   punto_mas_debil="el giro llega tarde")],
    }
    datos.update(cambios)
    return SalidaShowrunner(**datos)


def salida_guionista(**cambios) -> SalidaGuionista:
    planos = [
        PlanoPropuesto(orden=1, beat=1, duracion=1, tamano="plano general", camara="fijo",
                       refs=["@loc_canon-rojo_Despacho_v1"], es_master=True),
        PlanoPropuesto(orden=2, beat=1, duracion=30, tamano="primer plano", camara="push-in",
                       refs=["@char_canon-rojo_Nadia_v1"], dialogo="Esta firma no es mía"),
        PlanoPropuesto(orden=3, beat=3, duracion=30, tamano="plano medio", camara="tilt",
                       refs=["@char_canon-rojo_Nadia_v1"], dialogo="Entonces es peor"),
    ]
    datos: dict = {
        "titulo": "El sobre",
        "beats": [Beat(numero=1, funcion="gancho", texto="Nadia abre el sobre."),
                  Beat(numero=2, funcion="giro", texto="La firma es suya."),
                  Beat(numero=3, funcion="cliffhanger", texto="Hay una segunda copia.")],
        "planos": planos,
        "duracion_total": sum(p.duracion for p in planos),
        "gancho_3s": "un sobre abierto con su firma",
        "cliffhanger": "alguien más tiene una copia",
    }
    datos.update(cambios)
    return SalidaGuionista(**datos)


#: tag → descriptor congelado, tal y como están en el registro de prueba.
DESCRIPTORES = {
    "@char_canon-rojo_Nadia_v1": DESCRIPTOR_NADIA,
    "@loc_canon-rojo_Despacho_v1": DESCRIPTOR_DESPACHO,
}


def salida_guionista_corta() -> SalidaGuionista:
    """Episodio de 6 s: sirve para todo menos para comprobar el mínimo de TikTok.

    Los tests que no miden la duración lo usan para no pasarse un minuto
    recodificando vídeo de prueba.
    """
    planos = [
        PlanoPropuesto(orden=1, beat=1, duracion=1, tamano="plano general", camara="fijo",
                       refs=["@loc_canon-rojo_Despacho_v1"], es_master=True),
        PlanoPropuesto(orden=2, beat=1, duracion=3, tamano="primer plano", camara="push-in",
                       refs=["@char_canon-rojo_Nadia_v1"], dialogo="No es mia"),
        PlanoPropuesto(orden=3, beat=3, duracion=2, tamano="plano medio", camara="tilt",
                       refs=["@char_canon-rojo_Nadia_v1"]),
    ]
    return salida_guionista(planos=planos, duracion_total=6)


def prompt_valido(plano_refs: list[str] | None = None) -> str:
    refs = plano_refs or ["@char_canon-rojo_Nadia_v1"]
    citas = "\n".join(f"{t} — {DESCRIPTORES.get(t, DESCRIPTOR_NADIA)}" for t in refs)
    return f"""# STYLE PREFIX (inmutable durante toda la serie)
{STYLE_PREFIX}

SCENE CONTEXT
A municipal office at noon.

ACTIVE REFERENCES
{citas}

PERFORMANCE
She squares the papers against the desk twice, then sets them down. Eyes wet and alive.

CAMERA
Slow push-in from medium to close-up, tripod.

AUDIO
No music — diegetic sound only.

CONSTRAINTS (inmutable)
{CONSTRAINTS}

POSITIVE LOCKS
A second person entering frame = failed take.
"""


def salida_director(refs: list[str] | None = None, **cambios) -> SalidaDirector:
    refs = refs or ["@char_canon-rojo_Nadia_v1"]
    datos: dict = {"prompt": prompt_valido(refs), "referencias_activas": refs,
                   "riesgos_detectados": ["el primer fotograma podría salir vacío"]}
    datos.update(cambios)
    return SalidaDirector(**datos)


def salida_qc(**cambios) -> SalidaQC:
    datos: dict = {"veredicto": "aceptada", "motivo_codigo": "ACEPTADA",
                   "motivo": "identidad y eje correctos", "hallazgos": [],
                   "segundos_utiles": 0.0, "confianza": 0.9, "requiere_humano": False}
    datos.update(cambios)
    return SalidaQC(**datos)


def sobre(resultado) -> Sobre:
    return Sobre[type(resultado)](tipo="resultado", resultado=resultado, rechazo=None)
