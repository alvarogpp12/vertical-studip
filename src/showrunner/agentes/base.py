"""Un agente es una función tipada, no una sesión.

`(entrada, contexto) -> Resultado | Rechazo`. Ni harness ni estado de sesión: así
los agentes son independientes del modo de ejecución (interactivo hoy, desatendido
mañana) y las llamadas caras —vídeo e imagen— quedan fuera, en el orquestador.

Los `SKILL.md` que ya existen **son** el system prompt de cada agente. Una sola
fuente: siguen sirviendo para afinarlos a mano en Claude Code y el pipeline los
carga y los cachea.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel

from ..config import ROOT
from ..dominio import eventos as ev
from .cliente import ClienteAnthropic, ClienteLLM, Respuesta
from .contratos import Rechazo, Sobre

SKILLS = ROOT / ".claude" / "skills"
FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)

INSTRUCCIONES_SOBRE = """
# Formato de salida (obligatorio)
Devuelves un único objeto JSON con este contrato:

* Si puedes hacer el trabajo:  {"tipo": "resultado", "resultado": {...}, "rechazo": null}
* Si NO puedes hacerlo bien:   {"tipo": "rechazo", "resultado": null, "rechazo": {...}}

Rechaza —y devuelve el trabajo a quien corresponda— cuando el material que recibes
incumpla una regla del proyecto y arreglarlo no sea cosa tuya: una referencia que no
está en `registry.json`, un diálogo que no cabe en la duración, un plano que pide algo
que el modelo de vídeo hace mal. `motivo_codigo` va en MAYÚSCULAS_CON_GUIONES y
`detalle` es un hecho concreto en una o dos frases. Un rechazo con motivo es más útil
que un resultado inventado.

No añadas texto fuera del JSON.
""".strip()


def cargar_skill(nombre: str) -> str:
    """El `SKILL.md` sin su frontmatter YAML."""
    ruta = SKILLS / nombre / "SKILL.md"
    if not ruta.exists():
        raise FileNotFoundError(f"No existe la skill «{nombre}» en {SKILLS}")
    return FRONTMATTER.sub("", ruta.read_text(encoding="utf-8")).strip()


@dataclass
class Contexto:
    """Lo que sitúa la llamada en el proyecto, para el log y para la caché."""

    serie: str = ""
    episodio: str = ""
    plano: str = ""
    intento: int = 1
    #: Bloque grande e inmutable (biblia, estilo, registro). Se cachea entero.
    estable: list[str] = field(default_factory=list)


@dataclass
class Agente:
    """Base común: carga la skill, cachea el prefijo y registra cada llamada."""

    nombre: str
    skill: str
    modelo: str
    effort: str = "high"
    max_tokens: int = 16000
    cliente: ClienteLLM = field(default_factory=ClienteAnthropic)
    ultima_respuesta: Respuesta | None = None

    def sistema(self, contexto: Contexto) -> list[dict]:
        """Bloques de sistema, del más estable al más volátil.

        El único `cache_control` va al final: todo lo anterior entra en la caché y
        lo que cambia por llamada viaja en `messages`.
        """
        bloques = [cargar_skill(self.skill), INSTRUCCIONES_SOBRE, *contexto.estable]
        sistema = [{"type": "text", "text": b} for b in bloques if b.strip()]
        sistema[-1]["cache_control"] = {"type": "ephemeral", "ttl": "1h"}
        return sistema

    def preguntar(self, peticion: str | list[dict], formato: type[BaseModel],
                  contexto: Contexto | None = None) -> Sobre:
        """Una llamada. Devuelve siempre un `Sobre`: resultado o rechazo.

        `peticion` admite texto o una lista de bloques de contenido (el QC manda
        fotogramas).
        """
        contexto = contexto or Contexto()
        sobre_tipo = Sobre[formato]
        respuesta = self.cliente.pedir(
            modelo=self.modelo,
            sistema=self.sistema(contexto),
            mensajes=[{"role": "user", "content": peticion}],
            formato=sobre_tipo,
            effort=self.effort,
            max_tokens=self.max_tokens,
        )
        self.ultima_respuesta = respuesta
        self._registrar(respuesta, contexto)
        sobre: Sobre = respuesta.parsed  # type: ignore[assignment]
        if sobre.tipo == "rechazo" and sobre.rechazo is not None:
            ev.registrar("rechazo", serie=contexto.serie, episodio=contexto.episodio,
                         plano=contexto.plano, intento=contexto.intento,
                         emisor=self.nombre, destinatario=sobre.rechazo.destinatario,
                         motivo_codigo=sobre.rechazo.motivo_codigo,
                         detalle=sobre.rechazo.detalle, regla=sobre.rechazo.regla)
        return sobre

    def _registrar(self, respuesta: Respuesta, contexto: Contexto) -> None:
        ev.registrar("llm_llamada", serie=contexto.serie, episodio=contexto.episodio,
                     plano=contexto.plano, intento=contexto.intento,
                     coste_real=respuesta.uso.coste_usd,
                     agente=self.nombre, modelo=respuesta.modelo, effort=self.effort,
                     tokens_entrada=respuesta.uso.entrada, tokens_salida=respuesta.uso.salida,
                     cache_lectura=respuesta.uso.cache_lectura,
                     cache_escritura=respuesta.uso.cache_escritura)


def preguntar_validando(agente: Agente, peticion: str | list[dict], formato: type[BaseModel],
                        contexto: Contexto, validador, intentos: int = 2) -> Sobre:
    """Pregunta y pasa el resultado por un validador determinista.

    Si el validador encuentra errores, se reintenta **una sola vez** con las
    incidencias delante (corregir texto es barato; generar vídeo no). Si sigue mal,
    se devuelve un rechazo al humano con los códigos: es contable y no inventa nada.
    """
    incidencias = None
    for intento in range(1, intentos + 1):
        entrada = peticion
        if incidencias:
            aviso = ("\n\n# Corrige estas incidencias del validador\n"
                     "Cambia sólo lo necesario para resolverlas; no reescribas el resto.\n"
                     + incidencias)
            entrada = (peticion + aviso) if isinstance(peticion, str) else [
                *peticion, {"type": "text", "text": aviso}]
        sobre = agente.preguntar(entrada, formato, contexto)
        if not sobre.ok:
            return sobre
        informe = validador(sobre.resultado)
        if informe.ok:
            return sobre
        incidencias = informe.resumen()
        if intento == intentos:
            return rechazo(
                "humano",
                informe.errores[0].codigo,
                f"{agente.nombre} no supera el validador tras {intentos} intentos: "
                + ", ".join(i.codigo for i in informe.errores),
                informe.errores[0].regla,
            )
    raise AssertionError("inalcanzable")


def rechazo(destinatario: str, codigo: str, detalle: str, regla: str = "") -> Sobre:
    """Rechazo construido por código (no por el modelo): validadores, cortacircuitos."""
    return Sobre(tipo="rechazo", resultado=None,
                 rechazo=Rechazo(destinatario=destinatario, motivo_codigo=codigo,
                                 detalle=detalle, regla=regla))


def bloque(titulo: str, cuerpo: str) -> str:
    """Un trozo de contexto con cabecera, para que el modelo sepa qué está leyendo."""
    return f"# {titulo}\n{cuerpo.strip()}"


def leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8") if ruta.exists() else ""
