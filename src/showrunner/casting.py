"""Preproducción: genera los assets y **escribe `registry.json`**.

Es el primer código del proyecto que toca el registro. Hasta ahora era honor
system entre prompts, así que R-01 no se podía aplicar.

Reglas que se aplican aquí, no en un documento:

* **R-05** · las hojas van en fondo gris y multiángulo, y *el primer plano original
  de la cara no se regenera*: una vez registrada, la referencia `cara` queda
  congelada y sólo se puede sustituir creando una versión nueva del asset.
* **R-04** · la referencia de localización manda en geometría, materiales y luz,
  nunca en el encuadre, y la sala no se amplía.
* **R-12** · un asset no se da por bueno hasta verlo en movimiento, en borrador.
"""
from __future__ import annotations

from pathlib import Path

from .dominio import eventos as ev
from .dominio import registro as reg
from .dominio.identidad import Tag
from .providers import PeticionVideo, elegir_modelo, estimar_coste, obtener_proveedor
from .providers.imagen import (
    PeticionImagen,
    elegir_modelo_imagen,
    estimar_coste_imagen,
    obtener_proveedor_imagen,
)
from .providers.subida import asegurar_url
from .qc import sonda
from .valida.resultado import Resultado
from .valida.toma import valida_toma

#: R-05 · la cara de referencia: un solo ángulo, neutra, sin estilo de la serie.
PROMPT_CARA = (
    "Photoreal studio headshot of {descriptor} "
    "Neutral expression, eyes open and alive with catch-lights, facing camera. "
    "Flat neutral grey seamless background, even soft key light, 85mm lens. "
    "Full head and shoulders in frame; any crop of the face = failed take."
)

#: R-05 · hoja multiángulo, fondo gris, identidad anclada a la cara ya registrada.
PROMPT_HOJA = (
    "Character sheet of {descriptor} "
    "The face, hair and wardrobe match the reference image exactly. "
    "{angulos} of the same person, evenly spaced on a flat neutral grey background, "
    "full body, even soft light, no props and no scenery. "
    "A different face between panels = failed take."
)

#: R-04 · la localización describe geometría, materiales y luz; nunca el encuadre.
PROMPT_LOCALIZACION = (
    "Photoreal empty interior reference of {descriptor} "
    "Shows geometry, materials and light only: no people, no camera framing intent. "
    "{estado} "
    "Anchored objects stay where described; adding rooms or windows = failed take."
)

ANGULOS = ("Front, three-quarter left, profile left, three-quarter right, profile right "
           "and back views")


class CaraCongelada(RuntimeError):
    """R-05: el primer plano original de la cara no se regenera."""


def _generar_imagenes(modelo: str, peticion: PeticionImagen, destino: Path, *,
                      serie: str, etiqueta: str) -> list[str | Path]:
    """Reserva presupuesto, genera y cierra el evento. Nunca gasta sin registrar."""
    coste = estimar_coste_imagen(modelo, peticion)
    solicitud = ev.reservar(coste, serie=serie, plano=etiqueta, intento=1, modelo=modelo,
                            tipo_medio="imagen", n=peticion.n, prompt=peticion.prompt)
    try:
        resultado = obtener_proveedor_imagen(modelo).generar(peticion, destino)
    except Exception as e:
        ev.cerrar(solicitud, ok=False, coste_real=0.0, motivo=str(e)[:400])
        raise
    ev.cerrar(solicitud, ok=True, coste_real=coste,
              salida=str(destino), urls=resultado.urls, rutas=[str(r) for r in resultado.rutas])
    # fal ya devuelve URLs públicas; el mock sólo deja archivos locales.
    return list(resultado.urls) or list(resultado.rutas)


def crear_personaje(base: Path, nombre: str, descriptor: str, *, voz_lock: str = "",
                    modelo: str = "", angulos: str = ANGULOS, version: int = 1,
                    subir: bool = True) -> reg.Asset:
    """Cara + hoja multiángulo de un personaje, registradas en `registry.json`.

    Si el personaje ya tiene cara registrada, **no se regenera** (R-05): se añade
    la hoja sobre la cara existente. Para cambiarle la cara hay que crear la
    versión siguiente del asset.
    """
    base = Path(base)
    ruta_registro = base / "registry.json"
    registro = reg.cargar(ruta_registro)
    tag = Tag.nuevo("char", registro.serie, nombre, version)
    modelo = modelo or elegir_modelo_imagen("hojas")
    carpeta = base / "assets" / str(tag).lstrip("@")
    carpeta.mkdir(parents=True, exist_ok=True)

    existente = registro.resolver(str(tag)) if registro.existe(str(tag)) else None
    asset = existente or reg.Asset(id=str(tag), descriptor=descriptor, version=version,
                                   voz_lock=voz_lock, creado_con=modelo)
    if existente and existente.descriptor != descriptor:
        raise CaraCongelada(
            f"{tag} ya está registrado con otro descriptor. Un estado nuevo es un asset "
            f"nuevo (R-01): crea {tag.con_version(version + 1)}."
        )

    cara = asset.cara_congelada
    if cara is None:
        salidas = _generar_imagenes(
            modelo,
            PeticionImagen(prompt=PROMPT_CARA.format(descriptor=descriptor), n=1),
            carpeta / "cara.png", serie=registro.serie, etiqueta=f"{tag}:cara",
        )
        url = asegurar_url(salidas[0]) if subir else str(salidas[0])
        cara = reg.Referencia(url=url, tipo="cara", creada_con=modelo,
                              notas="R-05 · original congelado, no se regenera")
        asset.referencias.append(cara)

    salidas = _generar_imagenes(
        modelo,
        PeticionImagen(prompt=PROMPT_HOJA.format(descriptor=descriptor, angulos=angulos),
                       referencias=[cara.url] if cara.url.startswith("http") else [], n=1),
        carpeta / "hoja.png", serie=registro.serie, etiqueta=f"{tag}:hoja",
    )
    asset.referencias.append(reg.Referencia(
        url=asegurar_url(salidas[0]) if subir else str(salidas[0]),
        tipo="hoja", creada_con=modelo, notas="fondo gris, multiángulo (R-05)"))

    registro.anadir(asset)
    reg.guardar(registro, ruta_registro)
    return asset


