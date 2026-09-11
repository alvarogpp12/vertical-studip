"""Validadores: un caso bueno y un caso malo por familia."""
from __future__ import annotations

from showrunner.dominio import serie as ser
from showrunner.dominio.eventos import EstadoPlano
from showrunner.dominio.registro import Asset, Referencia, Registro
from showrunner.dominio.shotlist import Plano, Shotlist
from showrunner.valida import (
    bloques_de_estilo,
    es_vertical,
    valida_episodio,
    valida_plano,
    valida_prompt,
    valida_shotlist,
    valida_toma,
)

STYLE = """# STYLE PREFIX (inmutable durante toda la serie)
Style: gritty 90s film look, vertical 9:16 composition, hard key light, 85mm.

# CONSTRAINTS (inmutable)
Photoreal live-action. Faces blink and breathe. No music — diegetic sound only.

# PALETA (hex)
- dominante: #101010
"""
DESCRIPTOR = "Woman, 40s, short black hair, scar on left brow, grey wool coat."

PROMPT_BUENO = """# STYLE PREFIX (inmutable durante toda la serie)
Style: gritty 90s film look, vertical 9:16 composition, hard key light, 85mm.

ACTIVE REFERENCES
@char_canon-rojo_Nadia_v1 — Woman, 40s, short black hair, scar on left brow, grey wool coat.

PERFORMANCE
She counts the folder pages twice, then squares them against the table. Eyes wet and alive.

CAMERA
Slow push-in from medium to close-up, tripod.

AUDIO
No music — diegetic sound only.

CONSTRAINTS (inmutable)
Photoreal live-action. Faces blink and breathe. No music — diegetic sound only.

POSITIVE LOCKS
A second person entering frame = failed take.
"""


def _registro() -> Registro:
    r = Registro(serie="canon-rojo")
    r.anadir(Asset(id="@char_canon-rojo_Nadia_v1", descriptor=DESCRIPTOR, estado="aprobado",
                   referencias=[Referencia(url="https://x/cara.png", tipo="cara")]))
    return r


def test_bloques_de_estilo():
    bloques = bloques_de_estilo(STYLE)
    assert bloques["style"].startswith("Style: gritty")
    assert "Photoreal live-action" in bloques["constraints"]
    assert "#101010" not in bloques["constraints"]


def test_prompt_bueno_pasa():
    plano = Plano(id="s01_ep01_sh002", duracion=6, camara="push-in",
                  refs=["@char_canon-rojo_Nadia_v1"])
    informe = valida_prompt(PROMPT_BUENO, style_md=STYLE, registro=_registro(), plano=plano)
    assert informe.ok, informe.resumen()


def test_prompt_sin_style_prefix_se_bloquea_antes_de_la_red():
    """R-03: el bloque inmutable tiene que ir copiado palabra por palabra."""
    sin_prefix = PROMPT_BUENO.split("ACTIVE REFERENCES", 1)[1]
    informe = valida_prompt("ACTIVE REFERENCES" + sin_prefix, style_md=STYLE, registro=_registro())
    assert not informe.ok and "STYLE_PREFIX_AUSENTE" in informe.codigos


def test_prompt_con_tag_no_registrado():
    informe = valida_prompt(PROMPT_BUENO.replace("Nadia_v1", "Otra_v1"), style_md=STYLE,
                            registro=_registro())
    assert "TAG_NO_REGISTRADO" in informe.codigos


def test_descriptor_tiene_que_ir_literal():
    """R-02: si el prompt resume el descriptor, la identidad se va."""
    informe = valida_prompt(PROMPT_BUENO.replace("scar on left brow, ", ""), style_md=STYLE,
                            registro=_registro())
    assert "DESCRIPTOR_NO_LITERAL" in informe.codigos


def test_prompt_con_emocion_y_herencia():
    malo = PROMPT_BUENO.replace("She counts the folder pages twice",
                                "She looks sad, same as before")
    informe = valida_prompt(malo, style_md=STYLE, registro=_registro())
    assert {"VOCABULARIO_EMOCION", "PROMPT_NO_ES_ISLA"} <= set(informe.codigos)


def test_prompt_sin_no_music():
    informe = valida_prompt(PROMPT_BUENO.replace("No music — diegetic sound only.", "Soft score."),
                            style_md=STYLE, registro=_registro())
    assert "SIN_NO_MUSIC" in informe.codigos


