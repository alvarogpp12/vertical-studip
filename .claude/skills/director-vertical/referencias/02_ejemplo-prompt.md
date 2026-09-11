# Un prompt completo, línea a línea

> **Procedencia.** La estructura de bloques y las reglas citadas están validadas
> (**[V]**). Las decisiones concretas de redacción de este ejemplo son hipótesis de
> trabajo (**[H]**) hasta la fase 5.

Plano `s01_ep01_sh004` del shotlist:

```json
{"id": "s01_ep01_sh004", "beat": 2, "duracion": 6, "tamano": "primer plano",
 "camara": "push-in lento", "refs": ["@char_canon-rojo_Nadia_v1",
 "@loc_canon-rojo_Despacho_v1"], "dialogo": "Esta firma no es mia",
 "es_master": false}
```

## El prompt

```
# STYLE PREFIX (inmutable durante toda la serie)
Style: gritty 90s film look, vertical 9:16 composition, hard key light from a single
window, palette #101010 #8A8F98 #B3372B, fine grain, 85mm lens, tripod, tilts and
push-ins only.

SCENE CONTEXT
Midday. The office door is already closed when the shot starts. She has read the sheet
once already.

ACTIVE REFERENCES
@char_canon-rojo_Nadia_v1 — Woman in her early forties, short black hair, a thin scar
through the left eyebrow, grey wool coat over a dark green shirt.
@loc_canon-rojo_Despacho_v1 — A narrow municipal office: grey filing cabinets along the
left wall, a steel desk under a tall window, cold north light on scuffed linoleum.

LOCATION MAP
Nadia stands left of the steel desk, the tall window behind her right shoulder, the
filing cabinets out of frame camera-left. The camera looks north. She does not move
from that spot.

FIRST FRAME
Nadia already holding the single sheet at chest height, both hands visible, the open
envelope flat on the desk beside her.

SEGMENTS
0.0–2.0s she reads the signature line, eyes tracking left to right once.
2.0–4.5s she lowers the sheet and speaks.
4.5–6.0s she holds still, looking at the sheet, clean silence.

DIALOGUE
Nadia: "Esta firma no es mia"
Voice: AUDIO LOCK — low register, slow tempo, short sentences, northern accent.

PERFORMANCE
She reads the signature line, then lowers the sheet to chest height without letting go
of it. Her jaw stays set the whole shot. Eyes wet and alive with catch-lights; she
blinks twice.

CAMERA
Slow push-in from medium close-up to close-up, tripod. One move only.

LIGHTING
Cold north light from the tall window camera-right, single source, no fill.

PHYSICS
The sheet bends slightly under its own weight; the wool coat holds its folds; the
envelope stays flat where it is.

AUDIO
No music — diegetic sound only. Paper, breath, a radiator ticking off-screen.

CONSTRAINTS (inmutable)
Photoreal live-action. Identities, hair and wardrobe match their @tag references in
every shot. Faces blink and breathe; eyes wet and alive with catch-lights. Only
scripted lines are spoken, about four words per second, one second of clean silence at
the end. No music — diegetic sound only. Location references control geometry,
materials and light only; nothing added beyond what the reference shows. Subject kept
inside the vertical safe zone: eyes on the upper third, lower fifth clear for
subtitles.

POSITIVE LOCKS
A second person entering frame = failed take.
A different face between the first and last frame = failed take.
The sheet leaving her hands = failed take.
Text on the sheet readable = failed take.
```

## Por qué cada decisión

| Línea | Por qué |
|---|---|
| `SCENE CONTEXT`: «the door is already closed» | Cierra una puerta que el modelo abriría a media toma **[H]** |
| Los dos descriptores, enteros | R-02 **[V]**. Resumirlos cambia la cara: es el fallo número uno |
| `LOCATION MAP`: «the camera looks north» | Fija el eje. Sin esto, el plano siguiente puede salir invertido **[V]** |
| «She does not move from that spot» | Ancla la posición; el modelo tiende a hacer deambular **[H]** |
| `FIRST FRAME`: «already holding» | Evita el plano que empieza vacío **[V]** |
| `SEGMENTS` con 1 s final de silencio | R-09 **[V]**. 5 palabras = 1,25 s; el resto es lectura y cola |
| `PERFORMANCE`: tarea + estado + ojos | R-07 **[V]** |
| `CAMERA`: «One move only» | Redundante con el STYLE PREFIX, y aun así reduce el segundo movimiento **[H]** |
| `PHYSICS`: sólo tres objetos | Los que salen. Nombrar más invoca más **[V, de R-08]** |
| `POSITIVE LOCKS`: cuatro, específicos | Salen de los riesgos de **este** plano, no de una lista genérica |

## La versión mala del mismo plano

```
Style: gritty 90s look, vertical.

Nadia (@char_canon-rojo_Nadia_v1), a tired judge, reads a document in her office and
becomes furious when she realises the signature is hers. Close-up, camera pushes in
and then tilts down to her hands. She looks devastated. Same office as the previous
shot. No other people, no music, avoid weird hands.
```

Diagnóstico, en el orden en que lo canta el linter:

| Código | Qué pasa de verdad en la toma |
|---|---|
| `STYLE_PREFIX_AUSENTE` | El look deriva; el episodio no parece la misma serie |
| `CONSTRAINTS_AUSENTE` | Sin el bloque, no hay parpadeo, ni zona segura, ni «4 palabras/s» |
| `DESCRIPTOR_NO_LITERAL` | Cita el tag pero no el descriptor: la cicatriz desaparece y la cara cambia |
| `VOCABULARIO_EMOCION` (`tired`, `furious`, `devastated`) | Tres muecas encadenadas |
| — | `becomes furious` es una transición: morphing de cara |
| `CAMARA_MULTIPLE` | Push-in **y** tilt: el modelo hace una cosa rara a medio camino |
| `PROMPT_NO_ES_ISLA` (`same office as the previous shot`) | El modelo no tiene el plano anterior; se inventa una oficina |
| `PROHIBICION_SUELTA` (`no other people`, `avoid weird hands`) | Nombrar «people» y «hands» los invoca |
| — | Sin `FIRST FRAME`: la toma empieza con la mesa vacía |
| — | Sin mapa: el eje se rompe con el contraplano |

Mismo plano, mismo modelo, mismo coste por intento. La diferencia entre aceptar al
primero y gastar seis tiradas está entera en el texto.
