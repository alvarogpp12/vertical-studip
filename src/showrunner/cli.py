from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import ledger, proyecto
from .config import ROOT, cargar_modelos, env
from .providers import PeticionVideo, elegir_modelo, estimar_coste, obtener_proveedor
from .qc import escenas, fotogramas, paleta, sonda

app = typer.Typer(help="Showrunner IA · idea → biblia → producción", no_args_is_help=True)
con = Console()


@app.command()
def doctor():
    """Comprueba dependencias, claves y modelos (sin gastar créditos)."""
    t = Table(title="Diagnóstico")
    t.add_column("Elemento"); t.add_column("Estado"); t.add_column("Detalle")
    t.add_row("Python", "✅" if sys.version_info >= (3, 11) else "❌", sys.version.split()[0])
    for binario in ["ffmpeg", "ffprobe", "git", "node", "claude"]:
        ruta = shutil.which(binario)
        t.add_row(binario, "✅" if ruta else "❌", ruta or "no instalado")
    t.add_row("ANTHROPIC_API_KEY", "✅" if env("ANTHROPIC_API_KEY") else "⚠️",
              "presente" if env("ANTHROPIC_API_KEY") else "vacía (necesaria para el Agent SDK)")
    for nombre in cargar_modelos():
        ok, detalle = obtener_proveedor(nombre).comprobar()
        t.add_row(f"modelo {nombre}", "✅" if ok else "⚠️", detalle)
    t.add_row("Gasto registrado hoy", "ℹ️", f"{ledger.gasto_hoy():.2f} $")
    con.print(t)


@app.command()
def modelos():
    """Lista el catálogo con precio por segundo."""
    t = Table(title="Catálogo de modelos (USD/seg)")
    for col in ["Modelo", "Nivel", "480p", "720p", "Máx s", "Estado"]:
        t.add_column(col)
    for n, s in cargar_modelos().items():
        p = s["precio_seg"]
        t.add_row(n, s["nivel"], str(p.get("480p", "–")), str(p.get("720p", "–")),
                  str(s["max_duracion"]), s["estado"])
    con.print(t)


@app.command()
def nuevo(nombre: str, idea: str = typer.Option("", help="Idea básica en 1–3 frases")):
    """Crea la carpeta de una serie nueva."""
    ruta = proyecto.crear(nombre, idea)
    con.print(f"[green]Serie creada:[/green] {ruta.relative_to(ROOT)}")


@app.command()
def estimar(duracion: int = 5, resolucion: str = "480p", modelo: str = "", nivel: str = "borrador"):
    """Estima el coste de un plano."""
    p = PeticionVideo(prompt="-", duracion=duracion, resolucion=resolucion)
    nombre = modelo or elegir_modelo(nivel, p)
    con.print(f"{nombre}: {estimar_coste(nombre, p):.3f} $ por {duracion}s a {resolucion}")


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
):
    """Genera un plano con control de presupuesto y lo registra en el ledger."""
    p = PeticionVideo(prompt=prompt_archivo.read_text(encoding="utf-8"), duracion=duracion,
                      resolucion=resolucion, imagenes=imagen,
                      primer_fotograma=primer_fotograma or None)
    nombre = modelo or elegir_modelo(nivel, p)
    coste = estimar_coste(nombre, p)
    ledger.comprobar_presupuesto(coste)
    con.print(f"Generando con [bold]{nombre}[/bold] · coste estimado {coste:.3f} $ …")
    res = obtener_proveedor(nombre).generar(p, salida)
    info = sonda.sondear(res.ruta_local)
    ledger.registrar(plano=plano, modelo=nombre, coste_usd=coste, prompt=p.prompt,
                     imagenes=p.imagenes, duracion=p.duracion, resolucion=p.resolucion,
                     salida=str(salida), task_id=res.task_id, seed=res.seed, tecnico=info,
                     veredicto="pendiente")
    con.print(f"[green]Listo:[/green] {salida} · {info['ancho']}x{info['alto']} · {info['fps']} fps")


@app.command()
def qc(video: Path, referencia: Path = typer.Option(None, help="Imagen de referencia de estilo")):
    """Control de calidad técnico: formato, cortes, fotogramas, paleta y deriva de color."""
    info = sonda.sondear(video)
    carpeta = video.parent / f"{video.stem}_qc"
    frames = fotogramas.extraer(video, carpeta)
    informe = {
        "tecnico": info,
        "cortes_detectados": escenas.cortes(video),
        "fotogramas": [str(f) for f in frames],
        "paleta_medio": paleta.paleta(frames[len(frames) // 2]),
    }
    if referencia:
        informe["delta_e_vs_referencia"] = [paleta.delta_e_medio(f, referencia) for f in frames]
    (carpeta / "qc.json").write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")
    con.print_json(data=informe)


if __name__ == "__main__":
    app()
