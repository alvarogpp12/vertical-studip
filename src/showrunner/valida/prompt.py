"""Linter de prompts. Corre **antes** de gastar: es gratis y bloquea la llamada.

Aquí aterrizan las reglas que la skill `director-vertical` no podía imponer porque
nadie las comprobaba: R-01 (nada sin registro), R-02 (palabra por palabra e islas),
R-03 (bloques fijos), R-07 (tareas, no emociones), R-08 (límites como toma fallida)
y R-09 ("No music").

También es el antídoto del fallo conocido del LLM: «se cree director» y añade
detalles o cambia el encuadre. Si el prompt no cita el descriptor congelado, no sale.
"""
from __future__ import annotations

import re
import unicodedata

from ..config import cargar_denylist
from ..dominio import referencias as refs
from ..dominio.identidad import RE_TAG, tags_en_texto
from ..dominio.registro import Registro
from ..dominio.shotlist import Plano
from .resultado import Resultado

CABECERA_STYLE = re.compile(r"^#+\s*STYLE\s+PREFIX.*$", re.IGNORECASE | re.MULTILINE)
CABECERA_CONSTRAINTS = re.compile(r"^#+\s*CONSTRAINTS.*$", re.IGNORECASE | re.MULTILINE)
CABECERA_CUALQUIERA = re.compile(r"^#+\s+\w.*$", re.MULTILINE)

#: R-08 · prohibiciones sueltas. La única excepción es «No music» (R-09).
PROHIBICIONES = re.compile(
    r"^\s*(?:no|avoid|never|don't|do not|without|sin)\b(?!\s+music\b)", re.IGNORECASE
)
MARCA_FALLIDA = re.compile(r"=\s*(?:failed take|toma fallida)", re.IGNORECASE)
SIN_MUSICA = re.compile(r"\bno\s+music\b", re.IGNORECASE)

#: El bloque CONSTRAINTS habla de «@tag references» en abstracto: no es un tag.
MARCADORES = {"@tag", "@tags"}
#: Citas posicionales del proveedor: @Image1, @Video1, @Audio1, @Element1 (Kling).
RE_CITA = re.compile(r"@(Image|Video|Audio|Element)(\d+)")
#: Rangos de tiempo literales. El modelo los lee como texto e intenta honrarlos.
RE_RANGO = re.compile(r"\b\d+(?:[.,]\d+)?\s*[-–]\s*\d+(?:[.,]\d+)?\s*s\b", re.IGNORECASE)


def _norm(texto: str) -> str:
    """Colapsa espacios: «palabra por palabra» no significa «con los mismos saltos»."""
    return re.sub(r"\s+", " ", texto).strip()


def _plano_ascii(texto: str) -> str:
    sin = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in sin if not unicodedata.combining(c))


def bloques_de_estilo(style_md: str) -> dict[str, str]:
    """Extrae los bloques inmutables de `style.md` (STYLE PREFIX y CONSTRAINTS)."""
    bloques: dict[str, str] = {}
    for clave, cabecera in (("style", CABECERA_STYLE), ("constraints", CABECERA_CONSTRAINTS)):
        m = cabecera.search(style_md)
        if not m:
            continue
        resto = style_md[m.end():]
        siguiente = CABECERA_CUALQUIERA.search(resto)
        bloques[clave] = (resto[: siguiente.start()] if siguiente else resto).strip()
    return bloques


def _terminos_presentes(texto_plano: str, terminos: list[str]) -> list[str]:
    encontrados = []
    for t in terminos:
        patron = r"\b" + r"\s+".join(re.escape(p) for p in _plano_ascii(t).split()) + r"\b"
        if re.search(patron, texto_plano):
            encontrados.append(t)
    return encontrados


