"""Montaje del episodio con FFmpeg. Sin LLM: el orden ya lo decidió el shotlist.

Dos decisiones que vienen de las reglas del proyecto:

* **Se escala aquí, no en el proveedor.** Seedance 2.5 no genera 1080p nativo y el
  «1080p» de los revendedores es un upscale caro. Se genera a 720p como mucho y el
  máster final se escala a 1080×1920 en local, que es gratis.
* **Los subtítulos van en un `.srt` aparte, no quemados.** El quinto inferior se
  deja libre para que los ponga la plataforma. `--quemar` existe para cuando hace
  falta, y los coloca dentro de la zona segura.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .dominio import eventos as ev
from .dominio import shotlist as sl
from .dominio.serie import Proyecto

#: Zonas seguras de interfaz en 1080×1920 (00_investigacion_sistema.md).
MARGEN_SUPERIOR = 130
MARGEN_INFERIOR = 320


class SinTomas(RuntimeError):
    """No hay tomas aceptadas que montar."""


@dataclass
class Segmento:
    plano: str
    ruta: Path
    duracion: float
    dialogo: str


def _ffmpeg(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def segmentos(lista: sl.Shotlist, estados: dict[str, ev.EstadoPlano]) -> list[Segmento]:
    """Las tomas aprobadas, en orden de montaje. Un plano sin toma corta el montaje."""
    salida = []
    faltan = []
    for plano in lista.en_orden:
        estado = estados.get(plano.id)
        if estado is None or not estado.toma_aprobada:
            faltan.append(plano.id)
            continue
        ruta = Path(estado.toma_aprobada)
        if not ruta.exists():
            faltan.append(f"{plano.id} (falta {ruta})")
            continue
        util = estado.segundos_aceptados or plano.duracion
        salida.append(Segmento(plano.id, ruta, float(util), plano.dialogo))
    if faltan:
        raise SinTomas(f"sin toma aprobada: {faltan}")
    if not salida:
        raise SinTomas("el shotlist no tiene planos")
    return salida


def _srt(segs: list[Segmento]) -> str:
    def marca(t: float) -> str:
        h, resto = divmod(t, 3600)
        m, s = divmod(resto, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{round((s % 1) * 1000):03d}"

    lineas, reloj, numero = [], 0.0, 1
    for seg in segs:
        if seg.dialogo.strip():
            # R-09: el diálogo ocupa la duración menos el segundo de cola limpia.
            fin = reloj + max(seg.duracion - 1.0, 0.5)
            lineas.append(f"{numero}\n{marca(reloj)} --> {marca(fin)}\n{seg.dialogo.strip()}\n")
            numero += 1
        reloj += seg.duracion
    return "\n".join(lineas)


def montar(lista: sl.Shotlist, estados: dict[str, ev.EstadoPlano], destino: Path, *,
           proyecto: Proyecto, quemar_subtitulos: bool = False) -> dict[str, Path]:
    """Concatena las tomas aprobadas, escala a 1080×1920 y escribe el `.srt`."""
    segs = segmentos(lista, estados)
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    ancho, alto = (int(x) for x in proyecto.resolucion_final.split("x"))

    trozos = []
    normalizados = destino.parent / f"{destino.stem}_trozos"
    normalizados.mkdir(parents=True, exist_ok=True)
    for indice, seg in enumerate(segs):
        trozo = normalizados / f"{indice:03d}_{seg.plano}.mp4"
        _ffmpeg([
            "-i", str(seg.ruta), "-t", f"{seg.duracion:g}",
            "-vf", f"scale={ancho}:{alto}:force_original_aspect_ratio=decrease,"
                   f"pad={ancho}:{alto}:(ow-iw)/2:(oh-ih)/2,fps={proyecto.fps}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000",
            str(trozo),
        ])
        trozos.append(trozo)

    lista_txt = normalizados / "concat.txt"
    lista_txt.write_text("".join(f"file '{t.name}'\n" for t in trozos), encoding="utf-8")
    _ffmpeg(["-f", "concat", "-safe", "0", "-i", str(lista_txt),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(destino)])

    escritos = {"final": destino}
    srt = _srt(segs)
    if srt.strip():
        ruta_srt = destino.with_suffix(".srt")
        ruta_srt.write_text(srt, encoding="utf-8")
        escritos["subtitulos"] = ruta_srt
        if quemar_subtitulos:
            quemado = destino.with_name(f"{destino.stem}_sub.mp4")
            estilo = (f"FontSize=18,Alignment=2,MarginV={MARGEN_INFERIOR // 4},"
                      "PrimaryColour=&H00FFFFFF,BorderStyle=3")
            _ffmpeg(["-i", str(destino),
                     "-vf", f"subtitles={ruta_srt}:force_style='{estilo}'",
                     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy", str(quemado)])
            escritos["quemado"] = quemado
    return escritos
