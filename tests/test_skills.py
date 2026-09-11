"""Las skills son el system prompt: si están vacías, los agentes no saben nada.

Estos tests no juzgan si el contenido es bueno —eso lo dicen las evaluaciones con
llamadas reales—, pero sí que existe, que cada agente tiene el suyo, y que la skill
enseña **los mismos códigos** que el validador va a comprobar. Un agente que no sabe
con qué se le mide, falla y no entiende por qué.
"""
from __future__ import annotations

import re

import pytest

from showrunner.agentes import director, guionista, qc, showrunner
from showrunner.agentes.base import SKILLS, cargar_skill

AGENTES = {"showrunner": showrunner, "guionista": guionista, "director": director, "qc": qc}

#: Códigos que cada skill tiene que nombrar, porque su validador los emite.
CODIGOS_ESPERADOS = {
    "showrunner": ["DEMASIADOS_PERSONAJES", "DEMASIADAS_LOCALIZACIONES", "SIN_ANCLAS",
                   "SIN_VOZ_LOCK", "SIN_MAPA", "PALETA_NO_HEX", "STYLE_SIN_VERTICAL",
                   "NOMBRE_NO_ETIQUETABLE", "SIN_NO_MUSIC"],
    "guionista": ["EPISODIO_CORTO", "SIN_GANCHO", "SIN_CLIFFHANGER", "SIN_MASTER",
                  "DIALOGO_NO_CABE", "CAMARA_MULTIPLE", "CAMARA_PROHIBIDA",
                  "MASTER_CON_DIALOGO", "TAG_NO_REGISTRADO", "ORDEN_INCOMPLETO"],
    "director-vertical": ["STYLE_PREFIX_AUSENTE", "CONSTRAINTS_AUSENTE", "TAG_NO_REGISTRADO",
                          "TAG_MAL_FORMADO", "DESCRIPTOR_NO_LITERAL", "REFERENCIA_FALTA",
                          "SIN_NO_MUSIC", "VOCABULARIO_EMOCION", "VOCABULARIO_FILTRO",
                          "VOCABULARIO_PLATAFORMA", "PROMPT_NO_ES_ISLA"],
}


def test_cada_agente_tiene_su_propia_skill():
    """El guionista usaba la del showrunner: un atajo, no una decisión."""
    skills = {nombre: modulo.agente().skill for nombre, modulo in AGENTES.items()}
    assert skills == {"showrunner": "showrunner", "guionista": "guionista",
                      "director": "director-vertical", "qc": "qc-continuidad"}
    assert len(set(skills.values())) == 4, "dos agentes comparten system prompt"


@pytest.mark.parametrize("skill", ["showrunner", "guionista", "director-vertical",
                                   "qc-continuidad"])
def test_la_skill_tiene_contenido_de_verdad(skill: str):
    texto = cargar_skill(skill)
    assert len(texto.splitlines()) >= 50, f"{skill} es un esqueleto, no una skill"
    assert "Pendiente de construir" not in texto
    assert re.search(r"^## ", texto, re.MULTILINE), f"{skill} no tiene secciones"


@pytest.mark.parametrize("skill", ["showrunner", "guionista", "director-vertical"])
def test_la_skill_enseña_los_codigos_con_los_que_se_la_mide(skill: str):
    texto = cargar_skill(skill)
    faltan = [c for c in CODIGOS_ESPERADOS[skill] if c not in texto]
    assert not faltan, f"{skill} no menciona: {faltan}"


@pytest.mark.parametrize("skill", ["showrunner", "guionista", "director-vertical",
                                   "qc-continuidad"])
def test_la_skill_dice_cuando_rechazar(skill: str):
    texto = cargar_skill(skill).lower()
    assert "rechaz" in texto, f"{skill} no explica cuándo devolver el trabajo arriba"


def test_el_frontmatter_declara_nombre_y_descripcion():
    for carpeta in sorted(SKILLS.iterdir()):
        bruto = (carpeta / "SKILL.md").read_text(encoding="utf-8")
        assert bruto.startswith("---\n"), carpeta.name
        frontmatter = bruto.split("---", 2)[1]
        assert f"name: {carpeta.name}" in frontmatter
        assert "description:" in frontmatter


# ------------------------------------------------------------- referencias
#: Mínimo de caracteres del prefijo de sistema de cada agente. Por debajo de ~1000
#: tokens la caché de prompt ni siquiera se activa, y por debajo de esto la skill no
#: enseña a pensar: enumera pasos.
MINIMO_CARACTERES = 10_000

REFERENCIAS = {
    "showrunner": ["01_criterios", "02_ejemplo-biblia", "03_errores"],
    "guionista": ["01_presupuesto-de-segundos", "02_ejemplo-episodio", "03_errores"],
    "director-vertical": ["01_vocabulario", "02_ejemplo-prompt", "03_errores"],
    "qc-continuidad": ["01_rubrica", "02_ejemplos"],
}


@pytest.mark.parametrize("skill", list(REFERENCIAS))
def test_cada_skill_trae_sus_referencias(skill: str):
    """El SKILL.md dice qué hacer; las referencias enseñan cómo se piensa."""
    nombres = [r.stem for r in sorted((SKILLS / skill / "referencias").glob("*.md"))]
    assert nombres == REFERENCIAS[skill]


@pytest.mark.parametrize("skill", list(REFERENCIAS))
def test_el_contexto_del_agente_es_lo_bastante_grande(skill: str):
    from showrunner.agentes.base import contexto_de_skill

    bloques = contexto_de_skill(skill)
    assert len(bloques) == 1 + len(REFERENCIAS[skill])
    total = sum(len(b) for b in bloques)
    assert total >= MINIMO_CARACTERES, f"{skill} sólo aporta {total} caracteres de criterio"


@pytest.mark.parametrize("skill", list(REFERENCIAS))
def test_las_referencias_declaran_su_procedencia(skill: str):
    """Distinguir lo validado de la hipótesis es la diferencia entre criterio e invento."""
    for ruta in sorted((SKILLS / skill / "referencias").glob("*.md")):
        texto = ruta.read_text(encoding="utf-8")
        assert "Procedencia" in texto, f"{ruta.name} no dice de dónde sale lo que afirma"
        assert "[V]" in texto and "[H]" in texto, (
            f"{ruta.name} no separa lo validado de la hipótesis")


def test_las_referencias_viajan_en_el_prefijo_cacheado():
    """Son grandes, no cambian y se repiten en cada llamada: es el caso de la caché."""
    import factorias as f

    from showrunner.agentes import director
    from showrunner.agentes.cliente import ClienteFalso
    from showrunner.dominio import registro as reg

    registro = reg.Registro(serie="canon-rojo")
    registro.anadir(reg.Asset(id="@char_canon-rojo_Nadia_v1", descriptor=f.DESCRIPTOR_NADIA))
    cliente = ClienteFalso([f.sobre(f.salida_director())])
    agente = director.agente(cliente)
    sistema = agente.sistema(director.Contexto(
        estable=director.contexto_estable("biblia", "estilo", registro)))

    texto = "\n".join(b["text"] for b in sistema)
    assert "Referencia · 01_vocabulario" in texto
    assert "Referencia · 03_errores" in texto
    concache = [b for b in sistema if "cache_control" in b]
    assert len(concache) == 1 and concache[0] is sistema[-1]