def crear_localizacion(base: Path, nombre: str, descriptor: str, *, mapa: str = "",
                       estado: str = "", modelo: str = "", version: int = 1,
                       subir: bool = True) -> reg.Asset:
    """Referencia de localización (R-04) y su mapa espacial vertical (R-06)."""
    base = Path(base)
    ruta_registro = base / "registry.json"
    registro = reg.cargar(ruta_registro)
    tag = Tag.nuevo("loc", registro.serie, nombre, version)
    modelo = modelo or elegir_modelo_imagen("localizaciones")
    carpeta = base / "assets" / str(tag).lstrip("@")
    carpeta.mkdir(parents=True, exist_ok=True)

    salidas = _generar_imagenes(
        modelo,
        PeticionImagen(prompt=PROMPT_LOCALIZACION.format(descriptor=descriptor, estado=estado),
                       aspect_ratio="9:16", n=1),
        carpeta / "loc.png", serie=registro.serie, etiqueta=f"{tag}:loc",
    )
    asset = reg.Asset(id=str(tag), descriptor=descriptor, version=version, mapa=mapa,
                      creado_con=modelo,
                      referencias=[reg.Referencia(
                          url=asegurar_url(salidas[0]) if subir else str(salidas[0]),
                          tipo="localizacion", creada_con=modelo,
                          notas="R-04 · manda en geometría, materiales y luz, "
                                "nunca en el encuadre")])
    registro.anadir(asset)
    reg.guardar(registro, ruta_registro)
    return asset


def prueba_en_movimiento(base: Path, tag: str, *, prompt: str = "", duracion: int = 3,
                         nivel: str = "borrador", modelo: str = "") -> tuple[Resultado, Path]:
    """R-12: ningún asset se aprueba sin verlo moverse, y en borrador.

    Genera un clip corto con las referencias del asset y lo pasa por el QC técnico.
    """
    base = Path(base)
    registro = reg.cargar(base / "registry.json")
    asset = registro.resolver(tag)
    urls = [u for u in asset.urls if u.startswith("http")]
    peticion = PeticionVideo(
        prompt=prompt or (
            f"{asset.descriptor} Slow push-in, the subject breathes and blinks, "
            "eyes wet and alive. "
            "No music — diegetic sound only. A change of face or wardrobe = failed take."
        ),
        duracion=duracion, resolucion="480p", imagenes=urls,
    )
    modelo = modelo or elegir_modelo(nivel, peticion)
    coste = estimar_coste(modelo, peticion)
    etiqueta = f"{tag}:movimiento"
    salida = base / "assets" / str(tag).lstrip("@") / "prueba_movimiento.mp4"
    solicitud = ev.reservar(coste, serie=registro.serie, plano=etiqueta, intento=1,
                            modelo=modelo, tipo_medio="video", prompt=peticion.prompt)
    try:
        resultado = obtener_proveedor(modelo).generar(peticion, salida)
    except Exception as e:
        ev.cerrar(solicitud, ok=False, coste_real=0.0, motivo=str(e)[:400])
        raise
    tecnico = sonda.sondear(resultado.ruta_local)
    ev.cerrar(solicitud, ok=True, coste_real=coste, salida=str(salida), tecnico=tecnico)
    informe = valida_toma(tecnico, duracion_pedida=duracion)
    ev.registrar("qc_veredicto", serie=registro.serie, plano=etiqueta, intento=1,
                 veredicto="aceptada" if informe.ok else "rechazada",
                 motivo="; ".join(i.codigo for i in informe.errores),
                 segundos=duracion, toma=str(salida))
    return informe, Path(resultado.ruta_local)


def aprobar(base: Path, tag: str, por: str, notas: str = "") -> reg.Asset:
    """CONTROL HUMANO 2 (casting). Deja rastro en el log de eventos."""
    base = Path(base)
    ruta_registro = base / "registry.json"
    registro = reg.cargar(ruta_registro)
    asset = registro.resolver(tag)
    asset.estado = "aprobado"
    reg.guardar(registro, ruta_registro)
    # Sin `plano=`: una aprobación de casting no es un plano y no debe aparecer al plegar.
    ev.registrar("aprobacion_humana", serie=registro.serie,
                 tipo="casting", por=por, referencia=tag, notas=notas)
    return asset
