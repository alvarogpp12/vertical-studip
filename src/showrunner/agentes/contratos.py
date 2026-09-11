"""Lo que cada agente recibe y devuelve, como esquema.

Todo lo que sale de un agente es una **unión discriminada**: o un resultado o un
rechazo. El rechazo lleva destinatario y `motivo_codigo` sacado de las reglas
R-01…R-12 y de los códigos del linter, nunca texto libre: así los rechazos se
cuentan y se pueden convertir en métricas.
"""
from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

Destinatario = Literal["showrunner", "guionista", "director", "qc", "humano"]
Nivel = Literal["borrador", "trabajo", "clave"]


class Rechazo(BaseModel):
    """Trabajo devuelto arriba. El canal de rechazo forma parte del contrato."""

    model_config = ConfigDict(extra="forbid")

    destinatario: Destinatario
    motivo_codigo: str = Field(
        description="Código en MAYÚSCULAS_CON_GUIONES, p. ej. DIALOGO_NO_CABE o TAG_NO_REGISTRADO"
    )
    detalle: str = Field(description="Una o dos frases con el hecho concreto, sin opinión")
    regla: str = Field("", description="Regla incumplida, p. ej. R-09; vacío si no aplica")


T = TypeVar("T", bound=BaseModel)


class Sobre(BaseModel, Generic[T]):
    """Unión discriminada. Exactamente uno de `resultado` o `rechazo`."""

    model_config = ConfigDict(extra="forbid")

    tipo: Literal["resultado", "rechazo"]
    resultado: T | None = None
    rechazo: Rechazo | None = None

    @property
    def ok(self) -> bool:
        return self.tipo == "resultado" and self.resultado is not None


# ----------------------------------------------------------- agente showrunner
class Concepto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str
    logline: str = Field(description="Una frase: quién quiere qué y qué se lo impide")
    mundo: str
    motor_de_temporada: str = Field(description="Por qué da para 20 episodios y no para uno")
    personajes: int = Field(ge=1, le=6, description="Nº de personajes principales")
    localizaciones: int = Field(ge=1, le=6)
    producibilidad: int = Field(ge=1, le=10, description="Facilidad de producir con IA")
    motivo_producibilidad: str
    riesgo_principal: str


class PerfilActuacion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mascara_publica: str
    que_la_rompe: str
    habitos_fisicos: str = Field(description="Hábito físico y su detonante")
    forma_de_caminar: str


