"""Máquina de estados de la producción. Código, no LLM: no juzga contenido.

Tres cosas que hace y que ningún agente debería hacer:

* **Idempotencia por content-addressing.** Antes de cada llamada cara se calcula
  `sha256(modelo + parámetros + referencias)`. Si esa huella ya se generó con
  éxito, se reutiliza el archivo. Un rerun no vuelve a pagar 30 $ de vídeo.
* **Fusible de gasto.** `max_gasto_usd` por ejecución, además del tope diario.
* **Gates humanos como estado.** Biblia, casting y visto bueno final son estados
  con rastro auditable —quién, cuándo, sobre qué versión—, no una conversación.

Cada fase es una ejecución independiente: el orquestador avanza hasta el siguiente
gate y para. Eso es también lo que exige la limitación de «no hay entrada de
usuario a mitad de ejecución» de cualquier harness de agente.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from . import casting as casting_mod
from . import montaje as montaje_mod
from . import proyecto as proy
from .agentes import director as ag_director
from .agentes import escritura
from .agentes import guionista as ag_guionista
from .agentes import showrunner as ag_showrunner
from .agentes.cliente import LLMNoDisponible
from .config import ROOT
from .dominio import eventos as ev
from .dominio import registro as reg
from .dominio import serie as ser
from .dominio import shotlist as sl
from .dominio.identidad import IdPlano
from .providers import PeticionVideo, elegir_modelo, estimar_coste, obtener_proveedor
from .qc import sonda
from .valida import valida_prompt, valida_toma
from .valida.resultado import Resultado


class Estado(StrEnum):
    PENDIENTE = "pendiente"
    HECHO = "hecho"
    ESPERA_HUMANO = "espera_humano"
    BLOQUEADO = "bloqueado"


@dataclass
class Paso:
    nombre: str
    estado: Estado
    detalle: str = ""
    accion: str = ""

    def __str__(self) -> str:
        marca = {Estado.HECHO: "✓", Estado.PENDIENTE: "·",
                 Estado.ESPERA_HUMANO: "🔒", Estado.BLOQUEADO: "✗"}[self.estado]
        extra = f" — {self.detalle}" if self.detalle else ""
        return f"{marca} {self.nombre}{extra}"


@dataclass
class Politica:
    """Quién decide y hasta dónde se puede gastar.

    El modo desatendido no finge una firma humana: registra que la aprobación fue
    automática **bajo la política de una persona con nombre**. Si nadie se hace
    responsable, no hay modo desatendido.
    """

    responsable: str = ""
    auto_aprobar: set[str] = field(default_factory=set)
    max_gasto_usd: float = 10.0
    nivel: str = "borrador"
    resolucion: str = "480p"
    #: Modelos concretos; vacío = el más barato del nivel que esté configurado.
    modelo_video: str = ""
    modelo_imagen: str = ""
    subir_referencias: bool = True

    @classmethod
    def interactiva(cls, **kwargs) -> Politica:
        return cls(**kwargs)

    @classmethod
    def desatendida(cls, responsable: str, **kwargs) -> Politica:
        if not responsable:
            raise ValueError("el modo desatendido necesita un responsable con nombre")
        return cls(responsable=responsable,
                   auto_aprobar={"biblia", "casting", "episodio"}, **kwargs)

    def aprueba_sola(self, gate: str) -> bool:
        return gate in self.auto_aprobar


def _sin_cerebro(paso: str, e: LLMNoDisponible) -> Paso:
    """Falta la credencial del LLM: es un bloqueo con remedio, no una traza."""
    return Paso(paso, Estado.BLOQUEADO, detalle=str(e),
                accion="rellena ANTHROPIC_API_KEY en .env (`showrunner doctor` lo comprueba)")


def _relativa(ruta: Path) -> str:
    """Ruta legible. Una serie puede vivir fuera del repo: no se asume lo contrario."""
    try:
        return str(ruta.relative_to(ROOT))
    except ValueError:
        return str(ruta)


class GastoAgotado(RuntimeError):
    """El fusible de la ejecución, distinto del tope diario."""


@dataclass
class Informe:
    pasos: list[Paso] = field(default_factory=list)
    gastado: float = 0.0
    reutilizado: float = 0.0

    def anota(self, paso: Paso) -> Paso:
        self.pasos.append(paso)
        return paso

    @property
    def parado_en(self) -> Paso | None:
        for paso in self.pasos:
            if paso.estado in (Estado.ESPERA_HUMANO, Estado.BLOQUEADO):
                return paso
        return None

    def como_dict(self) -> dict[str, Any]:
        return {
            "pasos": [{"nombre": p.nombre, "estado": p.estado.value, "detalle": p.detalle,
                       "accion": p.accion} for p in self.pasos],
            "gastado_usd": round(self.gastado, 4),
            "reutilizado_usd": round(self.reutilizado, 4),
            "parado_en": self.parado_en.nombre if self.parado_en else None,
        }


class Orquestador:
    def __init__(self, slug: str, politica: Politica | None = None, cliente=None):
        self.base = proy.ruta(slug)
        self.slug = slug
        self.politica = politica or Politica()
        #: Cliente LLM inyectable: los tests y las evaluaciones corren sin red.
        self.cliente = cliente
        self.informe = Informe()

    # ------------------------------------------------------------ lectura
    @property
    def proyecto(self) -> ser.Proyecto:
        return ser.cargar(self.base / "proyecto.json")

    @property
    def registro(self) -> reg.Registro:
        return reg.cargar(self.base / "registry.json")

    def shotlist(self, id_episodio: str) -> sl.Shotlist:
        return sl.cargar(self._carpeta(id_episodio) / "shotlist.json")

    def _carpeta(self, id_episodio: str) -> Path:
        return self.base / "episodios" / IdPlano.parse(f"{id_episodio}_sh001").carpeta_episodio

    def estados(self, id_episodio: str = "") -> dict[str, ev.EstadoPlano]:
        return ev.plegar(serie=self.slug, episodio=id_episodio)

    def diagnostico(self, id_episodio: str = "s01_ep01") -> list[Paso]:
        """Dónde está la serie ahora mismo, sin ejecutar nada ni gastar."""
        proyecto = self.proyecto
        pasos = [
            Paso("biblia", Estado.HECHO if (self.base / "biblia.json").exists()
                 else Estado.PENDIENTE, accion=f"showrunner biblia \"{proyecto.titulo}\""),
            Paso("aprobación de la biblia",
                 Estado.HECHO if proyecto.aprobado("biblia") else Estado.ESPERA_HUMANO,
                 accion=f"showrunner aprobar {self.slug} biblia --por tu-nombre"),
        ]
        registro = self.registro
        sin_refs = [a.id for a in registro.assets() if not a.urls]
        pasos.append(Paso("casting", Estado.HECHO if registro.tags and not sin_refs
                          else Estado.PENDIENTE,
                          detalle=f"sin referencias: {sin_refs}" if sin_refs else "",
                          accion=f"showrunner casting personaje {self.slug} …"))
        pasos.append(Paso("aprobación del casting",
                          Estado.HECHO if proyecto.aprobado("casting") else Estado.ESPERA_HUMANO,
                          accion=f"showrunner aprobar {self.slug} casting --por tu-nombre"))

        hay_shotlist = (self._carpeta(id_episodio) / "shotlist.json").exists()
        pasos.append(Paso(f"guion {id_episodio}",
                          Estado.HECHO if hay_shotlist else Estado.PENDIENTE,
                          accion=f"showrunner guion {self.slug} --episodio {id_episodio}"))
        if hay_shotlist:
            lista = self.shotlist(id_episodio)
            estados = self.estados(id_episodio)
            aceptados = [p.id for p in lista.planos
                         if estados.get(p.id) and estados[p.id].estado in
                         ("aceptado", "empalmable")]
            pasos.append(Paso("tomas aprobadas",
                              Estado.HECHO if len(aceptados) == len(lista.planos)
                              else Estado.PENDIENTE,
                              detalle=f"{len(aceptados)}/{len(lista.planos)}"))
        pasos.append(Paso("visto bueno final",
                          Estado.HECHO if proyecto.aprobado("episodio", id_episodio)
                          else Estado.ESPERA_HUMANO,
                          accion=f"showrunner aprobar {self.slug} episodio "
                                 f"--referencia {id_episodio} --por tu-nombre"))
        return pasos

    # -------------------------------------------------------------- gates
    def _gate(self, tipo: str, referencia: str = "") -> Paso:
        proyecto = self.proyecto
        nombre = f"gate: {tipo}" + (f" {referencia}" if referencia else "")
        if proyecto.aprobado(tipo, referencia):
            return self.informe.anota(Paso(nombre, Estado.HECHO))
        if not self.politica.aprueba_sola(tipo):
            return self.informe.anota(Paso(
                nombre, Estado.ESPERA_HUMANO,
                detalle="hace falta una firma humana",
                accion=f"showrunner aprobar {self.slug} {tipo}"
                       + (f" --referencia {referencia}" if referencia else "")
                       + " --por tu-nombre"))
        proyecto.aprobar(tipo, por=f"auto:{self.politica.responsable}", referencia=referencia,
                         notas="aprobación automática bajo política desatendida")
        ser.guardar(proyecto, self.base / "proyecto.json")
        ev.registrar("aprobacion_humana", serie=self.slug, episodio=referencia, tipo=tipo,
                     por=f"auto:{self.politica.responsable}", automatica=True)
        return self.informe.anota(Paso(nombre, Estado.HECHO,
                                       detalle=f"automática · política de "
                                               f"{self.politica.responsable}"))

    # ---------------------------------------------------------- ejecución
    def _presupuesto_restante(self) -> float:
        return self.politica.max_gasto_usd - self.informe.gastado

    def generar_plano(self, plano: sl.Plano, prompt: str, *, id_episodio: str) -> Paso:
        """Una toma, con huella de contenido, fusible y registro. Idempotente."""
        registro = self.registro
        refs = registro.urls(*[t for t in plano.refs if registro.existe(t)])
        peticion = PeticionVideo(prompt=prompt, duracion=plano.duracion,
                                 resolucion=self.politica.resolucion, imagenes=refs)
        modelo = self.politica.modelo_video or elegir_modelo(self.politica.nivel, peticion)
        coste = estimar_coste(modelo, peticion)
        # La huella identifica «la generación de ESTE plano»: lleva serie y plano
        # dentro. Dos planos con el mismo prompt no comparten toma —el episodio
        # tendría un clip repetido— y un rerun del mismo plano sí la reutiliza.
        # El `intento` queda fuera a propósito: si el proceso murió entre la
        # generación y el veredicto, el rerun recupera el archivo en vez de pagarlo.
        params = {"serie": self.slug, "plano": plano.id, "duracion": plano.duracion,
                  "resolucion": self.politica.resolucion, "prompt": prompt, "seed": plano.seed}
        firma = ev.huella(modelo, params, refs)

        estado = self.estados(id_episodio).get(plano.id)
        # Un reintento tras un rechazo sí vuelve a rodar: es una tirada nueva, no un rerun.
        reintentando = estado is not None and estado.estado in ("rechazado", "fallido")
        previa = ev.generacion_previa(firma)
        if previa and not reintentando and Path(previa["payload"].get("salida", "")).exists():
            self.informe.reutilizado += coste
            return self.informe.anota(Paso(
                f"{plano.id}: generación", Estado.HECHO,
                detalle=f"reutilizada (misma huella, {coste:.3f} $ no gastados)"))

        if coste > self._presupuesto_restante():
            return self.informe.anota(Paso(
                f"{plano.id}: generación", Estado.BLOQUEADO,
                detalle=f"el fusible de la ejecución no llega: quedan "
                        f"{self._presupuesto_restante():.2f} $ y hacen falta {coste:.2f} $"))

        intento = (estado.intentos if estado else 0) + 1
        salida = self._carpeta(id_episodio) / "tomas" / f"{plano.id}_t{intento}.mp4"
        try:
            solicitud = ev.reservar(coste, serie=self.slug, episodio=id_episodio, plano=plano.id,
                                    intento=intento, huella=firma, modelo=modelo,
                                    nivel=self.politica.nivel, salida=str(salida))
        except (ev.PresupuestoExcedido, ev.DemasiadosIntentos) as e:
            return self.informe.anota(Paso(f"{plano.id}: generación", Estado.BLOQUEADO,
                                           detalle=str(e)))
        try:
            resultado = obtener_proveedor(modelo).generar(peticion, salida)
        except Exception as e:
            ev.cerrar(solicitud, ok=False, coste_real=0.0, motivo=str(e)[:400])
            return self.informe.anota(Paso(f"{plano.id}: generación", Estado.BLOQUEADO,
                                           detalle=f"{type(e).__name__}: {e}"))
        tecnico = sonda.sondear(resultado.ruta_local)
        ev.cerrar(solicitud, ok=True, coste_real=coste, salida=str(salida), tecnico=tecnico,
                  task_id=resultado.task_id, seed=resultado.seed)
        self.informe.gastado += coste

        informe_tecnico = valida_toma(tecnico, duracion_pedida=plano.duracion)
        self._veredicto(plano, salida, intento, informe_tecnico, id_episodio, tecnico)
        return self.informe.anota(Paso(
            f"{plano.id}: generación", Estado.HECHO if informe_tecnico.ok else Estado.PENDIENTE,
            detalle=f"{coste:.3f} $ · intento {intento} · "
                    + ("QC técnico OK" if informe_tecnico.ok
                       else ", ".join(i.codigo for i in informe_tecnico.errores))))

    def _veredicto(self, plano: sl.Plano, salida: Path, intento: int, tecnico: Resultado,
                   id_episodio: str, datos: dict) -> None:
        ev.registrar("qc_veredicto", serie=self.slug, episodio=id_episodio, plano=plano.id,
                     intento=intento,
                     veredicto="aceptada" if tecnico.ok else "rechazada",
                     motivo="; ".join(i.codigo for i in tecnico.errores),
                     segundos=float(datos.get("duracion_video") or plano.duracion),
                     toma=str(salida))

    # ------------------------------------------------------------- fases
    def fase_desarrollo(self, idea: str = "") -> Informe:
        if not (self.base / "biblia.json").exists():
            if not idea:
                self.informe.anota(Paso("biblia", Estado.BLOQUEADO,
                                        detalle="no hay biblia.json y no se ha dado una idea"))
                return self.informe
            try:
                sobre = ag_showrunner.crear_biblia(idea, self.proyecto.titulo,
                                                   plataforma=self.proyecto.plataforma,
                                                   proyecto=self.proyecto, cliente=self.cliente)
            except LLMNoDisponible as e:
                self.informe.anota(_sin_cerebro("biblia", e))
                return self.informe
            if not sobre.ok:
                self.informe.anota(Paso("biblia", Estado.BLOQUEADO,
                                        detalle=f"[{sobre.rechazo.motivo_codigo}] "
                                                f"{sobre.rechazo.detalle}"))
                return self.informe
            escritura.guardar_biblia(self.base, sobre.resultado)
            self.informe.anota(Paso("biblia", Estado.HECHO, detalle="escrita por el showrunner"))
        else:
            self.informe.anota(Paso("biblia", Estado.HECHO, detalle="ya existía"))
        self._gate("biblia")
        return self.informe

    def fase_preproduccion(self) -> Informe:
        if not self.proyecto.aprobado("biblia"):
            self.informe.anota(Paso("casting", Estado.ESPERA_HUMANO,
                                    detalle="la biblia no está aprobada"))
            return self.informe
        registro = self.registro
        modelo_imagen = self.politica.modelo_imagen
        subir = self.politica.subir_referencias
        for asset in list(registro.assets()):
            if asset.urls:
                self.informe.anota(Paso(f"casting {asset.id}", Estado.HECHO,
                                        detalle="ya tiene referencias"))
                continue
            tag = asset.tag
            try:
                if tag.tipo == "char":
                    casting_mod.crear_personaje(self.base, tag.nombre, asset.descriptor,
                                                voz_lock=asset.voz_lock, modelo=modelo_imagen,
                                                version=tag.version, subir=subir)
                elif tag.tipo == "loc":
                    casting_mod.crear_localizacion(self.base, tag.nombre, asset.descriptor,
                                                   mapa=asset.mapa, modelo=modelo_imagen,
                                                   version=tag.version, subir=subir)
                else:
                    self.informe.anota(Paso(f"casting {asset.id}", Estado.PENDIENTE,
                                            detalle="los props se generan a mano por ahora"))
                    continue
            except Exception as e:
                self.informe.anota(Paso(f"casting {asset.id}", Estado.BLOQUEADO,
                                        detalle=f"{type(e).__name__}: {e}"))
                return self.informe
            self.informe.anota(Paso(f"casting {asset.id}", Estado.HECHO))
        self._gate("casting")
        return self.informe

    def fase_produccion(self, id_episodio: str = "s01_ep01", *, sinopsis: str = "",
                        montar: bool = True) -> Informe:
        proyecto = self.proyecto
        if not proyecto.aprobado("casting"):
            self.informe.anota(Paso("producción", Estado.ESPERA_HUMANO,
                                    detalle="el casting no está aprobado"))
            return self.informe

        carpeta = self._carpeta(id_episodio)
        if not (carpeta / "shotlist.json").exists():
            try:
                sobre = ag_guionista.escribir_episodio(
                    (self.base / "biblia.md").read_text(encoding="utf-8"),
                    (self.base / "style.md").read_text(encoding="utf-8"),
                    self.registro, id_episodio=id_episodio, proyecto=proyecto,
                    sinopsis=sinopsis, base=self.base, cliente=self.cliente)
            except LLMNoDisponible as e:
                self.informe.anota(_sin_cerebro(f"guion {id_episodio}", e))
                return self.informe
            if not sobre.ok:
                self.informe.anota(Paso(f"guion {id_episodio}", Estado.BLOQUEADO,
                                        detalle=f"[{sobre.rechazo.motivo_codigo}] "
                                                f"{sobre.rechazo.detalle}"))
                return self.informe
            escritura.guardar_episodio(self.base, sobre.resultado, id_episodio)
            self.informe.anota(Paso(f"guion {id_episodio}", Estado.HECHO))
        else:
            self.informe.anota(Paso(f"guion {id_episodio}", Estado.HECHO, detalle="ya existía"))

        lista = self.shotlist(id_episodio)
        registro = self.registro
        estilo = (self.base / "style.md").read_text(encoding="utf-8")
        biblia_md = (self.base / "biblia.md").read_text(encoding="utf-8")
        prompts = carpeta / "prompts"
        prompts.mkdir(parents=True, exist_ok=True)

        for plano in lista.en_orden:
            estado = self.estados(id_episodio).get(plano.id)
            if estado and estado.estado in ("aceptado", "empalmable"):
                self.informe.anota(Paso(f"{plano.id}", Estado.HECHO, detalle="toma ya aprobada"))
                continue
            prompt = self._prompt(plano, registro, biblia_md, estilo, prompts)
            if prompt is None:
                return self.informe
            paso = self.generar_plano(plano, prompt, id_episodio=id_episodio)
            if paso.estado is Estado.BLOQUEADO:
                return self.informe

        if montar:
            self._montar(lista, id_episodio, proyecto)
        self._gate("episodio", id_episodio)
        return self.informe

    def _prompt(self, plano: sl.Plano, registro: reg.Registro, biblia_md: str, estilo: str,
                carpeta: Path) -> str | None:
        archivo = carpeta / f"{plano.id}.md"
        if archivo.exists():
            texto = archivo.read_text(encoding="utf-8")
            informe = valida_prompt(texto, style_md=estilo, registro=registro, plano=plano)
            if informe.ok:
                return texto
            self.informe.anota(Paso(f"{plano.id}: prompt", Estado.PENDIENTE,
                                    detalle="el prompt guardado ya no pasa el linter; se rehace"))
        try:
            sobre = ag_director.escribir_prompt(plano, registro, biblia_md=biblia_md,
                                                estilo_md=estilo, serie=self.slug,
                                                cliente=self.cliente)
        except LLMNoDisponible as e:
            self.informe.anota(_sin_cerebro(f"{plano.id}: prompt", e))
            return None
        if not sobre.ok:
            self.informe.anota(Paso(f"{plano.id}: prompt", Estado.BLOQUEADO,
                                    detalle=f"[{sobre.rechazo.motivo_codigo}] "
                                            f"{sobre.rechazo.detalle}"))
            return None
        archivo.write_text(sobre.resultado.prompt, encoding="utf-8")
        self.informe.anota(Paso(f"{plano.id}: prompt", Estado.HECHO))
        return sobre.resultado.prompt

    def _montar(self, lista: sl.Shotlist, id_episodio: str, proyecto: ser.Proyecto) -> Paso:
        destino = self._carpeta(id_episodio) / "final.mp4"
        try:
            escritos = montaje_mod.montar(lista, self.estados(id_episodio), destino,
                                          proyecto=proyecto)
        except montaje_mod.SinTomas as e:
            return self.informe.anota(Paso("montaje", Estado.PENDIENTE, detalle=str(e)))
        tecnico = sonda.sondear(escritos["final"])
        from .valida import valida_episodio

        informe = valida_episodio(tecnico, proyecto=proyecto, etiqueta_ia=True)
        return self.informe.anota(Paso(
            "montaje", Estado.HECHO if informe.ok else Estado.PENDIENTE,
            detalle=f"{_relativa(escritos['final'])} · {tecnico['duracion']:.1f} s"
                    + ("" if informe.ok else " · " + ", ".join(i.codigo
                                                               for i in informe.errores))))


def producir(slug: str, *, idea: str = "", id_episodio: str = "s01_ep01",
             politica: Politica | None = None, cliente=None, montar: bool = True) -> Informe:
    """Avanza la serie hasta el siguiente gate y para."""
    orq = Orquestador(slug, politica, cliente=cliente)
    orq.fase_desarrollo(idea)
    if orq.informe.parado_en:
        return orq.informe
    orq.fase_preproduccion()
    if orq.informe.parado_en:
        return orq.informe
    orq.fase_produccion(id_episodio, montar=montar)
    return orq.informe
