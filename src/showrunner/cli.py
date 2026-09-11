from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import casting as casting_mod
from . import proyecto
from .agentes.cliente import LLMNoDisponible
from .config import ROOT, cargar_modelos, cargar_modelos_imagen, env
from .dominio import eventos as ev
from .dominio import registro as reg
from .dominio import serie as ser
from .dominio import shotlist as sl
from .dominio.identidad import IdPlano, slugify
from .providers import PeticionVideo, elegir_modelo, estimar_coste, obtener_proveedor
from .providers.imagen import obtener_proveedor_imagen
from .qc import escenas, fotogramas, paleta, sonda
from .valida import valida_episodio, valida_prompt, valida_shotlist, valida_toma

app = typer.Typer(help="Showrunner IA · idea → biblia → producción", no_args_is_help=True)
valida_app = typer.Typer(help="Validadores deterministas (sin coste)", no_args_is_help=True)
casting_app = typer.Typer(help="Preproducción de assets y registry.json", no_args_is_help=True)
app.add_typer(valida_app, name="valida")
app.add_typer(casting_app, name="casting")
con = Console()


def _sin_clave(e: Exception) -> None:
    con.print(f"[red]{e}[/red]\nRellena ANTHROPIC_API_KEY en .env; "
              "`showrunner doctor` te dice qué falta.")
    raise typer.Exit(3)


def _pinta(informe, titulo: str) -> None:
    color = "green" if informe.ok else "red"
    con.print(f"[{color}]{titulo}[/{color}]")
    con.print(informe.resumen())


@app.command()
def doctor():
    """Comprueba dependencias, claves y modelos (sin gastar créditos)."""
    import shutil
    import sys

    t = Table(title="Diagnóstico")
    for col in ("Elemento", "Estado", "Detalle"):
        t.add_column(col)
    t.add_row("Python", "✅" if sys.version_info >= (3, 11) else "❌", sys.version.split()[0])
    for binario in ["ffmpeg", "ffprobe", "git", "node", "claude"]:
        ruta = shutil.which(binario)
        t.add_row(binario, "✅" if ruta else "❌", ruta or "no instalado")
    t.add_row("ANTHROPIC_API_KEY", "✅" if env("ANTHROPIC_API_KEY") else "⚠️",
              "presente" if env("ANTHROPIC_API_KEY") else "vacía (necesaria para el Agent SDK)")
    for nombre in cargar_modelos():
        ok, detalle = obtener_proveedor(nombre).comprobar()
        t.add_row(f"vídeo {nombre}", "✅" if ok else "⚠️", detalle)
    for nombre in cargar_modelos_imagen():
        ok, detalle = obtener_proveedor_imagen(nombre).comprobar()
        t.add_row(f"imagen {nombre}", "✅" if ok else "⚠️", detalle)
    t.add_row("Log de eventos", "ℹ️", str(ev.ruta_bd()))
    t.add_row("Gasto registrado hoy", "ℹ️", f"{ev.gasto_hoy():.2f} $")
    con.print(t)


@app.command()
def modelos():
    """Lista el catálogo con precio por segundo y por imagen."""
    t = Table(title="Modelos de vídeo (USD/seg)")
    for col in ["Modelo", "Nivel", "480p", "720p", "Máx s", "Estado"]:
        t.add_column(col)
    for n, s in cargar_modelos().items():
        p = s["precio_seg"]
        t.add_row(n, s["nivel"], str(p.get("480p", "–")), str(p.get("720p", "–")),
                  str(s["max_duracion"]), s["estado"])
    con.print(t)
    ti = Table(title="Modelos de imagen (USD/imagen)")
    for col in ["Modelo", "Usos", "Precio", "Refs", "Estado"]:
        ti.add_column(col)
    for n, s in cargar_modelos_imagen().items():
        ti.add_row(n, ", ".join(s.get("usos", [])), str(s["precio_img"]),
                   str(s.get("referencias", {}).get("imagenes", "–")), s["estado"])
    con.print(ti)


