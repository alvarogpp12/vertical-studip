"""Los cuatro agentes, sin red y sin gastar: `ClienteFalso` devuelve lo que se le encola."""
from __future__ import annotations

import factorias as f
import pytest

from showrunner.agentes import director, guionista, qc, showrunner
from showrunner.agentes.base import cargar_skill
from showrunner.agentes.cliente import ClienteFalso, esquema_estricto
from showrunner.agentes.contratos import SalidaDirector, Sobre
from showrunner.dominio import eventos as ev
from showrunner.dominio import registro as reg


def _registro() -> reg.Registro:
    r = reg.Registro(serie="canon-rojo")
    r.anadir(reg.Asset(id="@char_canon-rojo_Nadia_v1", descriptor=f.DESCRIPTOR_NADIA,
                       estado="aprobado"))
    r.anadir(reg.Asset(id="@loc_canon-rojo_Despacho_v1", descriptor=f.DESCRIPTOR_DESPACHO,
                       estado="aprobado", mapa="Nadia a la izquierda del escritorio."))
    return r


STYLE_MD = f"""# STYLE PREFIX (inmutable durante toda la serie)
{f.STYLE_PREFIX}

# CONSTRAINTS (inmutable)
{f.CONSTRAINTS}

# PALETA (hex)
- dominante: #101010
"""


def test_la_skill_es_el_system_prompt():
    """Una sola fuente: el mismo SKILL.md que se afina a mano en Claude Code."""
    texto = cargar_skill("director-vertical")
    assert texto.startswith("# Director vertical")
    assert "name: director-vertical" not in texto      # el frontmatter YAML se quita


def test_el_esquema_sale_estricto():
    esquema = esquema_estricto(Sobre[SalidaDirector])
    assert esquema["additionalProperties"] is False
    assert esquema["required"] == ["tipo", "resultado", "rechazo"]
    interno = esquema["$defs"]["SalidaDirector"]
    assert interno["required"] == ["prompt", "referencias_activas", "riesgos_detectados"]


def test_solo_hay_un_punto_de_cache_y_va_al_final():
    """Lo estable delante, el breakpoint al final, lo volátil en `messages`."""
    cliente = ClienteFalso([f.sobre(f.salida_director())])
    ag = director.agente(cliente)
    sistema = ag.sistema(director.Contexto(estable=director.contexto_estable(
        "biblia", STYLE_MD, _registro())))
    concache = [b for b in sistema if "cache_control" in b]
    assert len(concache) == 1 and concache[0] is sistema[-1]
    assert concache[0]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
    assert sistema[0]["text"].startswith("# Director vertical")


# --------------------------------------------------------------- showrunner
def test_showrunner_devuelve_biblia_valida():
    cliente = ClienteFalso([f.sobre(f.salida_showrunner())])
    sobre = showrunner.crear_biblia("Una jueza descubre que su hija miente.", "Cañón Rojo",
                                    cliente=cliente)
    assert sobre.ok
    assert sobre.resultado.biblia.titulo == "Cañón Rojo"
    assert len(cliente.llamadas) == 1
    assert cliente.llamadas[0]["modelo"] == "claude-opus-5"
    assert cliente.llamadas[0]["effort"] == "xhigh"


def test_showrunner_reintenta_una_vez_y_luego_rechaza():
    """Corregir texto es barato; inventarse una biblia que no cumple, no."""
    mala = f.salida_showrunner(biblia=f.biblia_sin_mapa())
    cliente = ClienteFalso([f.sobre(mala), f.sobre(mala)])
    sobre = showrunner.crear_biblia("idea", "Cañón Rojo", cliente=cliente)
    assert not sobre.ok
    assert sobre.rechazo.motivo_codigo == "SIN_MAPA"
    assert sobre.rechazo.destinatario == "humano"
    assert len(cliente.llamadas) == 2
    assert "SIN_MAPA" in cliente.llamadas[1]["mensajes"][0]["content"]


def test_showrunner_acepta_la_correccion_del_segundo_intento():
    cliente = ClienteFalso([f.sobre(f.salida_showrunner(biblia=f.biblia_sin_mapa())),
                            f.sobre(f.salida_showrunner())])
    assert showrunner.crear_biblia("idea", "Cañón Rojo", cliente=cliente).ok


def test_el_rechazo_del_modelo_queda_registrado():
    from showrunner.agentes.contratos import SalidaShowrunner

    rechazo = Sobre[SalidaShowrunner](
        tipo="rechazo", resultado=None,
        rechazo={"destinatario": "humano", "motivo_codigo": "IDEA_INSUFICIENTE",
                 "detalle": "la idea no tiene conflicto", "regla": ""})
    cliente = ClienteFalso([rechazo])
    sobre = showrunner.crear_biblia("x", "Cañón Rojo", cliente=cliente)
    assert not sobre.ok
    registrados = [e for e in ev.leer() if e["tipo"] == "rechazo"]
    assert registrados[0]["payload"]["motivo_codigo"] == "IDEA_INSUFICIENTE"
    assert registrados[0]["payload"]["emisor"] == "showrunner"


def test_cada_llamada_deja_su_coste():
    cliente = ClienteFalso([f.sobre(f.salida_showrunner())])
    showrunner.crear_biblia("idea", "Cañón Rojo", cliente=cliente)
    llamadas = [e for e in ev.leer() if e["tipo"] == "llm_llamada"]
    assert len(llamadas) == 1
    assert llamadas[0]["payload"]["agente"] == "showrunner"
    assert llamadas[0]["payload"]["cache_lectura"] == 1000


