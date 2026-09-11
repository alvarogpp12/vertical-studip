"""Log append-only de eventos en SQLite. Sustituye a `runs/ledger.jsonl`.

Por qué SQLite y no JSONL:

1. **Presupuesto sin TOCTOU.** Con el JSONL, dos generaciones en paralelo leían el
   mismo gasto y ambas pasaban el tope diario. Aquí la comprobación y la reserva
   ocurren dentro de una misma transacción `BEGIN IMMEDIATE`.
2. **Una línea corrupta no rompe `doctor`.**
3. **El plegado con índices es instantáneo.**

El estado de un plano no se guarda: se pliega desde aquí (`plegar`). Las métricas
que importan —intentos por plano aceptado, coste por segundo aceptado, % al primer
intento— salen del mismo plegado.

Los fallos, que antes no dejaban rastro, ahora se registran: sin ellos la palanca
de coste más grande del proyecto (los reintentos) es inmedible.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Literal

from ..config import ROOT, env, presupuesto

TipoEvento = Literal[
    "generacion_solicitada",
    "generacion_ok",
    "generacion_fallo",
    "qc_veredicto",
    "rechazo",
    "aprobacion_humana",
]
TERMINALES = ("generacion_ok", "generacion_fallo")

#: R-11: tras 20 intentos fallidos no se sigue quemando crédito; se escala al humano.
MAX_INTENTOS = 20

ESQUEMA = """
CREATE TABLE IF NOT EXISTS eventos (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  ts              TEXT    NOT NULL,
  serie           TEXT    NOT NULL DEFAULT '',
  episodio        TEXT    NOT NULL DEFAULT '',
  plano           TEXT    NOT NULL DEFAULT '',
  intento         INTEGER NOT NULL DEFAULT 0,
  tipo            TEXT    NOT NULL,
  ref             INTEGER,
  coste_estimado  REAL    NOT NULL DEFAULT 0.0,
  coste_real      REAL,
  payload_json    TEXT    NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_eventos_ts    ON eventos(ts);
CREATE INDEX IF NOT EXISTS idx_eventos_serie ON eventos(serie, episodio, plano);
CREATE INDEX IF NOT EXISTS idx_eventos_tipo  ON eventos(tipo);
CREATE INDEX IF NOT EXISTS idx_eventos_ref   ON eventos(ref);
"""


class PresupuestoExcedido(RuntimeError):
    """La generación se detiene antes de gastar."""


class DemasiadosIntentos(RuntimeError):
    """R-11: el plano ha agotado los intentos; decide un humano."""


def ruta_bd() -> Path:
    """`runs/eventos.sqlite`, o lo que diga `SHOWRUNNER_EVENTOS` (útil en tests)."""
    return Path(env("SHOWRUNNER_EVENTOS") or ROOT / "runs" / "eventos.sqlite")


def _ahora() -> str:
    """ISO local sin zona: el tope de gasto es «por día natural» del usuario."""
    return time.strftime("%Y-%m-%dT%H:%M:%S")


ESPERA_MS = 30_000
_INICIADAS: set[str] = set()
_CERROJO = threading.Lock()


def _iniciar(con: sqlite3.Connection) -> None:
    # WAL toma un bloqueo exclusivo momentáneo y no respeta busy_timeout: si otro
    # proceso está escribiendo, se queda en el modo que ya tenga la base.
    try:
        con.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        pass
    con.executescript(ESQUEMA)


@contextmanager
def conexion(ruta: Path | None = None) -> Iterator[sqlite3.Connection]:
    ruta = Path(ruta) if ruta else ruta_bd()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ruta, timeout=ESPERA_MS / 1000, isolation_level=None)
    con.row_factory = sqlite3.Row
    try:
        con.execute(f"PRAGMA busy_timeout={ESPERA_MS}")
        clave = str(ruta.resolve())
        if clave not in _INICIADAS:
            with _CERROJO:
                _iniciar(con)
                _INICIADAS.add(clave)
        yield con
    finally:
        con.close()


def _insertar(con: sqlite3.Connection, tipo: TipoEvento, *, serie: str = "", episodio: str = "",
              plano: str = "", intento: int = 0, ref: int | None = None,
              coste_estimado: float = 0.0, coste_real: float | None = None,
              ts: str | None = None, payload: dict | None = None) -> int:
    cur = con.execute(
        "INSERT INTO eventos (ts, serie, episodio, plano, intento, tipo, ref, "
        "coste_estimado, coste_real, payload_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (ts or _ahora(), serie, episodio, plano, intento, tipo, ref,
         float(coste_estimado), coste_real,
         json.dumps(payload or {}, ensure_ascii=False)),
    )
    return int(cur.lastrowid)


def registrar(tipo: TipoEvento, /, *, serie: str = "", episodio: str = "", plano: str = "",
              intento: int = 0, ref: int | None = None, coste_estimado: float = 0.0,
              coste_real: float | None = None, ts: str | None = None,
              bd: Path | None = None, **payload) -> int:
    """Añade un evento y devuelve su id.

    `tipo` es posicional a propósito: así un payload puede llevar su propia clave
    `tipo` (p. ej. el tipo de aprobación humana) sin chocar con el del evento.
    """
    with conexion(bd) as con:
        return _insertar(con, tipo, serie=serie, episodio=episodio, plano=plano, intento=intento,
                         ref=ref, coste_estimado=coste_estimado, coste_real=coste_real, ts=ts,
                         payload=payload)


# ---------------------------------------------------------------- consultas
def _fila_a_dict(fila: sqlite3.Row) -> dict[str, Any]:
    d = dict(fila)
    d["payload"] = json.loads(d.pop("payload_json"))
    return d


def leer(serie: str = "", episodio: str = "", plano: str = "", tipo: str = "",
         bd: Path | None = None) -> list[dict[str, Any]]:
    where, args = [], []
    campos = (("serie", serie), ("episodio", episodio), ("plano", plano), ("tipo", tipo))
    for campo, valor in campos:
        if valor:
            where.append(f"{campo} = ?")
            args.append(valor)
    sql = "SELECT * FROM eventos"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id"
    with conexion(bd) as con:
        return [_fila_a_dict(f) for f in con.execute(sql, args)]


def _gasto_desde(con: sqlite3.Connection, desde: str, serie: str = "") -> float:
    filtro_serie = " AND serie = ?" if serie else ""
    args_serie = [serie] if serie else []
    confirmado = con.execute(
        f"SELECT COALESCE(SUM(coste_real), 0) FROM eventos "
        f"WHERE tipo IN {TERMINALES} AND coste_real IS NOT NULL AND ts >= ?{filtro_serie}",
        [desde, *args_serie],
    ).fetchone()[0]
    # Generaciones en vuelo: cuentan por su estimación hasta que se cierran.
    en_vuelo = con.execute(
        f"SELECT COALESCE(SUM(s.coste_estimado), 0) FROM eventos s "
        f"WHERE s.tipo = 'generacion_solicitada' AND s.ts >= ?{filtro_serie} "
        f"AND NOT EXISTS (SELECT 1 FROM eventos t WHERE t.ref = s.id AND t.tipo IN {TERMINALES})",
        [desde, *args_serie],
    ).fetchone()[0]
    return round(float(confirmado) + float(en_vuelo), 4)


def gasto_hoy(serie: str = "", bd: Path | None = None) -> float:
    with conexion(bd) as con:
        return _gasto_desde(con, date.today().isoformat(), serie)


def gasto_total(serie: str = "", bd: Path | None = None) -> float:
    with conexion(bd) as con:
        return _gasto_desde(con, "", serie)


# ------------------------------------------------------- reserva de gasto
def reservar(coste_estimado: float, *, serie: str = "", episodio: str = "", plano: str = "",
             intento: int = 1, bd: Path | None = None, **payload) -> int:
    """Comprueba los topes y reserva el gasto **en la misma transacción**.

    Devuelve el id del evento `generacion_solicitada`, que hay que pasar luego a
    `cerrar` para registrar el coste real. Lanza `PresupuestoExcedido` o
    `DemasiadosIntentos` sin haber escrito nada.
    """
    max_job, max_dia = presupuesto()
    if coste_estimado > max_job:
        raise PresupuestoExcedido(
            f"Coste estimado {coste_estimado:.2f} $ supera el límite por tarea ({max_job} $)."
        )
    with conexion(bd) as con:
        con.execute("BEGIN IMMEDIATE")
        try:
            if plano:
                previos = con.execute(
                    "SELECT COUNT(*) FROM eventos WHERE plano = ? "
                    "AND tipo = 'generacion_solicitada'",
                    (plano,),
                ).fetchone()[0]
                if previos >= MAX_INTENTOS:
                    raise DemasiadosIntentos(
                        f"{plano} lleva {previos} intentos (máximo {MAX_INTENTOS}, R-11). "
                        "Cambia el plano o pide criterio humano."
                    )
            gastado = _gasto_desde(con, date.today().isoformat(), serie="")
            if gastado + coste_estimado > max_dia:
                raise PresupuestoExcedido(
                    f"Se superaría el límite diario ({max_dia} $). "
                    f"Gastado hoy: {gastado:.2f} $, esta tarea: {coste_estimado:.2f} $."
                )
            evento = _insertar(con, "generacion_solicitada", serie=serie, episodio=episodio,
                               plano=plano, intento=intento, coste_estimado=coste_estimado,
                               payload=payload)
            con.execute("COMMIT")
            return evento
        except BaseException:
            con.execute("ROLLBACK")
            raise


def cerrar(solicitud_id: int, *, ok: bool, coste_real: float | None = None,
           bd: Path | None = None, **payload) -> int:
    """Cierra una generación reservada: `generacion_ok` o `generacion_fallo`."""
    with conexion(bd) as con:
        fila = con.execute("SELECT * FROM eventos WHERE id = ?", (solicitud_id,)).fetchone()
        if fila is None:
            raise KeyError(f"no existe la solicitud {solicitud_id}")
        return _insertar(
            con, "generacion_ok" if ok else "generacion_fallo",
            serie=fila["serie"], episodio=fila["episodio"], plano=fila["plano"],
            intento=fila["intento"], ref=solicitud_id,
            coste_real=fila["coste_estimado"] if coste_real is None else float(coste_real),
            payload=payload,
        )


def comprobar_presupuesto(coste_estimado: float, bd: Path | None = None) -> None:
    """Comprobación sin reserva (para `estimar` y avisos previos)."""
    max_job, max_dia = presupuesto()
    if coste_estimado > max_job:
        raise PresupuestoExcedido(
            f"Coste estimado {coste_estimado:.2f} $ supera el límite por tarea ({max_job} $)."
        )
    gastado = gasto_hoy(bd=bd)
    if gastado + coste_estimado > max_dia:
        raise PresupuestoExcedido(
            f"Se superaría el límite diario ({max_dia} $). Gastado hoy: {gastado:.2f} $."
        )


# ------------------------------------------------------------- plegado
EstadoNombre = Literal[
    "pendiente", "generando", "fallido", "qc_pendiente", "rechazado", "empalmable", "aceptado"
]


@dataclass
class EstadoPlano:
    """Estado derivado de un plano. No se guarda en ningún sitio: se pliega."""

    plano: str
    serie: str = ""
    episodio: str = ""
    estado: EstadoNombre = "pendiente"
    intentos: int = 0
    fallos: int = 0
    coste: float = 0.0
    toma: str | None = None
    toma_aprobada: str | None = None
    aceptado_en_intento: int | None = None
    segundos_aceptados: float = 0.0
    motivo_rechazo: str | None = None
    rechazos: list[dict] = field(default_factory=list)

    @property
    def agotado(self) -> bool:
        return self.intentos >= MAX_INTENTOS and self.estado != "aceptado"


def plegar(serie: str = "", episodio: str = "", plano: str = "",
           bd: Path | None = None) -> dict[str, EstadoPlano]:
    """Pliega el log en el estado actual de cada plano."""
    estados: dict[str, EstadoPlano] = {}
    pendientes: dict[str, dict[int, float]] = {}
    for ev in leer(serie=serie, episodio=episodio, plano=plano, bd=bd):
        pid = ev["plano"]
        if not pid:
            continue
        est = estados.setdefault(
            pid, EstadoPlano(plano=pid, serie=ev["serie"], episodio=ev["episodio"])
        )
        pend = pendientes.setdefault(pid, {})
        p, tipo = ev["payload"], ev["tipo"]
        if tipo == "generacion_solicitada":
            est.estado = "generando"
            est.intentos = max(est.intentos, ev["intento"] or est.intentos + 1)
            pend[ev["id"]] = float(ev["coste_estimado"])
        elif tipo == "generacion_ok":
            est.estado = "qc_pendiente"
            est.toma = p.get("salida") or est.toma
            pend.pop(ev["ref"], None)
            est.coste += float(ev["coste_real"] or 0.0)
        elif tipo == "generacion_fallo":
            est.estado = "fallido"
            est.fallos += 1
            pend.pop(ev["ref"], None)
            est.coste += float(ev["coste_real"] or 0.0)
        elif tipo == "qc_veredicto":
            veredicto = p.get("veredicto", "rechazada")
            if veredicto == "aceptada":
                est.estado = "aceptado"
                est.toma_aprobada = p.get("toma") or est.toma
                est.aceptado_en_intento = ev["intento"] or est.intentos
                est.segundos_aceptados = float(p.get("segundos", 0.0))
                est.motivo_rechazo = None
            elif veredicto == "empalmable":
                est.estado = "empalmable"
                est.toma_aprobada = p.get("toma") or est.toma
                est.segundos_aceptados = float(p.get("segundos_utiles", 0.0))
            else:
                est.estado = "rechazado"
                est.motivo_rechazo = p.get("motivo", "")
        elif tipo == "rechazo":
            est.rechazos.append(p)
    for pid, est in estados.items():
        est.coste = round(est.coste + sum(pendientes.get(pid, {}).values()), 4)
    return estados


def intentos(plano: str, bd: Path | None = None) -> int:
    estado = plegar(plano=plano, bd=bd).get(plano)
    return estado.intentos if estado else 0


def metricas(serie: str = "", episodio: str = "", bd: Path | None = None) -> dict[str, Any]:
    """Las métricas que `CLAUDE.md` declara importantes, sin instrumentación extra."""
    estados = list(plegar(serie=serie, episodio=episodio, bd=bd).values())
    aceptados = [e for e in estados if e.estado in ("aceptado", "empalmable")]
    intentos_aceptados = sum(e.intentos for e in aceptados)
    segundos = sum(e.segundos_aceptados for e in aceptados)
    coste = sum(e.coste for e in estados)
    primeros = [e for e in aceptados if (e.aceptado_en_intento or e.intentos) == 1]
    return {
        "planos": len(estados),
        "planos_aceptados": len(aceptados),
        "planos_agotados": sum(1 for e in estados if e.agotado),
        "intentos_totales": sum(e.intentos for e in estados),
        "coste_usd": round(coste, 4),
        "intentos_por_plano_aceptado": (
            round(intentos_aceptados / len(aceptados), 2) if aceptados else None),
        "coste_por_segundo_aceptado": round(coste / segundos, 4) if segundos else None,
        "pct_aceptadas_primer_intento": (
            round(100 * len(primeros) / len(aceptados), 1) if aceptados else None),
        "segundos_aceptados": round(segundos, 2),
    }


# ------------------------------------------------- migración y exportación
CAMPOS_LEDGER = ("plano", "modelo", "coste_usd", "prompt", "imagenes", "duracion",
                 "resolucion", "salida", "task_id", "seed", "tecnico", "veredicto")


def migrar_jsonl(origen: Path, bd: Path | None = None) -> int:
    """Importa un `ledger.jsonl` antiguo. Cada línea = solicitud + cierre correcto.

    El ledger sólo registraba éxitos, así que toda línea migrada se cierra como
    `generacion_ok` con coste real igual al estimado. Las líneas ilegibles se
    saltan: una línea corrupta no puede bloquear la migración.
    """
    origen = Path(origen)
    if not origen.exists():
        return 0
    migrados = 0
    with conexion(bd) as con:
        con.execute("BEGIN IMMEDIATE")
        try:
            for linea in origen.read_text(encoding="utf-8").splitlines():
                if not linea.strip():
                    continue
                try:
                    row = json.loads(linea)
                except json.JSONDecodeError:
                    continue
                ts = row.get("fecha") or _ahora()
                coste = float(row.get("coste_usd", 0) or 0)
                plano = row.get("plano") or ""
                solicitud = _insertar(
                    con, "generacion_solicitada", plano=plano, intento=1, ts=ts,
                    coste_estimado=coste,
                    payload={k: row.get(k) for k in ("modelo", "prompt", "imagenes", "duracion",
                                                     "resolucion")},
                )
                _insertar(
                    con, "generacion_ok", plano=plano, intento=1, ts=ts, ref=solicitud,
                    coste_real=coste,
                    payload={k: row.get(k) for k in ("salida", "task_id", "seed", "tecnico")},
                )
                if row.get("veredicto") and row["veredicto"] != "pendiente":
                    _insertar(con, "qc_veredicto", plano=plano, intento=1, ts=ts,
                              payload={"veredicto": row["veredicto"], "toma": row.get("salida")})
                migrados += 1
            con.execute("COMMIT")
        except BaseException:
            con.execute("ROLLBACK")
            raise
    return migrados


def exportar_jsonl(destino: Path, formato: Literal["eventos", "ledger"] = "eventos",
                   bd: Path | None = None) -> int:
    """Vuelca el log a JSONL legible.

    `formato="ledger"` reconstruye las filas del antiguo `ledger.jsonl` (una por
    generación cerrada), de modo que un ledger migrado se reproduce sin pérdida.
    """
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    todos = leer(bd=bd)
    filas: list[dict[str, Any]] = []
    if formato == "eventos":
        filas = todos
    else:
        por_id = {e["id"]: e for e in todos}
        veredictos: dict[str, str] = {}
        for ev in todos:
            if ev["tipo"] == "qc_veredicto":
                veredictos[ev["plano"]] = ev["payload"].get("veredicto", "pendiente")
        for ev in todos:
            if ev["tipo"] != "generacion_ok":
                continue
            sol = por_id.get(ev["ref"], {"payload": {}})
            datos = {**sol["payload"], **ev["payload"]}
            filas.append({
                "fecha": sol.get("ts", ev["ts"]),
                **{k: datos.get(k) for k in CAMPOS_LEDGER
                   if k not in ("plano", "coste_usd", "veredicto")},
                "plano": ev["plano"],
                "coste_usd": ev["coste_real"],
                "veredicto": veredictos.get(ev["plano"], "pendiente"),
            })
    with destino.open("w", encoding="utf-8") as f:
        for fila in filas:
            f.write(json.dumps(fila, ensure_ascii=False, default=str) + "\n")
    return len(filas)
