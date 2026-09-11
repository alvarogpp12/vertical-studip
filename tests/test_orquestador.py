"""El orquestador: gates, idempotencia, fusible y un episodio piloto de punta a punta.

Todo con proveedores mock y `ClienteFalso`: cero red, cero gasto.
"""
from __future__ import annotations

import factorias as f
import pytest

from showrunner.agentes.cliente import ClienteFalso
from showrunner.dominio import eventos as ev
from showrunner.dominio import serie as ser
from showrunner.orquestador import Estado, Orquestador, Politica, producir
from showrunner.qc import sonda

#: Las referencias de cada plano del episodio de prueba, en orden de montaje.
REFS_POR_PLANO = [["@loc_canon-rojo_Despacho_v1"],
                  ["@char_canon-rojo_Nadia_v1"],
                  ["@char_canon-rojo_Nadia_v1"]]


def _cliente(corto: bool = True) -> ClienteFalso:
    """Un showrunner, un guionista y un director por plano, en ese orden."""
    guion = f.salida_guionista_corta() if corto else f.salida_guionista()
    # `ranuras=[]`: el casting de los tests corre con --no-subir, así que las
    # referencias son rutas locales. El modelo no puede leerlas, no ocupan ranura y
    # el prompt no debe citar ninguna @ImageN.
    return ClienteFalso([f.sobre(f.salida_showrunner()), f.sobre(guion),
                         *[f.sobre(f.salida_director(refs, ranuras=[]))
                           for refs in REFS_POR_PLANO]])


def _politica(**cambios) -> Politica:
    datos: dict = {"max_gasto_usd": 5.0, "modelo_video": "mock", "modelo_imagen": "mock-imagen",
                   "subir_referencias": False}
    datos.update(cambios)
    return Politica(**datos)


def _desatendida(**cambios) -> Politica:
    datos: dict = {"max_gasto_usd": 5.0, "modelo_video": "mock", "modelo_imagen": "mock-imagen",
                   "subir_referencias": False}
    datos.update(cambios)
    return Politica.desatendida("alvaro", **datos)


def test_el_plan_dice_donde_esta_la_serie(serie):
    pasos = {p.nombre: p for p in Orquestador("canon-rojo").diagnostico()}
    assert pasos["biblia"].estado is Estado.PENDIENTE
    assert pasos["aprobación de la biblia"].estado is Estado.ESPERA_HUMANO
    assert "showrunner aprobar" in pasos["aprobación de la biblia"].accion


def test_para_en_el_primer_gate_y_no_sigue(serie):
    """CONTROL HUMANO 1: sin firma no se pasa a preproducción."""
    _rebaja(serie)
    informe = producir("canon-rojo", idea="Una jueza y su hija.", politica=_politica(),
                       cliente=_cliente())
    parado = informe.parado_en
    assert parado is not None and parado.nombre == "gate: biblia"
    assert parado.estado is Estado.ESPERA_HUMANO
    assert (serie / "biblia.json").exists()          # el trabajo previo sí se guarda
    assert not (serie / "assets").exists()           # y el casting no ha empezado


def test_el_modo_desatendido_exige_un_responsable():
    with pytest.raises(ValueError):
        Politica.desatendida("")


def test_la_aprobacion_automatica_no_finge_una_firma_humana(serie):
    _rebaja(serie)
    producir("canon-rojo", idea="Una jueza y su hija.", politica=_desatendida(),
             cliente=_cliente(), montar=False)
    aprobacion = ser.cargar(serie / "proyecto.json").aprobacion("biblia")
    assert aprobacion.por == "auto:alvaro"
    assert "automática" in aprobacion.notas
    evento = next(e for e in ev.leer() if e["tipo"] == "aprobacion_humana")
    assert evento["payload"]["automatica"] is True


def _rebaja(serie, *, episodio_corto: bool = True) -> None:
    """Baja el máster (y, si se pide, el mínimo de duración) para no recodificar

    un minuto de vídeo en cada test. El código de montaje es exactamente el mismo;
    lo único que cambia es cuántos píxeles y segundos se mueven.
    """
    proyecto = ser.cargar(serie / "proyecto.json")
    proyecto.resolucion_final = "540x960"
    if episodio_corto:
        proyecto.plataforma = "meta"          # TikTok impone 61 s pase lo que pase
        proyecto.duracion_objetivo_min = 5
    ser.guardar(proyecto, serie / "proyecto.json")


