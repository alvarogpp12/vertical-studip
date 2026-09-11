"""La prueba de humo, con el cliente falso: se comprueba el arnés, no la API."""
from __future__ import annotations

import factorias as f

from showrunner.agentes.cliente import ClienteFalso
from showrunner.dominio import eventos as ev
from showrunner.humo import prueba_llm, prueba_video


def _rechazo():
    from showrunner.agentes.contratos import SalidaShowrunner, Sobre

    return Sobre[SalidaShowrunner](
        tipo="rechazo", resultado=None,
        rechazo={"destinatario": "humano", "motivo_codigo": "IDEA_SIN_MOTOR",
                 "detalle": "no hay idea", "regla": ""})


def test_el_humo_pide_un_rechazo_para_no_pagar_una_biblia():
    cliente = ClienteFalso([_rechazo(), _rechazo()])
    informe = prueba_llm(cliente=cliente)
    assert informe.ok, [str(p) for p in informe.pasos]
    assert len(cliente.llamadas) == 2
    assert "Devuelve un rechazo" in cliente.llamadas[0]["mensajes"][0]["content"]
    assert cliente.llamadas[0]["effort"] == "low"


def test_el_humo_avisa_si_la_cache_no_lee():
    """Un invalidador silencioso no da error: esta es la única señal."""
    cliente = ClienteFalso([_rechazo(), _rechazo()])
    cliente_sin_cache = cliente

    class SinCache(ClienteFalso):
        def pedir(self, **kwargs):
            respuesta = super().pedir(**kwargs)
            respuesta.uso.cache_lectura = 0
            return respuesta

    informe = prueba_llm(cliente=SinCache([_rechazo(), _rechazo()]))
    assert not informe.ok
    assert any("invalidador silencioso" in p.detalle for p in informe.pasos)
    assert cliente_sin_cache.respuestas          # el otro cliente ni se usó


def test_el_humo_del_video_registra_el_gasto(tmp_path, monkeypatch):
    monkeypatch.setenv("BUDGET_MAX_PER_DAY", "10")
    informe = prueba_video(tmp_path / "humo.mp4", modelo="mock", duracion=2)
    assert informe.ok, [str(p) for p in informe.pasos]
    assert (tmp_path / "humo.mp4").exists()
    tipos = [e["tipo"] for e in ev.leer()]
    assert "generacion_solicitada" in tipos and "generacion_ok" in tipos


def test_el_humo_del_video_registra_tambien_el_fallo(tmp_path, monkeypatch):
    monkeypatch.setenv("BUDGET_MAX_PER_DAY", "10")
    from showrunner import humo as modulo

    class Roto:
        def generar(self, *a, **k):
            raise RuntimeError("401 no autorizado")

    monkeypatch.setattr(modulo, "obtener_proveedor", lambda _: Roto())
    informe = prueba_video(tmp_path / "humo.mp4", modelo="mock", duracion=2)
    assert not informe.ok
    fallos = [e for e in ev.leer() if e["tipo"] == "generacion_fallo"]
    assert fallos and "401" in fallos[0]["payload"]["motivo"]


def test_las_factorias_siguen_valiendo():
    assert f.salida_showrunner().biblia.titulo
