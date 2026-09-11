"""Incidencias contables: cada fallo lleva regla y código, nunca texto libre.

Un motivo con código se puede contar; una frase no. De aquí salen los
`motivo_codigo` de los rechazos entre agentes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Gravedad = Literal["error", "aviso"]


@dataclass(frozen=True)
class Incidencia:
    codigo: str
    mensaje: str
    regla: str = ""
    gravedad: Gravedad = "error"
    detalle: str = ""

    def __str__(self) -> str:
        marca = "✗" if self.gravedad == "error" else "!"
        regla = f"{self.regla} · " if self.regla else ""
        return f"{marca} [{self.codigo}] {regla}{self.mensaje}"


@dataclass
class Resultado:
    incidencias: list[Incidencia] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.ok

    @property
    def ok(self) -> bool:
        """Sólo los errores bloquean; los avisos se informan y se sigue."""
        return not self.errores

    @property
    def errores(self) -> list[Incidencia]:
        return [i for i in self.incidencias if i.gravedad == "error"]

    @property
    def avisos(self) -> list[Incidencia]:
        return [i for i in self.incidencias if i.gravedad == "aviso"]

    @property
    def codigos(self) -> list[str]:
        return [i.codigo for i in self.incidencias]

    def error(self, codigo: str, mensaje: str, regla: str = "", detalle: str = "") -> Resultado:
        self.incidencias.append(Incidencia(codigo, mensaje, regla, "error", detalle))
        return self

    def aviso(self, codigo: str, mensaje: str, regla: str = "", detalle: str = "") -> Resultado:
        self.incidencias.append(Incidencia(codigo, mensaje, regla, "aviso", detalle))
        return self

    def unir(self, otro: Resultado) -> Resultado:
        self.incidencias.extend(otro.incidencias)
        return self

    def resumen(self) -> str:
        if not self.incidencias:
            return "✓ sin incidencias"
        return "\n".join(str(i) for i in self.incidencias)

    def como_dict(self) -> dict:
        return {
            "ok": self.ok,
            "incidencias": [
                {"codigo": i.codigo, "regla": i.regla, "gravedad": i.gravedad,
                 "mensaje": i.mensaje, "detalle": i.detalle}
                for i in self.incidencias
            ],
        }