def test_episodio_piloto_de_punta_a_punta(serie):
    """Fase F: idea → biblia → casting → guion → prompts → tomas → montaje."""
    _rebaja(serie, episodio_corto=False)      # 61 s de verdad: es lo que exige TikTok
    informe = producir("canon-rojo", idea="Una jueza descubre que su hija miente.",
                       politica=_desatendida(), cliente=_cliente(corto=False))
    assert informe.parado_en is None, informe.como_dict()

    final = serie / "episodios" / "ep01" / "final.mp4"
    assert final.exists()
    tecnico = sonda.sondear(final)
    assert tecnico["vertical_9_16"] and (tecnico["ancho"], tecnico["alto"]) == (540, 960)
    assert tecnico["duracion"] == pytest.approx(61, abs=1.5)   # ≥ 61 s para TikTok
    assert final.with_suffix(".srt").exists()

    estados = ev.plegar(serie="canon-rojo")
    planos = {p for p in estados if p.startswith("s01_ep01_sh")}
    assert len(planos) == 3
    assert all(estados[p].estado == "aceptado" for p in planos)

    metricas = ev.metricas(serie="canon-rojo")
    assert metricas["planos_aceptados"] == 3
    assert metricas["pct_aceptadas_primer_intento"] == 100.0
    assert metricas["coste_por_segundo_aceptado"] == 0.0      # todo con el proveedor mock


def test_un_rerun_no_vuelve_a_pagar_lo_ya_generado(serie):
    """Idempotencia por huella: el content-addressing es lo que salva el dinero."""
    _rebaja(serie)
    producir("canon-rojo", idea="Una jueza y su hija.", politica=_desatendida(),
             cliente=_cliente())
    generaciones = len([e for e in ev.leer() if e["tipo"] == "generacion_solicitada"])

    # Se borran las tomas aprobadas del plegado para forzar el camino de generación,
    # pero la huella sigue en el log: no debe volver a generarse.
    segundo = Orquestador("canon-rojo", _desatendida(), cliente=ClienteFalso())
    lista = segundo.shotlist("s01_ep01")
    prompts = segundo._carpeta("s01_ep01") / "prompts"
    for plano in lista.planos:
        segundo.generar_plano(plano, (prompts / f"{plano.id}.md").read_text(encoding="utf-8"),
                              id_episodio="s01_ep01")
    assert segundo.informe.gastado == 0.0
    assert segundo.informe.reutilizado >= 0.0
    assert all("reutilizada" in p.detalle for p in segundo.informe.pasos)
    assert len([e for e in ev.leer() if e["tipo"] == "generacion_solicitada"]) == generaciones


def test_el_fusible_de_la_ejecucion_corta_antes_de_gastar(serie, monkeypatch):
    """Distinto del tope diario: limita lo que puede gastar ESTA ejecución."""
    monkeypatch.setenv("BUDGET_MAX_PER_DAY", "1000")
    politica = _desatendida(modelo_video="seedance-2.5@fal", max_gasto_usd=0.1)
    monkeypatch.setenv("FAL_KEY", "de-mentira")
    _rebaja(serie)
    informe = producir("canon-rojo", idea="Una jueza y su hija.", politica=politica,
                       cliente=_cliente(), montar=False)
    bloqueado = informe.parado_en
    assert bloqueado is not None and bloqueado.estado is Estado.BLOQUEADO
    assert "fusible" in bloqueado.detalle
    assert not [e for e in ev.leer() if e["tipo"] == "generacion_solicitada"
                and e["plano"].startswith("s01_ep01_sh")]


def test_el_prompt_guardado_se_rehace_si_deja_de_pasar_el_linter(serie):
    _rebaja(serie)
    producir("canon-rojo", idea="Una jueza y su hija.", politica=_desatendida(),
             cliente=_cliente(), montar=False)
    prompts = serie / "episodios" / "ep01" / "prompts"
    roto = prompts / "s01_ep01_sh002.md"
    roto.write_text("SCENE: nada.\n", encoding="utf-8")

    orq = Orquestador("canon-rojo", _desatendida(),
                      cliente=ClienteFalso([f.sobre(
                          f.salida_director(["@char_canon-rojo_Nadia_v1"], ranuras=[]))]))
    lista = orq.shotlist("s01_ep01")
    texto = orq._prompt(lista.plano("s01_ep01_sh002"), orq.registro,
                        (serie / "biblia.md").read_text(encoding="utf-8"),
                        (serie / "style.md").read_text(encoding="utf-8"), prompts)
    assert texto is not None and "STYLE PREFIX" in texto
    assert any("ya no pasa el linter" in p.detalle for p in orq.informe.pasos)