@app.command()
def nuevo(nombre: str, idea: str = typer.Option("", help="Idea básica en 1–3 frases"),
          plataforma: str = typer.Option("tiktok", help="tiktok | youtube | meta")):
    """Crea la carpeta de una serie nueva con las plantillas rellenadas."""
    ruta = proyecto.crear(nombre, idea, plataforma)
    con.print(f"[green]Serie creada:[/green] {ruta.relative_to(ROOT)}")
    con.print("Siguiente paso: escribir la biblia y aprobarla "
              f"(`showrunner aprobar {ruta.name} biblia --por tu-nombre`).")


@app.command()
def estimar(duracion: int = 5, resolucion: str = "480p", modelo: str = "",
            nivel: str = "borrador"):
    """Estima el coste de un plano."""
    p = PeticionVideo(prompt="-", duracion=duracion, resolucion=resolucion)
    nombre = modelo or elegir_modelo(nivel, p)
    coste = estimar_coste(nombre, p)
    con.print(f"{nombre}: {coste:.3f} $ por {duracion}s a {resolucion}")
    con.print(f"Gastado hoy: {ev.gasto_hoy():.2f} $")


@app.command()
def generar(
    prompt_archivo: Path = typer.Argument(..., help="Archivo .md/.txt con el prompt"),
    salida: Path = typer.Option(..., help="Ruta del .mp4 de salida"),
    modelo: str = typer.Option("", help="Modelo concreto; vacío = el más barato del nivel"),
    nivel: str = typer.Option("borrador", help="borrador | trabajo | clave"),
    duracion: int = 5,
    resolucion: str = "480p",
    imagen: list[str] = typer.Option([], help="URL de referencia (repetible)"),
    primer_fotograma: str = "",
    plano: str = typer.Option("", help="ID del plano, p. ej. s01_ep01_sh003"),
    serie: str = typer.Option("", help="Slug de la serie: activa el linter contra su registro"),
    intento: int = typer.Option(1, help="Nº de intento de este plano (R-11)"),
    saltar_lint: bool = typer.Option(False, help="No bloquear por incidencias del linter"),
):
    """Genera un plano: linter → reserva de presupuesto → generación → QC técnico."""
    texto = prompt_archivo.read_text(encoding="utf-8")
    id_ep = IdPlano.parse(plano).id_episodio if plano else ""

    if serie:
        base = proyecto.ruta(serie)
        registro = reg.cargar(base / "registry.json")
        style_md = (base / "style.md").read_text(encoding="utf-8")
        informe = valida_prompt(texto, style_md=style_md, registro=registro)
        _pinta(informe, "Linter del prompt")
        if not informe.ok and not saltar_lint:
            con.print("[red]No se genera nada.[/red] Corrige el prompt o usa --saltar-lint.")
            raise typer.Exit(2)
        if not imagen:
            from .dominio import referencias as refs_mod
            from .dominio.identidad import RE_TAG, tags_en_texto
            tags = [t for t in tags_en_texto(texto) if RE_TAG.match(t) and registro.existe(t)]
            imagen = refs_mod.urls(refs_mod.ranuras(registro, tags))
            if imagen:
                con.print(f"Referencias del registro: {len(imagen)} (@Image1…@Image{len(imagen)})")

    p = PeticionVideo(prompt=texto, duracion=duracion, resolucion=resolucion, imagenes=list(imagen),
                      primer_fotograma=primer_fotograma or None)
    nombre = modelo or elegir_modelo(nivel, p)
    coste = estimar_coste(nombre, p)
    solicitud = ev.reservar(coste, serie=serie, episodio=id_ep, plano=plano, intento=intento,
                            modelo=nombre, nivel=nivel, resolucion=resolucion, duracion=duracion,
                            salida=str(salida), imagenes=list(imagen))
    con.print(f"Generando con [bold]{nombre}[/bold] · coste estimado {coste:.3f} $ …")
    try:
        res = obtener_proveedor(nombre).generar(p, salida)
    except Exception as e:
        ev.cerrar(solicitud, ok=False, coste_real=0.0, motivo=str(e)[:400])
        con.print(f"[red]Fallo registrado[/red] ({type(e).__name__}): {e}")
        raise typer.Exit(1) from e
    info = sonda.sondear(res.ruta_local)
    ev.cerrar(solicitud, ok=True, coste_real=coste, salida=str(salida), url=res.url,
              task_id=res.task_id, seed=res.seed, tecnico=info)
    con.print(f"[green]Listo:[/green] {salida} · "
              f"{info['ancho']}x{info['alto']} · {info['fps']} fps")
    _pinta(valida_toma(info, duracion_pedida=duracion), "QC técnico")