def test_prompt_con_cara_real_o_ip_ajena():
    informe = valida_prompt(PROMPT_BUENO + "\nShe looks like a celebrity from Netflix.\n",
                            style_md=STYLE, registro=_registro())
    assert "VOCABULARIO_PLATAFORMA" in informe.codigos


def test_plano_bueno():
    assert valida_plano(Plano(id="s01_ep01_sh002", duracion=5, camara="push-in lento",
                              dialogo="No pienso firmar", refs=["@char_canon-rojo_Nadia_v1"]),
                        registro=_registro()).ok


def test_plano_con_dialogo_que_no_cabe():
    informe = valida_plano(Plano(id="s01_ep01_sh002", duracion=3,
                                 dialogo="Una frase demasiado larga para tres segundos de plano "
                                         "por muchas ganas que le pongamos"))
    assert "DIALOGO_NO_CABE" in informe.codigos


def test_plano_con_camara_prohibida_en_vertical():
    informe = valida_plano(
        Plano(id="s01_ep01_sh002", camara="travelling lateral con cámara en mano"))
    assert informe.codigos.count("CAMARA_PROHIBIDA") == 2


def test_master_sin_dialogo():
    informe = valida_plano(Plano(id="s01_ep01_sh001", es_master=True, duracion=1,
                                 dialogo="hola"))
    assert "MASTER_CON_DIALOGO" in informe.codigos


def test_nivel_clave_exige_borrador_aprobado():
    estado = EstadoPlano(plano="s01_ep01_sh002", estado="rechazado", intentos=1)
    informe = valida_plano(Plano(id="s01_ep01_sh002", nivel="clave"), estado=estado)
    assert "CLAVE_SIN_BORRADOR" in informe.codigos


def test_duracion_sobre_el_maximo_del_modelo():
    informe = valida_plano(Plano(id="s01_ep01_sh002", duracion=20), modelo="seedance-2.0@byteplus")
    assert "DURACION_SOBRE_MODELO" in informe.codigos


def test_shotlist_corto_para_tiktok():
    lista = Shotlist(episodio="s01_ep01",
                     planos=[Plano(id="s01_ep01_sh001", duracion=5, es_master=True)])
    informe = valida_shotlist(lista, duracion_min=61)
    assert "EPISODIO_CORTO" in informe.codigos


def test_tolerancia_9_16_admite_la_nativa_de_seedance():
    """496×864 es nativa de Seedance 2.5 y la tolerancia de 0,01 la dejaba fuera."""
    assert es_vertical(496, 864) and es_vertical(720, 1280) and es_vertical(1080, 1920)
    assert not es_vertical(1080, 1440)


def test_toma_buena_y_mala():
    bueno = {"ancho": 720, "alto": 1280, "fps": 24, "duracion": 5.0, "duracion_video": 5.0,
             "audio": True}
    assert valida_toma(bueno, duracion_pedida=5, delta_e=[3.2, 4.1], cortes=[]).ok
    malo = {"ancho": 1080, "alto": 1440, "fps": 30, "duracion": 3.0, "duracion_video": 3.0,
            "audio": False}
    informe = valida_toma(malo, duracion_pedida=5, delta_e=[22.0], cortes=[1.0, 2.0])
    assert {"NO_ES_VERTICAL", "FPS_DISTINTO", "DURACION_DISTINTA", "DERIVA_DE_COLOR",
            "CORTES_INTERNOS"} <= set(informe.codigos)


def test_episodio_corto_o_sin_etiqueta_de_ia():
    proy = ser.nuevo("Cañón Rojo", plataforma="tiktok")
    tecnico = {"ancho": 1080, "alto": 1920, "fps": 24, "duracion": 55.0, "audio": True}
    informe = valida_episodio(tecnico, proyecto=proy, etiqueta_ia=False)
    assert {"EPISODIO_CORTO", "SIN_ETIQUETA_IA"} <= set(informe.codigos)
    tecnico["duracion"] = 72.0
    assert valida_episodio(tecnico, proyecto=proy, etiqueta_ia=True).ok


def test_el_at_tag_del_bloque_constraints_no_cuenta_como_referencia():
    """La plantilla de CONSTRAINTS dice «match their @tag references»: no es un tag."""
    style = STYLE.replace(
        "Photoreal live-action. Faces blink and breathe.",
        "Photoreal live-action. Identities match their @tag references in every shot.")
    prompt = PROMPT_BUENO.replace(
        "Photoreal live-action. Faces blink and breathe.",
        "Photoreal live-action. Identities match their @tag references in every shot.")
    informe = valida_prompt(prompt, style_md=style, registro=_registro())
    assert informe.ok, informe.resumen()