def valida_prompt(texto: str, *, style_md: str = "", registro: Registro | None = None,
                  plano: Plano | None = None, denylist: dict | None = None) -> Resultado:
    """Revisa un prompt completo. Devuelve incidencias con código y regla."""
    r = Resultado()
    normalizado = _norm(texto)
    ascii_plano = _plano_ascii(normalizado)
    lista = cargar_denylist() if denylist is None else denylist

    # R-03 · bloques fijos copiados literalmente desde style.md
    if style_md:
        bloques = bloques_de_estilo(style_md)
        if not bloques.get("style"):
            r.aviso("STYLE_SIN_BLOQUE", "style.md no declara un bloque STYLE PREFIX", "R-03")
        elif _norm(bloques["style"]) not in normalizado:
            r.error("STYLE_PREFIX_AUSENTE",
                    "el STYLE PREFIX de style.md no aparece copiado palabra por palabra", "R-03",
                    _norm(bloques["style"])[:160])
        if not bloques.get("constraints"):
            r.aviso("CONSTRAINTS_SIN_BLOQUE", "style.md no declara un bloque CONSTRAINTS", "R-03")
        elif _norm(bloques["constraints"]) not in normalizado:
            r.error("CONSTRAINTS_AUSENTE",
                    "el bloque CONSTRAINTS de style.md no aparece copiado palabra por palabra",
                    "R-03", _norm(bloques["constraints"])[:160])

    # R-01 y R-02 · tags registrados y descriptores literales.
    # Los bloques copiados de style.md no se inspeccionan: son texto inmutable que
    # menciona «@tag» en abstracto, no referencias de este plano.
    sin_estilo = texto
    for copiado in (bloques_de_estilo(style_md).values() if style_md else []):
        if copiado:
            sin_estilo = sin_estilo.replace(copiado.strip(), " ")
    tags = [t for t in tags_en_texto(sin_estilo)
            if t not in MARCADORES and not RE_CITA.fullmatch(t)]
    for tag in tags:
        if not RE_TAG.match(tag):
            r.error("TAG_MAL_FORMADO", f"{tag} no sigue el formato @tipo_serie_Nombre_vN", "R-01")
            continue
        if registro is None:
            continue
        if not registro.existe(tag):
            r.error("TAG_NO_REGISTRADO", f"{tag} no está en registry.json", "R-01")
            continue
        descriptor = _norm(registro.descriptor(tag))
        if descriptor and descriptor not in normalizado:
            r.error("DESCRIPTOR_NO_LITERAL",
                    f"el descriptor congelado de {tag} no está copiado palabra por palabra",
                    "R-02", descriptor[:160])

    # Citas posicionales: el modelo no conoce nuestros @tag, sólo @Image1, @Image2…
    # («Refer to them in the prompt as @Image1, @Image2, etc.», esquema de fal).
    if plano is not None and registro is not None:
        ranuras = refs.de_plano(registro, plano)
        esperadas = refs.citas_esperadas(ranuras)
        citadas = {f"@{m[0]}{m[1]}" for m in RE_CITA.findall(texto)}
        sin_citar = [c for c in esperadas if c not in citadas]
        if sin_citar:
            r.error("REFERENCIA_SIN_CITAR",
                    f"se mandan {len(esperadas)} referencias y el prompt no cita {sin_citar}. "
                    "El modelo no conoce nuestros @tag: sin la cita posicional puede "
                    "ignorar la imagen", "R-01")
        fuera = [c for c in citadas
                 if c.startswith("@Image") and int(c.removeprefix("@Image")) > len(esperadas)]
        if fuera:
            r.error("CITA_FUERA_DE_RANGO",
                    f"el prompt cita {sorted(fuera)} y sólo se mandan {len(esperadas)} imágenes",
                    "R-01")

    # El prompt debe cubrir exactamente las referencias que el shotlist declara
    if plano is not None:
        faltan = [t for t in plano.refs if t not in tags]
        if faltan:
            r.error("REFERENCIA_FALTA",
                    f"el shotlist declara {faltan} y el prompt no las cita", "R-01")
        sobran = [t for t in tags if RE_TAG.match(t) and t not in plano.refs]
        if sobran:
            r.aviso("REFERENCIA_EXTRA",
                    f"el prompt cita {sobran}, que no están en el shotlist del plano", "R-02")

    # R-09 · "No music" siempre
    if not SIN_MUSICA.search(texto):
        r.error("SIN_NO_MUSIC", 'falta "No music" en el bloque de audio', "R-09")

    # R-07 · tareas, no emociones
    emociones = _terminos_presentes(ascii_plano, lista.get("emociones", []))
    if emociones:
        r.error("VOCABULARIO_EMOCION",
                f"vocabulario de emoción: {emociones}. Escribe objetivo, obstáculo y táctica",
                "R-07")

    # Filtros de los modelos y políticas de plataforma
    filtros = _terminos_presentes(ascii_plano, lista.get("filtros", []))
    if filtros:
        r.error("VOCABULARIO_FILTRO",
                f"vocabulario que dispara los filtros del modelo: {filtros}", "R-08")
    plataforma = _terminos_presentes(ascii_plano, lista.get("plataforma", []))
    if plataforma:
        r.error("VOCABULARIO_PLATAFORMA",
                f"caras, voces o IP ajena: {plataforma}. Las plataformas lo desmonetizan", "R-08")

    # Vocabulario que degrada la calidad (guía oficial de Seedance)
    degradan = _terminos_presentes(ascii_plano, lista.get("degradan", []))
    if degradan:
        r.error("VOCABULARIO_QUE_DEGRADA",
                f"palabras que degradan la generación: {degradan}. «fast» es la peor; "
                "«cinematic» o «epic» son vagas y el modelo rellena a su gusto",
                "prompting")

    # R-02 · cada prompt es una isla
    herencia = _terminos_presentes(ascii_plano, lista.get("herencia", []))
    if herencia:
        r.error("PROMPT_NO_ES_ISLA",
                f"referencias heredadas de otro plano: {herencia}", "R-02")
    if RE_RANGO.search(texto):
        r.error("RANGO_DE_TIEMPO",
                "los rangos tipo «0-5s:» se leen como texto y el modelo intenta honrarlos "
                "literalmente. Usa etiquetas: «Shot 1: … Shot 2: … Closing: …»", "prompting")
    if re.search(r"\b(?:escena|scene|plano)\s+\d+\b", ascii_plano):
        r.aviso("NUMERO_DE_ESCENA",
                "el prompt menciona un número de escena o de plano; cada prompt es una isla",
                "R-02")

    # R-08 · los límites se escriben como condición de toma fallida
    constraints = bloques_de_estilo(style_md).get("constraints", "") if style_md else ""
    constraints_norm = _norm(constraints)
    for linea in texto.splitlines():
        limpia = linea.strip(" -•\t")
        if not limpia or (constraints_norm and _norm(limpia) in constraints_norm):
            continue
        if PROHIBICIONES.match(limpia) and not MARCA_FALLIDA.search(limpia):
            r.aviso("PROHIBICION_SUELTA",
                    "prohibición suelta; descríbelo en positivo y cierra con «= failed take»",
                    "R-08", limpia[:120])
    return r
