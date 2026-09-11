# Una biblia, pieza a pieza

> **Procedencia.** El formato y las reglas citadas son **[V]**. El contenido del
> ejemplo es material de trabajo (**[H]**) para enseñar la forma, no un modelo a
> copiar: copiar este mundo es exactamente lo que las plataformas penalizan.

Idea de partida: *«Una jueza descubre que la coartada de su hija la incrimina a ella.»*

## Concepto

| Campo | Contenido | Por qué así |
|---|---|---|
| Logline | Una jueza descubre que la coartada de su hija lleva su propia firma. | Quién quiere qué y qué se lo impide, en una frase |
| Motor | Cada mentira que destapa la incrimina un poco más a ella. | Fuente de conflicto + coste que sube + no puede irse (es su hija) |
| Producibilidad | 9/10 · 2 personajes, 1 despacho, el conflicto se ve en una cara | 10 − 0 (2 personajes) − 0 (1 local) + 1 (cara) capado a 9 |
| Promesa del formato | Cada episodio revela una mentira nueva y quién la cubrió. | Por qué alguien ve el episodio 2 |
| Regla visual | El rojo sólo aparece cuando alguien miente. | Significado, no decoración |

## Personaje

```
@char_canon-rojo_Nadia_v1
Descriptor congelado:
  Woman in her early forties, short black hair, a thin scar through the left eyebrow,
  grey wool coat over a dark green shirt.
Anclas de identidad: cicatriz en la ceja izquierda · anillo de sello en el meñique
VOZ LOCK:
  AUDIO LOCK — low register, slow tempo, short sentences, northern accent.
Perfil de actuación:
  máscara pública: jueza impecable, nunca levanta la voz
  qué la rompe: que le mientan las personas a las que protege
  hábitos físicos: alinea los papeles contra la mesa cuando duda
  forma de caminar: pasos cortos, hombros altos
Objetivo de temporada: proteger a su hija sin romper la ley.
```

**Por qué cada pieza:**

- El descriptor es **visual y estable**: edad, pelo, una marca, ropa. Nada de
  «cansada» ni «elegante»: eso no son píxeles y el modelo se inventa una cara distinta
  en cada plano.
- Las **anclas** son lo que el QC comprueba. Dos o tres, pequeñas, permanentes, en
  sitios que salen en primer plano.
- El **VOZ LOCK** se repite palabra por palabra igual que el descriptor. Un cambio de
  voz entre planos se nota antes que un fallo de cara.
- El **hábito físico con su detonante** es lo que el director convierte en tarea:
  «alinea los papeles» es una acción rodable; «está nerviosa» no.

## Localización

```
@loc_canon-rojo_Despacho_v1
Descriptor congelado:
  A narrow municipal office: grey filing cabinets along the left wall, a steel desk
  under a tall window, cold north light on scuffed linoleum.
Mapa espacial vertical:
  Nadia a la izquierda del escritorio de acero, la ventana detrás de su hombro derecho,
  los archivadores fuera de cuadro a la izquierda de cámara. La cámara mira al norte.
Estados: día (luz fría de la ventana) · noche (fluorescente de techo, más verde)
```

- El descriptor manda en **geometría, materiales y luz**, nunca en el encuadre (R-04).
  Ni una palabra sobre planos ni sobre dónde se pone la cámara.
- El **mapa ancla las posiciones a objetos visibles** y fija el eje. Sin él, el
  contraplano sale invertido y la escena se rompe (R-06).
- Los **estados** son los que el guionista puede pedir sin inventar espacio nuevo.

## Estilo

```
STYLE PREFIX
Style: gritty 90s film look, vertical 9:16 composition, hard key light from a single
window, palette #101010 #8A8F98 #B3372B, fine grain, 85mm lens, tripod, tilts and
push-ins only.

CONSTRAINTS
Photoreal live-action. Identities, hair and wardrobe match their @tag references in
every shot. Faces blink and breathe; eyes wet and alive with catch-lights. Only
scripted lines are spoken, about four words per second, one second of clean silence at
the end. No music — diegetic sound only. Location references control geometry,
materials and light only; nothing added beyond what the reference shows. Subject kept
inside the vertical safe zone: eyes on the upper third, lower fifth clear for subtitles.

PALETA
dominante #101010 · secundaria #8A8F98 · acento #B3372B (aparece sólo cuando alguien
miente)
```

El STYLE PREFIX dice `vertical 9:16 composition` (el validador lo comprueba) y los
CONSTRAINTS dicen literalmente `No music`. Los dos bloques se copian **enteros** en
cada prompt de la serie, durante toda la temporada.

## Riesgos de producción

```
- Nada de manos escribiendo o firmando en primer plano: el modelo deforma los dedos.
- El texto de los documentos nunca se lee: papel del revés o fuera de foco.
- El cambio de día a noche del despacho se hace entre episodios, nunca dentro de un plano.
- Sara y Nadia no comparten cuadro: plano/contraplano siempre (vertical).
- Ninguna escena con más de dos personas identificables.
```

Esto no es papeleo defensivo: es donde se decide si el episodio cuesta 30 $ o 120 $.
Una biblia sin riesgos es una biblia que no ha mirado.

## Prueba de estrés (ep. 1)

| Campo | Contenido |
|---|---|
| Objetivo | Que Sara le diga dónde estaba el día 14 |
| Obstáculo | Sara tiene un motivo para mentir que Nadia no conoce |
| Táctica | Preguntar como madre, no como jueza |
| Giro | La firma del documento es real: Nadia firmó sin leer hace diez años |
| Cambio de valor | Seguridad → culpa |
| Punto más débil | El giro llega en el segundo 55 y deja poco aire al cliffhanger |

Señalar el punto débil es obligatorio. Si no encuentras ninguno, no has mirado.

## Los mismos apartados, mal

| Escrito así | Qué pasa después |
|---|---|
| `Descriptor: A tired, elegant judge who has seen too much.` | El modelo inventa una cara distinta en cada plano. `DESCRIPTOR_NO_LITERAL` en todos los prompts |
| `Anclas: su mirada` | No es un ancla: no se puede comprobar en un fotograma. `SIN_ANCLAS` |
| `Localización: un despacho, filmado en plano medio desde la puerta` | Encuadre dentro del descriptor: viola R-04 y el director hereda un plano decidido |
| `Paleta: tonos fríos y un rojo` | `PALETA_NO_HEX`. «Frío» no es un color |
| `Personajes: Nadia, Sara, el secretario, el fiscal, la vecina` | `DEMASIADOS_PERSONAJES`. Cinco castings, cinco hojas, cinco riesgos de identidad por plano |
| `Riesgos: ninguno conocido` | Aviso `SIN_RIESGOS`. Se descubren pagando |
| `Nombre: Sara Beltrán de la Cruz` | `NOMBRE_NO_ETIQUETABLE`: el nombre va dentro de un `@tag` |
