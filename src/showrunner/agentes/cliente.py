"""Cliente de la API de Claude para los agentes.

Tres decisiones, todas por la misma razón —que los agentes sean funciones tipadas
y no sesiones—:

* **Salidas estructuradas nativas** (`output_config.format` con JSON Schema): el
  esquema es el contrato, no una instrucción en prosa que el modelo puede ignorar.
* **Caché de prompt explícita**: biblia, hojas y estilo son un bloque grande e
  inmutable que se reutiliza en cada plano. Se comprueba que la caché funciona
  (`cache_read_input_tokens`), porque un invalidador silencioso no da error.
* **Un protocolo, dos implementaciones**: la real y una falsa. Los tests y las
  evaluaciones corren sin clave y sin gastar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from ..config import cargar_modelos_llm, env

M = TypeVar("M", bound=BaseModel)

#: Multiplicadores de la caché sobre el precio de entrada.
COSTE_LECTURA_CACHE = 0.1
COSTE_ESCRITURA_CACHE = 1.25

EFECTOS = ("low", "medium", "high", "xhigh", "max")


class LLMNoDisponible(RuntimeError):
    """No hay forma de hablar con el modelo (falta el paquete o la credencial)."""


class RespuestaIlegible(RuntimeError):
    """El modelo devolvió algo que no encaja en el esquema pedido."""


@dataclass
class Uso:
    entrada: int = 0
    salida: int = 0
    cache_lectura: int = 0
    cache_escritura: int = 0
    coste_usd: float = 0.0

    @property
    def cache_funciona(self) -> bool:
        """Si esto es False en llamadas repetidas, hay un invalidador silencioso."""
        return self.cache_lectura > 0


@dataclass
class Respuesta:
    parsed: BaseModel
    modelo: str
    uso: Uso = field(default_factory=Uso)
    stop_reason: str | None = None
    bruto: dict = field(default_factory=dict)


def esquema_estricto(modelo: type[BaseModel]) -> dict[str, Any]:
    """JSON Schema del modelo, apretado para salidas estructuradas.

    Pydantic marca como opcionales los campos con valor por defecto; las salidas
    estructuradas piden que todas las propiedades estén en `required` y que ningún
    objeto admita propiedades extra. Se recorre el esquema y se fuerza.
    """
    esquema = modelo.model_json_schema()

    def apretar(nodo: Any) -> None:
        if isinstance(nodo, list):
            for hijo in nodo:
                apretar(hijo)
            return
        if not isinstance(nodo, dict):
            return
        if nodo.get("type") == "object" and isinstance(nodo.get("properties"), dict):
            nodo["additionalProperties"] = False
            nodo["required"] = list(nodo["properties"])
        for clave in ("properties", "$defs", "definitions"):
            if isinstance(nodo.get(clave), dict):
                for hijo in nodo[clave].values():
                    apretar(hijo)
        for clave in ("items", "anyOf", "oneOf", "allOf", "prefixItems"):
            if clave in nodo:
                apretar(nodo[clave])

    apretar(esquema)
    return esquema


def coste(modelo: str, uso: Uso) -> float:
    spec = cargar_modelos_llm().get(modelo)
    if not spec:
        return 0.0
    entrada = float(spec["precio_entrada_mtok"]) / 1_000_000
    salida = float(spec["precio_salida_mtok"]) / 1_000_000
    return round(
        uso.entrada * entrada
        + uso.cache_lectura * entrada * COSTE_LECTURA_CACHE
        + uso.cache_escritura * entrada * COSTE_ESCRITURA_CACHE
        + uso.salida * salida,
        6,
    )


class ClienteLLM(Protocol):
    def pedir(self, *, modelo: str, sistema: list[dict], mensajes: list[dict],
              formato: type[M], effort: str = "high",
              max_tokens: int = 16000) -> Respuesta: ...

    def comprobar(self) -> tuple[bool, str]: ...


class ClienteAnthropic:
    """Implementación real. No se instancia el SDK hasta la primera llamada."""

    def __init__(self, timeout: float = 1200.0):
        self.timeout = timeout
        self._cliente = None

    def comprobar(self) -> tuple[bool, str]:
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False, "Falta el paquete anthropic (`uv sync`)"
        if not env("ANTHROPIC_API_KEY"):
            return False, "Falta ANTHROPIC_API_KEY en .env"
        return True, "ANTHROPIC_API_KEY presente"

    def _sdk(self):
        if self._cliente is None:
            ok, detalle = self.comprobar()
            if not ok:
                raise LLMNoDisponible(detalle)
            import anthropic

            self._cliente = anthropic.Anthropic(timeout=self.timeout)
        return self._cliente

    def pedir(self, *, modelo: str, sistema: list[dict], mensajes: list[dict],
              formato: type[M], effort: str = "high", max_tokens: int = 16000) -> Respuesta:
        import json

        if effort not in EFECTOS:
            raise ValueError(f"effort desconocido: {effort}. Válidos: {EFECTOS}")
        respuesta = self._sdk().messages.create(
            model=modelo,
            max_tokens=max_tokens,
            system=sistema,
            messages=mensajes,
            thinking={"type": "adaptive"},
            output_config={
                "effort": effort,
                "format": {"type": "json_schema", "schema": esquema_estricto(formato)},
            },
        )
        if respuesta.stop_reason == "refusal":
            detalle = getattr(respuesta.stop_details, "explanation", "")
            raise RespuestaIlegible(f"el modelo declinó la petición: {detalle}")
        texto = next((b.text for b in respuesta.content if b.type == "text"), "")
        if not texto:
            raise RespuestaIlegible(f"respuesta sin texto (stop_reason={respuesta.stop_reason})")
        try:
            parsed = formato.model_validate(json.loads(texto))
        except Exception as e:
            raise RespuestaIlegible(f"no encaja en {formato.__name__}: {e}") from e

        u = respuesta.usage
        uso = Uso(
            entrada=getattr(u, "input_tokens", 0) or 0,
            salida=getattr(u, "output_tokens", 0) or 0,
            cache_lectura=getattr(u, "cache_read_input_tokens", 0) or 0,
            cache_escritura=getattr(u, "cache_creation_input_tokens", 0) or 0,
        )
        uso.coste_usd = coste(modelo, uso)
        return Respuesta(parsed=parsed, modelo=modelo, uso=uso,
                         stop_reason=respuesta.stop_reason)


class ClienteFalso:
    """Doble de pruebas: devuelve respuestas preparadas y guarda lo que se le pidió."""

    def __init__(self, respuestas: list[BaseModel] | None = None):
        self.respuestas = list(respuestas or [])
        self.llamadas: list[dict] = []

    def comprobar(self) -> tuple[bool, str]:
        return True, "cliente falso (sin coste)"

    def encolar(self, *respuestas: BaseModel) -> ClienteFalso:
        self.respuestas.extend(respuestas)
        return self

    def pedir(self, *, modelo: str, sistema: list[dict], mensajes: list[dict],
              formato: type[M], effort: str = "high", max_tokens: int = 16000) -> Respuesta:
        self.llamadas.append({"modelo": modelo, "sistema": sistema, "mensajes": mensajes,
                              "formato": formato.__name__, "effort": effort})
        if not self.respuestas:
            raise RespuestaIlegible("ClienteFalso sin respuestas encoladas")
        siguiente = self.respuestas.pop(0)
        if not isinstance(siguiente, formato):
            raise RespuestaIlegible(
                f"se esperaba {formato.__name__} y la cola trae {type(siguiente).__name__}"
            )
        return Respuesta(parsed=siguiente, modelo=modelo,
                         uso=Uso(entrada=100, salida=200, cache_lectura=1000))
