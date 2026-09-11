"""De la salida de un agente a los archivos de la serie.

El puente entre la capa 3 (agentes) y la capa 0 (contratos): lo que el showrunner
decide acaba en `registry.json` con su descriptor congelado y su tag, de modo que
R-01 y R-02 son comprobables desde el primer minuto. El casting rellena después las
referencias; el registro ya existe.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..dominio import registro as reg
from ..dominio import serie as ser
from ..dominio import shotlist as sl
from ..dominio.identidad import IdPlano, Tag, parse_episodio
from .contratos import Biblia, Estilo, SalidaGuionista, SalidaShowrunner
from .guionista import a_guion_md, a_shotlist


def biblia_md(biblia: Biblia, slug: str) -> str:
    p = ["\n".join([
        f"# BIBLIA · {biblia.titulo}",
        "> Estado: borrador · Versión: 0.1",
        "> La aprobación humana se registra en `proyecto.json` (firma, fecha y versión), no aquí.",
        "",
        "## 1. Concepto",
        f"- Logline: {biblia.logline}",
        f"- Género y tono: {biblia.genero_y_tono}",
        f"- Público y plataforma: {biblia.publico_y_plataforma}",
        f"- Promesa del formato: {biblia.promesa_del_formato}",
        f"- Producibilidad IA: {biblia.producibilidad}/10 · {biblia.motivo_producibilidad}",
        "",
        "## 2. Fórmula de episodio (61–90 s, 9:16)",
        f"- 0–3 s gancho: {biblia.formula.gancho}",
        f"- Giro central: {biblia.formula.giro}",
        f"- Cliffhanger: {biblia.formula.cliffhanger}",
        "",
        "## 3. Mundo y reglas",
        f"- Época y lugar: {biblia.epoca_y_lugar}",
        "- Reglas del mundo:",
        *[f"  - {r}" for r in biblia.reglas_del_mundo],
        f"- Regla visual narrativa: {biblia.regla_visual_narrativa}",
        "",
        "## 4. Personajes",
    ])]
    for personaje in biblia.personajes:
        tag = Tag.nuevo("char", slug, personaje.nombre)
        p.append("\n".join([
            f"### {tag}",
            f"- Descriptor congelado: {personaje.descriptor_congelado}",
            f"- Anclas de identidad: {', '.join(personaje.anclas_identidad)}",
            f"- VOZ LOCK: {personaje.voz_lock}",
            f"- Máscara pública: {personaje.perfil.mascara_publica}",
            f"- Qué la rompe: {personaje.perfil.que_la_rompe}",
            f"- Hábitos físicos: {personaje.perfil.habitos_fisicos}",
            f"- Forma de caminar: {personaje.perfil.forma_de_caminar}",
            f"- Objetivo de temporada: {personaje.objetivo_temporada}",
        ]))
    p.append("## 5. Localizaciones")
    for local in biblia.localizaciones:
        tag = Tag.nuevo("loc", slug, local.nombre)
        p.append("\n".join([
            f"### {tag}",
            f"- Descripción: {local.descriptor_congelado}",
            f"- Mapa espacial vertical: {local.mapa_vertical}",
            f"- Estados: {', '.join(local.estados)}",
        ]))
    if biblia.props:
        p.append("## 6. Props")
        for prop in biblia.props:
            tag = Tag.nuevo("prop", slug, prop.nombre)
            p.append(f"### {tag}\n- {prop.descriptor_congelado}\n"
                     f"- Estados: {', '.join(prop.estados)}")
    p.append("## 7. Estilo (ver style.md)\n## 8. Arco de temporada (ver temporada.json)")
    p.append("## 9. Riesgos de producción\n"
             + "\n".join(f"- {r}" for r in biblia.riesgos_de_produccion))
    return "\n\n".join(p) + "\n"


def style_md(estilo: Estilo) -> str:
    return "\n".join([
        "# STYLE PREFIX (inmutable durante toda la serie)",
        estilo.style_prefix,
        "",
        "# CONSTRAINTS (inmutable)",
        estilo.constraints,
        "",
        "# PALETA (hex)",
        f"- dominante: {estilo.paleta.dominante}",
        f"- secundaria: {estilo.paleta.secundaria}",
        f"- acento reservado: {estilo.paleta.acento_reservado} "
        f"({estilo.paleta.significado_del_acento})",
        "",
    ])


def voces_md(biblia: Biblia) -> str:
    partes = ["# BIBLIA DE VOCES"]
    for personaje in biblia.personajes:
        partes.append(f"## {personaje.nombre}\nAUDIO LOCK: {personaje.voz_lock}")
    return "\n\n".join(partes) + "\n"


def registro_desde_biblia(biblia: Biblia, slug: str) -> reg.Registro:
    """Assets con su descriptor congelado y estado `pendiente`.

    Sin referencias todavía: las pone el casting. Pero el tag y el descriptor ya
    existen, que es lo que exige R-01 antes de rodar nada.
    """
    registro = reg.Registro(serie=slug)
    for personaje in biblia.personajes:
        registro.anadir(reg.Asset(
            id=str(Tag.nuevo("char", slug, personaje.nombre)),
            descriptor=personaje.descriptor_congelado,
            voz_lock=personaje.voz_lock,
            notas="Anclas: " + ", ".join(personaje.anclas_identidad),
        ))
    for local in biblia.localizaciones:
        registro.anadir(reg.Asset(
            id=str(Tag.nuevo("loc", slug, local.nombre)),
            descriptor=local.descriptor_congelado,
            mapa=local.mapa_vertical,
            notas="Estados: " + ", ".join(local.estados),
        ))
    for prop in biblia.props:
        registro.anadir(reg.Asset(
            id=str(Tag.nuevo("prop", slug, prop.nombre)),
            descriptor=prop.descriptor_congelado,
            notas="Estados: " + ", ".join(prop.estados),
        ))
    return registro


def guardar_biblia(base: Path, salida: SalidaShowrunner) -> dict[str, Path]:
    """Escribe biblia, estilo, voces, temporada y registro en la carpeta de la serie."""
    base = Path(base)
    proyecto = ser.cargar(base / "proyecto.json")
    slug = proyecto.slug
    escritos: dict[str, Path] = {}

    # `biblia.json` es la fuente estructurada; `biblia.md` es su lectura humana.
    # Tener las dos permite evaluar la biblia sin volver a llamar al modelo.
    for nombre, contenido in (
        ("biblia.json", json.dumps(salida.model_dump(mode="json"), indent=2,
                                   ensure_ascii=False) + "\n"),
        ("biblia.md", biblia_md(salida.biblia, slug)),
        ("style.md", style_md(salida.estilo)),
        ("voces.md", voces_md(salida.biblia)),
    ):
        ruta = base / nombre
        ruta.write_text(contenido, encoding="utf-8")
        escritos[nombre] = ruta

    temporada = {
        "temporada": proyecto.temporada,
        "episodios": [
            {"id": f"s{proyecto.temporada:02d}_ep{e.numero:02d}", "titulo": e.titulo,
             "gancho": e.gancho, "giro": e.giro, "cliffhanger": e.cliffhanger,
             "estado": "pendiente"}
            for e in sorted(salida.temporada, key=lambda e: e.numero)
        ],
    }
    ruta = base / "temporada.json"
    ruta.write_text(json.dumps(temporada, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    escritos["temporada.json"] = ruta

    # El registro existente manda: no se pisan assets que ya tienen referencias.
    nuevo = registro_desde_biblia(salida.biblia, slug)
    actual = reg.cargar(base / "registry.json")
    for asset in nuevo.assets():
        if not actual.existe(asset.id):
            actual.anadir(asset)
    escritos["registry.json"] = reg.guardar(actual, base / "registry.json")
    return escritos


def guardar_episodio(base: Path, salida: SalidaGuionista, id_episodio: str) -> dict[str, Path]:
    """Escribe `guion.md` y `shotlist.json` con ids canónicos."""
    base = Path(base)
    _, numero = parse_episodio(id_episodio)
    carpeta = base / "episodios" / IdPlano(1, numero, 1).carpeta_episodio
    carpeta.mkdir(parents=True, exist_ok=True)
    guion = carpeta / "guion.md"
    guion.write_text(a_guion_md(salida, id_episodio), encoding="utf-8")
    estructurado = carpeta / "guion.json"
    estructurado.write_text(
        json.dumps(salida.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    lista = sl.guardar(a_shotlist(salida, id_episodio), carpeta / "shotlist.json")
    return {"guion.md": guion, "guion.json": estructurado, "shotlist.json": lista}