# ---------------------------------------------------------------- guionista
def test_el_guionista_no_inventa_ids():
    """Los ids los asigna el código: `s01_ep01_shNNN`, en orden de montaje."""
    lista = guionista.a_shotlist(f.salida_guionista(), "s01_ep01")
    assert [p.id for p in lista.planos] == ["s01_ep01_sh001", "s01_ep01_sh002", "s01_ep01_sh003"]
    assert lista.planos[0].es_master and lista.planos[0].orden_montaje == 1
    assert lista.duracion_total == 61


def test_el_guionista_rechaza_un_episodio_corto():
    corta = f.salida_guionista(planos=[
        f.PlanoPropuesto(orden=1, beat=1, duracion=1, tamano="general", camara="fijo",
                         refs=[], es_master=True),
        f.PlanoPropuesto(orden=2, beat=3, duracion=5, tamano="primer plano", camara="tilt",
                         refs=[]),
    ], duracion_total=6)
    cliente = ClienteFalso([f.sobre(corta), f.sobre(corta)])
    from showrunner.dominio.serie import Proyecto

    sobre = guionista.escribir_episodio(
        "biblia", STYLE_MD, _registro(), id_episodio="s01_ep01",
        proyecto=Proyecto(slug="canon-rojo", titulo="Cañón Rojo"), cliente=cliente)
    assert not sobre.ok and sobre.rechazo.motivo_codigo == "EPISODIO_CORTO"


# ----------------------------------------------------------------- director
def _plano():
    from showrunner.dominio.shotlist import Plano

    return Plano(id="s01_ep01_sh002", duracion=5, tamano="primer plano", camara="push-in",
                 refs=["@char_canon-rojo_Nadia_v1"], dialogo="Esta firma no es mía")


def test_director_entrega_un_prompt_que_pasa_el_linter():
    cliente = ClienteFalso([f.sobre(f.salida_director())])
    sobre = director.escribir_prompt(_plano(), _registro(), biblia_md="biblia",
                                     estilo_md=STYLE_MD, serie="canon-rojo", cliente=cliente)
    assert sobre.ok, sobre.rechazo
    assert cliente.llamadas[0]["modelo"] == "claude-sonnet-5"


def test_director_rechaza_si_el_prompt_no_supera_el_linter():
    """El linter corre sobre la salida del agente: el prompt malo no sale de aquí."""
    malo = f.salida_director(prompt="SCENE: @char_canon-rojo_Fantasma_v1 looks sad.\n")
    cliente = ClienteFalso([f.sobre(malo), f.sobre(malo)])
    sobre = director.escribir_prompt(_plano(), _registro(), biblia_md="biblia",
                                     estilo_md=STYLE_MD, serie="canon-rojo", cliente=cliente)
    assert not sobre.ok
    assert sobre.rechazo.motivo_codigo in {"STYLE_PREFIX_AUSENTE", "TAG_NO_REGISTRADO"}
    assert len(cliente.llamadas) == 2


# ----------------------------------------------------------------------- QC
def test_qc_acepta_con_confianza_alta(tmp_path):
    foto = tmp_path / "f0.png"
    foto.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 32)
    cliente = ClienteFalso([f.sobre(f.salida_qc())])
    sobre = qc.revisar([foto], _registro(), ["@char_canon-rojo_Nadia_v1"], duracion=5,
                       plano="s01_ep01_sh002", cliente=cliente)
    assert sobre.ok and sobre.resultado.veredicto == "aceptada"
    assert len(cliente.llamadas) == 1 and cliente.llamadas[0]["modelo"] == "claude-sonnet-5"


def test_qc_escala_al_modelo_grande_si_duda(tmp_path):
    """Los artefactos finos se detectan mal: ante la duda, el modelo grande."""
    foto = tmp_path / "f0.png"
    foto.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 32)
    cliente = ClienteFalso([f.sobre(f.salida_qc(confianza=0.4, requiere_humano=True)),
                            f.sobre(f.salida_qc(veredicto="rechazada",
                                                motivo_codigo="ARTEFACTOS",
                                                motivo="seis dedos", confianza=0.85))])
    sobre = qc.revisar([foto], _registro(), ["@char_canon-rojo_Nadia_v1"], duracion=5,
                       cliente=cliente)
    assert [ll["modelo"] for ll in cliente.llamadas] == ["claude-sonnet-5", "claude-opus-5"]
    assert sobre.resultado.veredicto == "rechazada"


def test_qc_manda_los_fotogramas_como_imagenes(tmp_path):
    foto = tmp_path / "f0.png"
    foto.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 32)
    cliente = ClienteFalso([f.sobre(f.salida_qc())])
    qc.revisar([foto], _registro(), [], duracion=5, cliente=cliente)
    contenido = cliente.llamadas[0]["mensajes"][0]["content"]
    assert any(b.get("type") == "image" for b in contenido)


def test_cliente_falso_exige_el_formato_pedido():
    from showrunner.agentes.cliente import RespuestaIlegible

    cliente = ClienteFalso([f.salida_qc()])      # sin envolver en Sobre
    with pytest.raises(RespuestaIlegible):
        qc.revisar([], _registro(), [], duracion=5, cliente=cliente)
