"""Log de eventos: presupuesto atómico, plegado, migración y exportación."""
from __future__ import annotations

import json
import threading

import pytest

from showrunner.dominio import eventos as ev


def test_los_fallos_dejan_rastro():
    """Con el ledger antiguo los fallos no se registraban: los reintentos eran inmedibles."""
    s = ev.reservar(0.2, serie="x", plano="s01_ep01_sh001", intento=1)
    ev.cerrar(s, ok=False, coste_real=0.2, motivo="cara distinta")
    estado = ev.plegar()["s01_ep01_sh001"]
    assert estado.estado == "fallido" and estado.fallos == 1 and estado.coste == pytest.approx(0.2)


def test_gasto_cuenta_las_generaciones_en_vuelo():
    ev.reservar(0.5, serie="x", plano="s01_ep01_sh001")
    assert ev.gasto_hoy() == pytest.approx(0.5)


def test_coste_real_sustituye_a_la_estimacion():
    s = ev.reservar(0.5, serie="x", plano="s01_ep01_sh001")
    ev.cerrar(s, ok=True, coste_real=0.31, salida="a.mp4")
    assert ev.gasto_hoy() == pytest.approx(0.31)


def test_tope_por_tarea(monkeypatch):
    monkeypatch.setenv("BUDGET_MAX_PER_JOB", "1")
    with pytest.raises(ev.PresupuestoExcedido):
        ev.reservar(2.0, plano="s01_ep01_sh001")
    assert ev.leer() == []          # no escribe nada al rechazar


def test_tope_diario(monkeypatch):
    monkeypatch.setenv("BUDGET_MAX_PER_DAY", "1")
    ev.reservar(0.8, plano="s01_ep01_sh001")
    with pytest.raises(ev.PresupuestoExcedido):
        ev.reservar(0.5, plano="s01_ep01_sh002")


def test_dos_generaciones_a_la_vez_no_pasan_del_tope(monkeypatch):
    """Con el JSONL las dos leían el mismo gasto y ambas pasaban (TOCTOU)."""
    monkeypatch.setenv("BUDGET_MAX_PER_DAY", "1")
    resultados: list[str] = []
    barrera = threading.Barrier(2)

    def intenta(n: int) -> None:
        barrera.wait()
        try:
            ev.reservar(0.6, plano=f"s01_ep01_sh00{n}")
            resultados.append("ok")
        except ev.PresupuestoExcedido:
            resultados.append("bloqueado")

    hilos = [threading.Thread(target=intenta, args=(i,)) for i in (1, 2)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert sorted(resultados) == ["bloqueado", "ok"]
    assert ev.gasto_hoy() == pytest.approx(0.6)


def test_cortacircuitos_de_intentos(monkeypatch):
    """R-11: tras 20 intentos decide un humano, no el crédito."""
    monkeypatch.setenv("BUDGET_MAX_PER_DAY", "1000")
    for i in range(ev.MAX_INTENTOS):
        s = ev.reservar(0.01, plano="s01_ep01_sh001", intento=i + 1)
        ev.cerrar(s, ok=False, coste_real=0.01, motivo="x")
    with pytest.raises(ev.DemasiadosIntentos):
        ev.reservar(0.01, plano="s01_ep01_sh001", intento=21)
    assert ev.plegar()["s01_ep01_sh001"].agotado


def test_plegado_y_metricas(monkeypatch):
    monkeypatch.setenv("BUDGET_MAX_PER_DAY", "1000")
    # sh001: aceptado al segundo intento · sh002: aceptado al primero
    s = ev.reservar(0.2, serie="x", episodio="s01_ep01", plano="s01_ep01_sh001", intento=1)
    ev.cerrar(s, ok=False, coste_real=0.2, motivo="artefacto en la mano")
    s = ev.reservar(0.2, serie="x", episodio="s01_ep01", plano="s01_ep01_sh001", intento=2)
    ev.cerrar(s, ok=True, coste_real=0.2, salida="sh001_t2.mp4")
    ev.registrar("qc_veredicto", serie="x", episodio="s01_ep01", plano="s01_ep01_sh001",
                 intento=2, veredicto="aceptada", segundos=5)
    s = ev.reservar(0.3, serie="x", episodio="s01_ep01", plano="s01_ep01_sh002", intento=1)
    ev.cerrar(s, ok=True, coste_real=0.3, salida="sh002_t1.mp4")
    ev.registrar("qc_veredicto", serie="x", episodio="s01_ep01", plano="s01_ep01_sh002",
                 intento=1, veredicto="aceptada", segundos=5)

    estados = ev.plegar(serie="x")
    assert estados["s01_ep01_sh001"].estado == "aceptado"
    assert estados["s01_ep01_sh001"].intentos == 2
    assert estados["s01_ep01_sh001"].toma_aprobada == "sh001_t2.mp4"
    assert estados["s01_ep01_sh001"].coste == pytest.approx(0.4)

    m = ev.metricas(serie="x")
    assert m["planos_aceptados"] == 2
    assert m["intentos_por_plano_aceptado"] == pytest.approx(1.5)
    assert m["pct_aceptadas_primer_intento"] == pytest.approx(50.0)
    assert m["coste_por_segundo_aceptado"] == pytest.approx(0.7 / 10)


def test_rechazo_tipado_queda_registrado():
    ev.registrar("rechazo", serie="x", plano="s01_ep01_sh001",
                 destinatario="guionista", motivo_codigo="DIALOGO_NO_CABE",
                 detalle="18 palabras en 3 s")
    rechazos = ev.plegar()["s01_ep01_sh001"].rechazos
    assert rechazos[0]["motivo_codigo"] == "DIALOGO_NO_CABE"


def test_migracion_del_ledger_sin_perdida(tmp_path):
    """Verificación de la fase A: el ledger migrado se reproduce tal cual."""
    filas = [
        {"fecha": "2026-09-10T10:00:00", "plano": "s01_ep01_sh001", "modelo": "mock",
         "coste_usd": 0.0, "prompt": "x", "imagenes": [], "duracion": 5, "resolucion": "480p",
         "salida": "a.mp4", "task_id": "mock", "seed": None, "tecnico": {"fps": 24},
         "veredicto": "pendiente"},
        {"fecha": "2026-09-10T11:00:00", "plano": "s01_ep01_sh002", "modelo": "mock",
         "coste_usd": 0.12, "prompt": "y", "imagenes": ["https://x/a.png"], "duracion": 3,
         "resolucion": "720p", "salida": "b.mp4", "task_id": "t2", "seed": 7,
         "tecnico": {"fps": 24}, "veredicto": "aceptada"},
    ]
    origen = tmp_path / "ledger.jsonl"
    origen.write_text("\n".join(json.dumps(f) for f in filas) + "\nlínea corrupta\n",
                      encoding="utf-8")

    assert ev.migrar_jsonl(origen) == 2      # la línea corrupta no bloquea la migración
    destino = tmp_path / "reexportado.jsonl"
    assert ev.exportar_jsonl(destino, "ledger") == 2
    vueltas = [json.loads(linea) for linea in destino.read_text(encoding="utf-8").splitlines()]
    assert vueltas == filas


def test_exportacion_de_eventos_legible(tmp_path):
    ev.reservar(0.1, serie="x", plano="s01_ep01_sh001")
    destino = tmp_path / "eventos.jsonl"
    assert ev.exportar_jsonl(destino) == 1
    fila = json.loads(destino.read_text(encoding="utf-8").splitlines()[0])
    assert fila["tipo"] == "generacion_solicitada" and fila["serie"] == "x"
