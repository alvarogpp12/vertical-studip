"""Prueba de humo: la primera llamada real, barata, que descubre lo que los mocks no.

Todo lo demás del proyecto está verificado con dobles de prueba. Eso demuestra que la
fontanería encaja, **no** que la API acepte nuestros esquemas ni que la caché funcione.
Tres cosas concretas sólo se saben gastando dinero, y se saben por unos céntimos:

1. **¿La API acepta el esquema?** Los contratos generan JSON Schema con `$defs`,
   `anyOf` y uniones discriminadas. Si algo de eso no pasa, todo el diseño de salidas
   estructuradas se cae. Se comprueba pidiendo el esquema más grande del proyecto
   —el del showrunner— pero exigiendo un **rechazo** como respuesta: valida la unión
   entera con unos cientos de tokens de salida en vez de una biblia completa.
2. **¿La caché lee?** Un invalidador silencioso no da error: sólo multiplica la
   factura por diez. La única señal es `cache_read_input_tokens` en la segunda llamada.
3. **¿El coste estimado se parece al real?** Si no, todas las estimaciones del
   proyecto mienten.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .agentes.base import Agente, Contexto
from .agentes.cliente import ClienteLLM, Respuesta
from .agentes.contratos import SalidaShowrunner
from .dominio import eventos as ev
from .providers import PeticionVideo, estimar_coste, obtener_proveedor
from .qc import sonda
from .valida import valida_toma

#: Petición deliberadamente imposible: fuerza un rechazo, que es corto y barato.
PETICION = (
    "Idea de partida: (vacía, no hay ninguna).\n\n"
    "No hay idea que desarrollar. Devuelve un rechazo con destinatario `humano` y "
    "motivo_codigo `IDEA_SIN_MOTOR`. No escribas una biblia."
)


@dataclass
class Paso:
    nombre: str
    ok: bool
    detalle: str = ""

    def __str__(self) -> str:
        return f"{'✓' if self.ok else '✗'} {self.nombre} — {self.detalle}"


@dataclass
class Humo:
    pasos: list[Paso] = field(default_factory=list)
    coste_usd: float = 0.0

    def anota(self, nombre: str, ok: bool, detalle: str = "") -> Paso:
        paso = Paso(nombre, ok, detalle)
        self.pasos.append(paso)
        return paso

    @property
    def ok(self) -> bool:
        return all(p.ok for p in self.pasos)


def prueba_llm(cliente: ClienteLLM | None = None, modelo: str = "claude-sonnet-5",
               serie: str = "") -> Humo:
    """Dos llamadas con el mismo prefijo. Cuesta unos céntimos."""
    humo = Humo()
    kwargs = {"cliente": cliente} if cliente is not None else {}
    agente = Agente(nombre="humo", skill="showrunner", modelo=modelo, effort="low",
                    max_tokens=2000, **kwargs)
    contexto = Contexto(serie=serie)

    primera: Respuesta | None = None
    for vuelta in (1, 2):
        try:
            sobre = agente.preguntar(f"{PETICION}\n\n(comprobación {vuelta} de 2)",
                                     SalidaShowrunner, contexto)
        except Exception as e:
            humo.anota(f"llamada {vuelta}", False, f"{type(e).__name__}: {e}")
            return humo
        respuesta = agente.ultima_respuesta
        humo.coste_usd += respuesta.uso.coste_usd
        if vuelta == 1:
            primera = respuesta
            humo.anota("la API acepta el esquema del proyecto", True,
                       f"unión discriminada validada · respuesta «{sobre.tipo}»")
            humo.anota("el rechazo tipado llega bien formado", sobre.tipo == "rechazo",
                       f"motivo_codigo={sobre.rechazo.motivo_codigo if sobre.rechazo else '—'}")
        else:
            lee = respuesta.uso.cache_lectura
            humo.anota("la caché de prompt lee", lee > 0,
                       f"cache_read_input_tokens={lee} "
                       f"(escritos en la 1.ª: {primera.uso.cache_escritura})"
                       + ("" if lee else " · hay un invalidador silencioso en el prefijo"))
    humo.anota("coste medido", True, f"{humo.coste_usd:.4f} $ en 2 llamadas a {modelo}")
    return humo


def prueba_video(destino: Path, *, modelo: str = "", nivel: str = "borrador",
                 duracion: int = 3, serie: str = "") -> Humo:
    """Un plano de verdad, al nivel más barato. Del orden de 0,04–0,15 $."""
    from .providers import elegir_modelo

    humo = Humo()
    peticion = PeticionVideo(
        prompt="Static shot of an empty grey studio wall under a single soft key light. "
               "No music — diegetic room tone only. Any person in frame = failed take.",
        duracion=duracion, resolucion="480p")
    try:
        modelo = modelo or elegir_modelo(nivel, peticion)
    except LookupError as e:
        humo.anota("hay un modelo de vídeo configurado", False, str(e))
        return humo
    coste = estimar_coste(modelo, peticion)
    humo.anota("coste estimado", True, f"{coste:.3f} $ con {modelo}")

    solicitud = ev.reservar(coste, serie=serie, plano="humo", intento=1, modelo=modelo,
                            prueba_de_humo=True)
    try:
        resultado = obtener_proveedor(modelo).generar(peticion, destino)
    except Exception as e:
        ev.cerrar(solicitud, ok=False, coste_real=0.0, motivo=str(e)[:400])
        humo.anota(f"el conector {modelo} responde", False, f"{type(e).__name__}: {e}")
        return humo
    tecnico = sonda.sondear(resultado.ruta_local)
    ev.cerrar(solicitud, ok=True, coste_real=coste, salida=str(destino), tecnico=tecnico)
    humo.coste_usd += coste
    humo.anota(f"el conector {modelo} responde", True, str(destino))

    informe = valida_toma(tecnico, duracion_pedida=duracion)
    humo.anota("el vídeo sale 9:16 a 24 fps y con la duración pedida", informe.ok,
               tecnico and f"{tecnico['ancho']}x{tecnico['alto']} · {tecnico['fps']} fps · "
                           f"{tecnico['duracion']:.2f} s"
                           + ("" if informe.ok
                              else " · " + ", ".join(i.codigo for i in informe.errores)))
    return humo