class Personaje(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(description="Nombre propio, sin espacios ni acentos: va dentro del @tag")
    descriptor_congelado: str = Field(
        description="En inglés. Se pega palabra por palabra en cada prompt (R-02). "
                    "Edad, pelo, rostro, vestuario. Sin emociones ni encuadre."
    )
    anclas_identidad: list[str] = Field(description="Cicatriz, accesorio, peinado: 2 o 3")
    voz_lock: str = Field(description="AUDIO LOCK: timbre, tempo, forma de hablar, acento")
    perfil: PerfilActuacion
    objetivo_temporada: str


class Localizacion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(description="Nombre propio sin espacios ni acentos: va dentro del @tag")
    descriptor_congelado: str = Field(
        description="En inglés. Geometría, materiales y luz. Nunca el encuadre (R-04)."
    )
    mapa_vertical: str = Field(
        description="Posiciones ancladas a objetos visibles y eje de cámara (R-06)"
    )
    estados: list[str] = Field(description="Día, noche, u otros estados del espacio")


class Prop(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str
    descriptor_congelado: str
    estados: list[str]


class FormulaEpisodio(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gancho: str = Field(description="Qué pasa en los primeros 3 s")
    giro: str
    cliffhanger: str


class Paleta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dominante: str = Field(description="Hex, p. ej. #101010")
    secundaria: str
    acento_reservado: str
    significado_del_acento: str = Field(description="Qué significa narrativamente ese color")


class Estilo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    style_prefix: str = Field(
        description="En inglés, una sola línea. Look, 9:16, luz, paleta con hex, grano, óptica, "
                    "gramática de cámara. Inmutable durante la serie (R-03)."
    )
    constraints: str = Field(
        description="En inglés. Bloque inmutable. Debe incluir literalmente «No music»."
    )
    paleta: Paleta


class EpisodioPlaneado(BaseModel):
    model_config = ConfigDict(extra="forbid")

    numero: int = Field(ge=1, le=99)
    titulo: str
    gancho: str
    giro: str
    cliffhanger: str


class StressTest(BaseModel):
    """Prueba de estrés de un episodio: objetivo · obstáculo · táctica · giro · valor."""

    model_config = ConfigDict(extra="forbid")

    episodio: int
    objetivo: str
    obstaculo: str
    tactica: str
    giro: str
    cambio_de_valor: str
    punto_mas_debil: str


class Biblia(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str
    logline: str
    genero_y_tono: str
    publico_y_plataforma: str
    promesa_del_formato: str = Field(description="Por qué alguien ve el episodio 2")
    producibilidad: int = Field(ge=1, le=10)
    motivo_producibilidad: str
    formula: FormulaEpisodio
    epoca_y_lugar: str
    reglas_del_mundo: list[str]
    regla_visual_narrativa: str
    personajes: list[Personaje] = Field(max_length=3)
    localizaciones: list[Localizacion] = Field(max_length=3)
    props: list[Prop] = Field(default_factory=list)
    riesgos_de_produccion: list[str] = Field(
        description="Planos que el modelo hará mal y cómo esquivarlos (R-10)"
    )


class SalidaShowrunner(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conceptos: list[Concepto] = Field(min_length=3, max_length=3)
    concepto_elegido: int = Field(ge=1, le=3, description="1, 2 o 3")
    motivo_eleccion: str
    biblia: Biblia
    estilo: Estilo
    temporada: list[EpisodioPlaneado] = Field(min_length=1)
    stress_test: list[StressTest] = Field(min_length=1)


# ------------------------------------------------------------ agente guionista
class Beat(BaseModel):
    model_config = ConfigDict(extra="forbid")

    numero: int
    funcion: Literal["gancho", "desarrollo", "giro", "cliffhanger"]
    texto: str = Field(description="Qué ocurre, en prosa seca de guion")


class PlanoPropuesto(BaseModel):
    """Un plano del shotlist. El agente NO inventa el id: lo asigna el código."""

    model_config = ConfigDict(extra="forbid")

    orden: int = Field(ge=1)
    beat: int = Field(ge=1)
    duracion: int = Field(ge=1, le=30, description="Segundos que se GENERAN (mínimo 4 "
                                                    "en Seedance)")
    duracion_montaje: int | None = Field(
        None, ge=1, le=30,
        description="Segundos que se usan en el montaje si son menos que los generados. "
                    "El máster de geografía se genera a 4 s y se monta a 1 s.")
    tamano: str = Field(description="Primer plano, plano medio… (vertical: nada de planos corales)")
    camara: str = Field(description="UN solo movimiento: tilt, push-in, pull-back o fijo")
    refs: list[str] = Field(description="@tags del registro que salen en el plano")
    dialogo: str = Field(
        "", description="Sólo la línea hablada. ~4 palabras/s + 1 s de cola (R-09)")
    es_master: bool = Field(False, description="Máster de 1 s que fija la geografía (R-06)")
    nivel: Nivel = "borrador"
    notas: str = ""


class SalidaGuionista(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str
    beats: list[Beat] = Field(min_length=3)
    planos: list[PlanoPropuesto] = Field(min_length=2)
    duracion_total: int = Field(description="Suma de las duraciones, en segundos")
    gancho_3s: str = Field(description="Qué ve el espectador en los primeros 3 s")
    cliffhanger: str


# -------------------------------------------------------------- agente director
class SalidaDirector(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(
        description="El prompt completo, con los bloques fijos copiados palabra por palabra"
    )
    referencias_activas: list[str] = Field(description="@tags que el prompt cita")
    riesgos_detectados: list[str] = Field(
        default_factory=list,
        description="Comprobaciones de fallo que se han convertido en bloqueos positivos",
    )


# -------------------------------------------------------------------- agente QC
Dimension = Literal[
    "identidad", "vestuario", "props", "geografia", "artefactos", "zona_segura", "interpretacion"
]


class HallazgoQC(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: Dimension
    descripcion: str
    fotograma: int = Field(description="Índice del fotograma donde se ve, empezando en 0")


class SalidaQC(BaseModel):
    model_config = ConfigDict(extra="forbid")

    veredicto: Literal["aceptada", "empalmable", "rechazada"]
    motivo_codigo: str = Field(
        description="ACEPTADA si pasa; si no, la dimensión en mayúsculas, "
                    "p. ej. IDENTIDAD_DISTINTA"
    )
    motivo: str = Field(description="Una frase")
    hallazgos: list[HallazgoQC] = Field(default_factory=list)
    segundos_utiles: float = Field(
        0.0, description="Si es empalmable, cuántos segundos del principio sirven"
    )
    confianza: float = Field(ge=0.0, le=1.0,
                             description="0–1. Los artefactos finos se detectan mal")
    requiere_humano: bool = Field(
        False, description="True si hay duda razonable: mejor una mirada humana que quemar crédito"
    )