@app.command()
def qc(video: Path, referencia: Path = typer.Option(None, help="Imagen de referencia de estilo"),
       plano: str = typer.Option("", help="ID del plano para registrar el veredicto"),
       duracion: float = typer.Option(None, help="Duración pedida, para comprobarla")):
    """Control de calidad técnico: formato, cortes, fotogramas, paleta y deriva de color."""
    info = sonda.sondear(video)
    carpeta = video.parent / f"{video.stem}_qc"
    frames = fotogramas.extraer(video, carpeta)
    cortes = escenas.cortes(video)
    informe = {
        "tecnico": info,
        "cortes_detectados": cortes,
        "fotogramas": [str(f) for f in frames],
        "paleta_medio": paleta.paleta(frames[len(frames) // 2]),
    }
    deltas = None
    if referencia:
        deltas = [paleta.delta_e_medio(f, referencia) for f in frames]
        informe["delta_e_vs_referencia"] = deltas
    veredicto = valida_toma(info, duracion_pedida=duracion, delta_e=deltas, cortes=cortes)
    informe["validacion"] = veredicto.como_dict()
    (carpeta / "qc.json").write_text(json.dumps(informe, indent=2, ensure_ascii=False),
                                     encoding="utf-8")
    con.print_json(data=informe)
    if plano:
        ev.registrar("qc_veredicto", plano=plano,
                     episodio=IdPlano.parse(plano).id_episodio,
                     veredicto="aceptada" if veredicto.ok else "rechazada",
                     motivo="; ".join(i.codigo for i in veredicto.errores),
                     segundos=info["duracion"], toma=str(video))


# ------------------------------------------------------------------ valida
@valida_app.command("prompt")
def valida_prompt_cmd(archivo: Path, serie: str = typer.Option(..., help="Slug de la serie"),
                      plano: str = typer.Option("", help="ID del plano del shotlist")):
    """Lint de un prompt contra el registro y el estilo de la serie."""
    base = proyecto.ruta(serie)
    registro = reg.cargar(base / "registry.json")
    style_md = (base / "style.md").read_text(encoding="utf-8")
    ficha = None
    if plano:
        pid = IdPlano.parse(plano)
        ficha = sl.cargar(base / "episodios" / pid.carpeta_episodio / "shotlist.json").plano(plano)
    informe = valida_prompt(archivo.read_text(encoding="utf-8"), style_md=style_md,
                            registro=registro, plano=ficha)
    _pinta(informe, f"Prompt {archivo.name}")
    raise typer.Exit(0 if informe.ok else 2)


@valida_app.command("shotlist")
def valida_shotlist_cmd(serie: str, episodio: str = typer.Option("s01_ep01")):
    """Revisa un shotlist entero: R-01, R-06, R-09, duración del episodio."""
    base = proyecto.ruta(serie)
    proy = ser.cargar(base / "proyecto.json")
    pid = IdPlano.parse(f"{episodio}_sh001")
    lista = sl.cargar(base / "episodios" / pid.carpeta_episodio / "shotlist.json")
    informe = valida_shotlist(lista, registro=reg.cargar(base / "registry.json"),
                              duracion_min=proy.duracion_min,
                              duracion_max=proy.duracion_objetivo_max)
    _pinta(informe, f"Shotlist {episodio} ({lista.duracion_total} s)")
    raise typer.Exit(0 if informe.ok else 2)


@valida_app.command("episodio")
def valida_episodio_cmd(video: Path, serie: str = typer.Option(...),
                        etiqueta_ia: bool = typer.Option(
                            False, help="¿Se va a publicar con etiqueta de IA?")):
    """Revisa el episodio montado antes de publicar."""
    proy = ser.cargar(proyecto.ruta(serie) / "proyecto.json")
    informe = valida_episodio(sonda.sondear(video), proyecto=proy, etiqueta_ia=etiqueta_ia)
    _pinta(informe, f"Episodio {video.name}")
    raise typer.Exit(0 if informe.ok else 2)


# ----------------------------------------------------------------- casting
@casting_app.command("personaje")
def casting_personaje(serie: str, nombre: str, descriptor: str,
                      modelo: str = typer.Option("", help="Vacío = el más barato configurado"),
                      voz_lock: str = "", subir: bool = True):
    """Genera cara + hoja multiángulo y los registra (R-05)."""
    asset = casting_mod.crear_personaje(proyecto.ruta(serie), nombre, descriptor,
                                        modelo=modelo, voz_lock=voz_lock, subir=subir)
    con.print(f"[green]{asset.id}[/green] · {len(asset.referencias)} referencias")


@casting_app.command("localizacion")
def casting_localizacion(serie: str, nombre: str, descriptor: str, mapa: str = "",
                         estado: str = "", modelo: str = "", subir: bool = True):
    """Genera la referencia de una localización y la registra (R-04)."""
    asset = casting_mod.crear_localizacion(proyecto.ruta(serie), nombre, descriptor, mapa=mapa,
                                           estado=estado, modelo=modelo, subir=subir)
    con.print(f"[green]{asset.id}[/green] · {len(asset.referencias)} referencias")


@casting_app.command("prueba")
def casting_prueba(serie: str, tag: str, duracion: int = 3,
                   modelo: str = typer.Option("", help="Modelo de vídeo; «mock» no cuesta nada")):
    """R-12: prueba el asset en movimiento, en borrador, antes de darlo por bueno."""
    informe, ruta = casting_mod.prueba_en_movimiento(proyecto.ruta(serie), tag,
                                                     duracion=duracion, modelo=modelo)
    _pinta(informe, f"Prueba en movimiento de {tag} → {ruta}")


@casting_app.command("aprobar")
def casting_aprobar(serie: str, tag: str, por: str = typer.Option(..., help="Quién aprueba")):
    """CONTROL HUMANO 2: aprueba un asset del casting."""
    asset = casting_mod.aprobar(proyecto.ruta(serie), tag, por)
    con.print(f"[green]{asset.id} aprobado por {por}[/green]")


# ------------------------------------------------------------------ agentes
@app.command()
def biblia(
    titulo: str = typer.Argument(..., help="Título de la serie (crea la carpeta si no existe)"),
    idea: str = typer.Option(..., help="La idea, en 1–3 frases"),
    plataforma: str = typer.Option("tiktok", help="tiktok | youtube | meta"),
    episodios: int = typer.Option(6, help="Episodios a planificar"),
):
    """Agente showrunner: idea → 3 conceptos → biblia, estilo, voces, temporada y registro."""
    from .agentes import escritura
    from .agentes import showrunner as ag

    slug = slugify(titulo)
    base = ROOT / "proyectos" / slug
    if not base.exists():
        base = proyecto.crear(titulo, idea, plataforma)
        con.print(f"Serie creada: {base.relative_to(ROOT)}")
    proy = ser.cargar(base / "proyecto.json")
    con.print("Llamando al showrunner (claude-opus-5, effort xhigh)…")
    try:
        sobre = ag.crear_biblia(idea, titulo, plataforma=plataforma, n_episodios=episodios,
                                proyecto=proy)
    except LLMNoDisponible as e:
        _sin_clave(e)
    if not sobre.ok:
        con.print(f"[red]Rechazo[/red] [{sobre.rechazo.motivo_codigo}] → "
                  f"{sobre.rechazo.destinatario}: {sobre.rechazo.detalle}")
        raise typer.Exit(2)
    escritos = escritura.guardar_biblia(base, sobre.resultado)
    for nombre, ruta in escritos.items():
        con.print(f"  {nombre} → {ruta.relative_to(ROOT)}")
    con.print(f"[green]Biblia escrita.[/green] Gasto acumulado hoy: {ev.gasto_hoy():.4f} $")
    con.print(f"Siguiente: revísala y apruébala con "
              f"`showrunner aprobar {slug} biblia --por tu-nombre`.")


@app.command()
def guion(serie: str, episodio: str = typer.Option("s01_ep01"),
          sinopsis: str = typer.Option("", help="Punto de partida; vacío = lo saca de la biblia")):
    """Agente guionista: biblia → guion.md + shotlist.json con ids canónicos."""
    from .agentes import escritura
    from .agentes import guionista as ag

    base = proyecto.ruta(serie)
    proy = ser.cargar(base / "proyecto.json")
    if not proy.aprobado("biblia"):
        con.print("[red]La biblia no está aprobada.[/red] CONTROL HUMANO 1: "
                  f"`showrunner aprobar {serie} biblia --por tu-nombre`.")
        raise typer.Exit(2)
    con.print("Llamando al guionista (claude-opus-5, effort high)…")
    try:
        sobre = ag.escribir_episodio(
            (base / "biblia.md").read_text(encoding="utf-8"),
            (base / "style.md").read_text(encoding="utf-8"),
            reg.cargar(base / "registry.json"),
            id_episodio=episodio, proyecto=proy, sinopsis=sinopsis, base=base)
    except LLMNoDisponible as e:
        _sin_clave(e)
    if not sobre.ok:
        con.print(f"[red]Rechazo[/red] [{sobre.rechazo.motivo_codigo}] → "
                  f"{sobre.rechazo.destinatario}: {sobre.rechazo.detalle}")
        raise typer.Exit(2)
    escritos = escritura.guardar_episodio(base, sobre.resultado, episodio)
    for nombre, ruta in escritos.items():
        con.print(f"  {nombre} → {ruta.relative_to(ROOT)}")
    con.print(f"[green]Episodio escrito[/green] · {sobre.resultado.duracion_total} s · "
              f"{len(sobre.resultado.planos)} planos")


@app.command()
def prompts(serie: str, episodio: str = typer.Option("s01_ep01"),
            plano: str = typer.Option("", help="Un plano concreto; vacío = todos"),
            sobrescribir: bool = typer.Option(False, help="Rehacer prompts que ya existen")):
    """Agente director: cada plano del shotlist → su prompt, ya pasado por el linter."""
    from .agentes import director as ag

    base = proyecto.ruta(serie)
    registro = reg.cargar(base / "registry.json")
    estilo = (base / "style.md").read_text(encoding="utf-8")
    biblia_md = (base / "biblia.md").read_text(encoding="utf-8")
    carpeta = base / "episodios" / IdPlano.parse(f"{episodio}_sh001").carpeta_episodio
    lista = sl.cargar(carpeta / "shotlist.json")
    destino = carpeta / "prompts"
    destino.mkdir(parents=True, exist_ok=True)

    planos = [lista.plano(plano)] if plano else lista.en_orden
    con.print(f"Escribiendo {len(planos)} prompts con claude-sonnet-5 (caché de 1 h)…")
    rechazados = 0
    for ficha in planos:
        salida_md = destino / f"{ficha.id}.md"
        if salida_md.exists() and not sobrescribir:
            con.print(f"  {ficha.id}: ya existe, se salta")
            continue
        try:
            sobre = ag.escribir_prompt(ficha, registro, biblia_md=biblia_md, estilo_md=estilo,
                                       serie=serie)
        except LLMNoDisponible as e:
            _sin_clave(e)
        if not sobre.ok:
            rechazados += 1
            con.print(f"  [red]{ficha.id}[/red] [{sobre.rechazo.motivo_codigo}] "
                      f"{sobre.rechazo.detalle}")
            continue
        salida_md.write_text(sobre.resultado.prompt, encoding="utf-8")
        con.print(f"  [green]{ficha.id}[/green] → {salida_md.relative_to(ROOT)}")
    con.print(f"Gasto acumulado hoy: {ev.gasto_hoy():.4f} $")
    if rechazados:
        raise typer.Exit(2)


@app.command()
def humo(
    modelo: str = typer.Option("claude-sonnet-5", help="Modelo de lenguaje de la prueba"),
    video: bool = typer.Option(False, help="Añade un plano real al nivel más barato"),
    modelo_video: str = typer.Option("", help="Fuerza el modelo de vídeo"),
    duracion: int = typer.Option(3, help="Segundos del plano de prueba"),
):
    """Primera llamada real, barata: comprueba esquema, caché y conectores.

    Es lo que los mocks no pueden decir. Dos llamadas al LLM cuestan unos céntimos;
    con --video se añade un plano de unos 0,04–0,15 $.
    """
    from .humo import prueba_llm, prueba_video

    con.print("[bold]Prueba de humo del cerebro[/bold] (2 llamadas, unos céntimos)…")
    informe = prueba_llm(modelo=modelo)
    for paso in informe.pasos:
        con.print(str(paso))

    if video:
        salida = ROOT / "runs" / "humo.mp4"
        p = PeticionVideo(prompt="-", duracion=duracion, resolucion="480p")
        nombre = modelo_video or elegir_modelo("borrador", p)
        con.print(f"\n[bold]Prueba de humo del vídeo[/bold] · {nombre} · "
                  f"{estimar_coste(nombre, p):.3f} $ estimados…")
        informe_video = prueba_video(salida, modelo=modelo_video, duracion=duracion)
        for paso in informe_video.pasos:
            con.print(str(paso))
        informe.pasos.extend(informe_video.pasos)
        informe.coste_usd += informe_video.coste_usd

    con.print(f"\nCoste real de la prueba: [bold]{informe.coste_usd:.4f} $[/bold] · "
              f"gastado hoy: {ev.gasto_hoy():.4f} $")
    if not informe.ok:
        con.print("[red]Algo no responde como esperábamos.[/red] "
                  "Arréglalo antes de gastar en un episodio.")
        raise typer.Exit(1)
    con.print("[green]Todo responde.[/green] Siguiente paso: docs/PLAN_DE_PRUEBAS.md")


# ------------------------------------------------------------ orquestador
@app.command()
def plan(serie: str, episodio: str = typer.Option("s01_ep01")):
    """Dónde está la serie y cuál es el siguiente paso. No ejecuta nada ni gasta."""
    from .orquestador import Orquestador

    for paso in Orquestador(serie).diagnostico(episodio):
        con.print(str(paso))
        if paso.estado.value != "hecho" and paso.accion:
            con.print(f"    [dim]{paso.accion}[/dim]")


@app.command()
def producir(
    serie: str,
    episodio: str = typer.Option("s01_ep01"),
    idea: str = typer.Option("", help="Sólo si la serie aún no tiene biblia"),
    nivel: str = typer.Option("borrador", help="borrador | trabajo | clave"),
    resolucion: str = typer.Option("480p"),
    max_gasto: float = typer.Option(10.0, help="Fusible de ESTA ejecución, en USD"),
    modelo_video: str = typer.Option("", help="Fuerza un modelo; «mock» no cuesta nada"),
    modelo_imagen: str = typer.Option(""),
    desatendido: str = typer.Option("", help="Nombre de quien se hace responsable; "
                                             "aprueba los gates automáticamente"),
    montar: bool = typer.Option(True, help="Montar el episodio al terminar"),
    subir: bool = typer.Option(True, help="Subir las referencias del casting a una URL pública"),
):
    """Avanza la serie hasta el siguiente control humano y para.

    Idempotente: una toma con la misma huella (modelo + parámetros + referencias)
    no se vuelve a generar ni a pagar.
    """
    from .orquestador import Politica
    from .orquestador import producir as ejecutar

    if desatendido:
        politica = Politica.desatendida(desatendido, max_gasto_usd=max_gasto, nivel=nivel,
                                        resolucion=resolucion, modelo_video=modelo_video,
                                        modelo_imagen=modelo_imagen, subir_referencias=subir)
        con.print(f"[yellow]Modo desatendido[/yellow] bajo la responsabilidad de {desatendido}: "
                  "los gates se aprueban solos y queda registrado que fue automático.")
    else:
        politica = Politica(max_gasto_usd=max_gasto, nivel=nivel, resolucion=resolucion,
                            modelo_video=modelo_video, modelo_imagen=modelo_imagen,
                            subir_referencias=subir)
    con.print(f"Fusible de esta ejecución: {max_gasto:.2f} $ · gastado hoy: {ev.gasto_hoy():.2f} $")

    informe = ejecutar(serie, idea=idea, id_episodio=episodio, politica=politica, montar=montar)
    for paso in informe.pasos:
        con.print(str(paso))
    con.print(f"\nGastado en esta ejecución: [bold]{informe.gastado:.3f} $[/bold]"
              + (f" · reutilizado sin pagar: {informe.reutilizado:.3f} $"
                 if informe.reutilizado else ""))
    parado = informe.parado_en
    if parado:
        con.print(f"[yellow]Parado en:[/yellow] {parado.nombre} — {parado.detalle}")
        if parado.accion:
            con.print(f"  {parado.accion}")
        raise typer.Exit(0 if parado.estado.value == "espera_humano" else 1)
    con.print("[green]Fase completada.[/green]")


@app.command()
def montar(serie: str, episodio: str = typer.Option("s01_ep01"),
           quemar_subtitulos: bool = typer.Option(False, help="Quemarlos en la zona segura")):
    """Monta el episodio con las tomas aprobadas: concatena, escala a 1080×1920 y saca el .srt."""
    from .montaje import SinTomas
    from .montaje import montar as montar_episodio
    from .orquestador import Orquestador

    orq = Orquestador(serie)
    proy_ = orq.proyecto
    lista = orq.shotlist(episodio)
    destino = orq._carpeta(episodio) / "final.mp4"
    try:
        escritos = montar_episodio(lista, orq.estados(episodio), destino, proyecto=proy_,
                                   quemar_subtitulos=quemar_subtitulos)
    except SinTomas as e:
        con.print(f"[red]{e}[/red]")
        raise typer.Exit(2) from e
    for nombre, ruta in escritos.items():
        con.print(f"  {nombre} → {ruta.relative_to(ROOT)}")
    _pinta(valida_episodio(sonda.sondear(escritos["final"]), proyecto=proy_, etiqueta_ia=True),
           "Validación del episodio")


# ---------------------------------------------------------------- registro
@app.command()
def aprobar(serie: str, tipo: str = typer.Argument("biblia", help="biblia | casting | episodio"),
            por: str = typer.Option(..., help="Quién aprueba"), version: str = "0.1",
            referencia: str = typer.Option("", help="ID de episodio si tipo=episodio")):
    """Registra un control humano con firma, fecha y versión."""
    base = proyecto.ruta(serie)
    proy = ser.cargar(base / "proyecto.json")
    ap = proy.aprobar(tipo, por=por, version=version, referencia=referencia)
    ser.guardar(proy, base / "proyecto.json")
    ev.registrar("aprobacion_humana", serie=proy.slug, episodio=referencia, tipo=tipo, por=por,
                 version=version)
    con.print(f"[green]{tipo} aprobado[/green] por {ap.por} el {ap.fecha} (v{ap.version})")


@app.command()
def estado(serie: str = "", episodio: str = ""):
    """Estado plegado de cada plano desde el log de eventos."""
    estados = ev.plegar(serie=serie, episodio=episodio)
    t = Table(title=f"Estado de planos{f' · {serie}' if serie else ''}")
    for col in ["Plano", "Estado", "Intentos", "Fallos", "Coste $", "Toma aprobada", "Motivo"]:
        t.add_column(col)
    for pid in sorted(estados):
        e = estados[pid]
        t.add_row(pid, e.estado, str(e.intentos), str(e.fallos), f"{e.coste:.3f}",
                  e.toma_aprobada or "–", e.motivo_rechazo or "")
    con.print(t)
    con.print_json(data=ev.metricas(serie=serie, episodio=episodio))


@app.command()
def eventos(export: Path = typer.Option(None, help="Vuelca el log a un .jsonl"),
            formato: str = typer.Option("eventos", help="eventos | ledger"),
            migrar: Path = typer.Option(None, help="Importa un ledger.jsonl antiguo"),
            limite: int = typer.Option(20, help="Últimos N eventos a mostrar")):
    """Consulta, migra o exporta el log de eventos."""
    if migrar:
        con.print(f"[green]{ev.migrar_jsonl(migrar)}[/green] generaciones importadas de {migrar}")
    if export:
        con.print(f"[green]{ev.exportar_jsonl(export, formato)}[/green] filas en {export}")
        return
    t = Table(title="Últimos eventos")
    for col in ["id", "ts", "serie", "plano", "int.", "tipo", "coste"]:
        t.add_column(col)
    for e in ev.leer()[-limite:]:
        coste = e["coste_real"] if e["coste_real"] is not None else e["coste_estimado"]
        t.add_row(str(e["id"]), e["ts"], e["serie"], e["plano"], str(e["intento"]), e["tipo"],
                  f"{coste:.3f}" if coste else "–")
    con.print(t)


if __name__ == "__main__":
    app()
