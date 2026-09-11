# El contrato que acepta el modelo

> **Procedencia.** **[P]** = documentación del proveedor (OpenAPI de fal consultado el
> **2026-09-11**, o guía oficial de BytePlus). **[V]** = validado en ≥2 producciones del
> top 30 de Higgsfield. **[H]** = hipótesis de trabajo, sin verificar.
> Detalle y fuentes: `docs/conocimiento/04_apis_y_prompting.md`.

Esto no es estilo: es lo que la API acepta. Saltárselo no da una toma peor, da un error
o una referencia ignorada que has pagado igual.

## Las referencias se citan **por posición** [P]

El modelo **no conoce nuestros `@tag`**. El contrato dice, literal:

> «Reference images to guide video generation. **Refer to them in the prompt as
> @Image1, @Image2, etc.**»

Las URLs que se mandan en `image_urls` se numeran por su orden en la lista. En el
prompt, cada una se cita con su número **pegada a un sustantivo**, y además se copia el
descriptor congelado palabra por palabra:

```
ACTIVE REFERENCES
The woman in @Image1, same person from another angle in @Image2 — @char_canon-rojo_Nadia_v1
Woman in her early forties, short black hair, a thin scar through the left eyebrow, grey
wool coat over a dark green shirt.
The room in @Image3 — @loc_canon-rojo_Despacho_v1
A narrow municipal office: grey filing cabinets along the left wall, a steel desk under a
tall window, cold north light on scuffed linoleum.
```

- Nuestro `@tag` sigue en el prompt **para el registro y el linter**, no para el modelo.
- El número te lo da la petición: no lo cuentes tú.
- Una etiqueta suelta, sin sustantivo delante, rinde peor. **[H]**
- Citar `@Image7` cuando sólo se mandan 3 imágenes es un error del linter
  (`CITA_FUERA_DE_RANGO`), y en producción es una referencia que no existe.

`@Video1` y `@Audio1` funcionan igual. Kling es distinto: usa `@Element1` sobre su campo
`elements`.

## Límites duros [P]

| | Seedance 2.0 | Seedance 2.5 | Kling v3 standard |
|---|---|---|---|
| Duración | **4–15 s** | **4–30 s** | 3–15 s |
| Imágenes | 9 | 30 | 1 inicial + `elements` |
| Vídeos / audios | 3 / 3 | 10 / 10 | — |
| Archivos totales | 12 | 50 | — |
| Resolución | 480p·720p·1080p·4k | 480p·720p·1080p | 720p |
| `aspect_ratio` | incluye **9:16** | incluye **9:16** | — |
| `negative_prompt` | **no existe** | **no existe** | **sí**, por defecto `blur, distort, and low quality` |
| Prompt | — | — | máx **2.500 caracteres** |
| Imagen inicial | opcional | opcional | **obligatoria** |

**Ningún modelo genera menos de 4 s** (3 en Kling). El máster de 1 s de R-06 se pide a 4
y se recorta en el montaje: el shotlist lo dice con `duracion: 4, duracion_montaje: 1`.

`generate_audio` **no cambia el precio** [P], así que va siempre activado.

## Negativos: depende del modelo [P]

- **Kling** tiene campo propio. Ahí van los artefactos, no dentro del prompt:
  `blur, distortion, watermark, text overlay, low quality, compression artifacts,
  flickering, inconsistent lighting, morphing faces, extra limbs, unnatural physics`
- **Seedance** no tiene campo. La guía oficial sí admite negativos dentro del prompt, y
  recomienda estos: `avoid jitter`, `avoid bent limbs`, `avoid temporal flicker`,
  `avoid identity drift`.

Esto **matiza R-08**: la regla del top 30 —los límites como «= failed take»— sigue
valiendo para lo narrativo (que no entre otra persona, que el prop no cambie de mano),
porque nombrar algo lo invoca. Para **artefactos técnicos**, el proveedor documenta que
el negativo funciona. Se usan los dos, cada uno en lo suyo. **[P] + [V]**

## Tiempos: etiquetas, no rangos **[H, pruebas de terceros]**

Los rangos tipo `0-5s:` se leen como texto y el modelo intenta honrarlos literalmente,
con salidas anómalas. Se escriben como etiquetas:

```
SHOTS
Shot 1: she reads the signature line, eyes tracking once.
Shot 2: she lowers the sheet and speaks.
Closing: she holds still, clean silence.
```

El linter rechaza los rangos (`RANGO_DE_TIEMPO`).

## Diálogo y lip-sync **[H, pruebas de terceros]**

- ~**20 palabras habladas por clip de 15 s**, **máximo 10 por línea**. Más largo degrada.
  *(Ojo: R-09 del proyecto calcula 4 palabras/s, o sea 60 por 15 s. Son cifras que no
  cuadran; hasta medirlo en la fase 5, quédate con la más conservadora.)*
- Una sola frase por intervención.
- Cláusula fija en todo plano con diálogo:
  `Realistic lip articulation, no exaggerated mouth opening, no head turns while speaking.`
- El lip-sync empeora cuando la cámara se mueve: los planos hablados van fijos o con un
  push-in muy lento.

## Longitud del prompt **[P, guía oficial]**

La guía oficial de Seedance apunta a **60–100 palabras** y a una fórmula de seis piezas:
sujeto, acción, entorno, cámara, estilo, restricciones. Nuestros prompts son más largos
porque cargan los bloques inmutables (STYLE PREFIX y CONSTRAINTS) que mantienen la serie
coherente.

**La tensión es real y está sin resolver.** Mientras no se mida en la fase 5: mantén los
bloques fijos, y que **todo lo demás** —contexto, acción, cámara, luz, física— quepa en
unas 100 palabras. Si te pasas, lo que sobra casi siempre es descripción decorativa.

## Palabras que degradan **[P, guía oficial]**

`fast` es la que más degrada: rápido + cortes rápidos + escena cargada ≈ jitter y
artefactos. Si algo tiene que ser rápido, que lo sea **una sola** cosa.

Vagas, y por tanto caras: `cinematic`, `epic`, `amazing`, `stunning`,
`lots of movement`. El modelo las rellena a su gusto y la varianza se paga en
reintentos. El linter las rechaza (`VOCABULARIO_QUE_DEGRADA`).

Para velocidades: `slow`, `gentle`, `gradual`.

## Lo que no estamos usando todavía **[P]**

Está en el contrato y podría bajar el coste o subir la calidad. Sin verificar:

- **Kling `elements`**: un personaje como imagen frontal + 1–3 ángulos, citado
  `@Element1`. Es exactamente nuestra hoja de personaje, nativa.
- **Kling `voice_id`**: voz ligada a un elemento. Es nuestro AUDIO LOCK, nativo.
- **Kling `multi_prompt` + `shot_type`**: varios planos en una sola llamada.
- **Seedance `task: extension`**: continuar un vídeo de referencia. Es la vía para
  encadenar planos manteniendo continuidad.
- **`bitrate_mode: high`**: mejor codificación sin coste de generación.
