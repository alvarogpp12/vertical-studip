# Contratos de API reales y guías de prompting de los proveedores
Fecha de consulta: **2026-09-11**. Todo lo de este documento sale de fuentes citadas,
no de memoria. Los esquemas están sacados del OpenAPI que publica fal, que es el
contrato que la API acepta de verdad:

```bash
curl -s "https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=bytedance/seedance-2.5/reference-to-video"
```

## Por qué existe este documento

La primera versión de las referencias de `.claude/skills/` se escribió extrapolando de
las 12 reglas del top 30 de Higgsfield. Al contrastarla con los contratos de API y las
guías de los proveedores aparecieron **contradicciones y errores de diseño**. Esta es
la corrección, con fuentes.

---

## 1. Seedance 2.5 · `bytedance/seedance-2.5/reference-to-video` (fal)

| Campo | Valores | Nota |
|---|---|---|
| `prompt` | **requerido** | — |
| `image_urls` | hasta **30** imágenes, 30 MB c/u | «Refer to them in the prompt as **@Image1, @Image2**, etc.» |
| `video_urls` | hasta **10**, 1,8–30,2 s c/u, 30,2 s en total | `@Video1`… |
| `audio_urls` | hasta **10**, 1,8–30,2 s c/u | `@Audio1`… |
| Total de archivos | **50** entre las tres modalidades | |
| `duration` | `auto` o **4–30** segundos | **El mínimo es 4 s** |
| `resolution` | `480p` · `720p` · `1080p` | |
| `aspect_ratio` | `auto`·`21:9`·`16:9`·`4:3`·`1:1`·`3:4`·**`9:16`** | |
| `generate_audio` | `true` por defecto | «The cost of video generation is **the same** regardless of whether audio is generated or not» |
| `bitrate_mode` | `standard` · `high` | Palanca de calidad sin coste de generación |
| `task` | `reference` · `editing` · `extension` | `extension` continúa un vídeo de referencia |
| `seed` | opcional | «results may still vary slightly even with the same seed» |
| Negativo | **no existe** `negative_prompt` | |

Requisito: **al menos una imagen o un vídeo de referencia.**

## 2. Seedance 2.0 · `bytedance/seedance-2.0/reference-to-video` (fal)

Igual que 2.5 salvo:

| Campo | Valores |
|---|---|
| `duration` | `auto` o **4–15** s |
| `image_urls` | hasta **9** |
| `video_urls` | hasta **3**, 2–15 s en total |
| `audio_urls` | hasta **3**, 15 s en total |
| Total de archivos | **12** |
| `resolution` | `480p`·`720p`·`1080p`·**`4k`** |

## 3. Kling v3 standard · `fal-ai/kling-video/v3/standard/image-to-video` (fal)

Es un modelo distinto en casi todo, y tiene funciones que no estábamos usando:

| Campo | Valores | Nota |
|---|---|---|
| `start_image_url` | **requerido** | Kling no hace texto→vídeo en este endpoint |
| `prompt` | máx **2.500 caracteres** | |
| `negative_prompt` | **existe**, por defecto `"blur, distort, and low quality"` | |
| `elements` | personajes u objetos: `frontal_image_url` + **1–3 `reference_image_urls` desde otros ángulos** | «Reference in prompt as **@Element1, @Element2**» |
| `elements[].voice_id` | voz ligada al elemento | Las referencias a ese elemento usan esa voz |
| `duration` | **3–15** s (string) | |
| `multi_prompt` + `shot_type` | vídeo multiplano en una sola llamada | `customize` o `intelligent` |
| `cfg_scale` | 0,5 por defecto | Cuánto se ciñe al prompt |
| `end_image_url` | opcional | Último fotograma |

**`elements` es literalmente nuestra hoja de personaje** (frontal + multiángulo) y
**`voice_id` es literalmente nuestro AUDIO LOCK**, los dos como función nativa de la API.

## 4. Guía oficial de prompting de Seedance (BytePlus)

Existe: «Dreamina Seedance 2.0 series prompt guide», `docs.byteplus.com/en/docs/ModelArk/2222480`.
La página es una SPA y no se puede leer con un fetch simple; lo de abajo viene de
análisis que la citan, así que es **de segunda mano** hasta que se lea en la consola.

- Fórmula de 6 pasos: `[Sujeto], [Acción], en [Entorno], cámara [Movimiento], estilo
  [Estilo], evitar [Restricciones]`, con una longitud objetivo de **60–100 palabras**.
- **Una sola instrucción de cámara** por prompt.
- Velocidades como «slow, gentle, gradual», no especificaciones técnicas.
- **«fast» es la palabra que más degrada la calidad.** Movimiento rápido + cortes
  rápidos + escena cargada ≈ jitter y artefactos garantizados.
- Palabras peligrosas por vagas: `cinematic`, `epic`, `amazing`, `lots of movement`.
- Negativos que la guía sí recomienda: `avoid jitter`, `avoid bent limbs`,
  `avoid temporal flicker`, `avoid identity drift`.
- Seedance «entiende descripciones de ritmo humanas, no jerga fotográfica».

## 5. Prompting de diálogo (pruebas de terceros, no oficial)

De `ambienceai.com/tutorials/seedance-prompting-guide`, **pruebas propias del autor**:

- **20 palabras habladas por clip de 15 s**; **máximo 10 por línea**. Más largo degrada
  en «phoneme soup».
- Una sola frase por intervención; las peleas de diálogo se parten con acción.
- Cláusula de lip-sync: `realistic lip articulation, no exaggerated mouth opening, no
  head turns while speaking`.
- «lip sync degrades as the camera moves» → plano medio corto con cámara fija.
- **Los rangos de tiempo tipo `0-5s:` se leen como texto y el modelo intenta
  honrarlos literalmente**, con salidas anómalas. Usar etiquetas: `Shot 1: … Shot 2: …
  Closing: …`.
- Supresores en línea aparte: `- No music, no library audio, no voiceover narration,
  no on-screen text, no subtitles, no logo`.
- Las etiquetas `@ImageN` van **pegadas a un sustantivo**; sueltas rinden peor.

## 6. Prompting de Kling (pruebas de terceros)

De `ambienceai.com/tutorials/kling-prompting-guide` y `atlascloud.ai`, **ninguna
atribuida a documentación oficial de Kuaishou**:

- Fórmula: `[Tipo de plano] de [sujeto] [acción], [entorno], [movimiento de cámara],
  [luz/tono], [estilo]`.
- **60–100 palabras rinde mejor que agotar los 2.500 caracteres.**
- Negativo recomendado: `blur, distortion, watermark, text overlay, low quality,
  compression artifacts, flickering, inconsistent lighting, morphing faces, extra
  limbs, unnatural physics`.
- Kling 3.0 mapea el negativo semánticamente: mejor en su campo que dentro del prompt.

---

## 7. Lo que esto rompe de nuestro diseño

| Hallazgo | Fuente | Qué estaba mal |
|---|---|---|
| Las referencias se citan **`@Image1`/`@Video1`/`@Audio1` por posición** | esquema fal | Nuestros prompts citaban `@char_serie_Nombre_v1`, que el modelo **no conoce**. Mandábamos `image_urls` sin citarlas: el modelo podía ignorarlas |
| **Duración mínima 4 s** | esquema fal | El máster de 1 s de R-06 **no se puede generar** con Seedance |
| Kling tiene `negative_prompt` | esquema fal | `PeticionVideo` no tenía el campo: perdíamos una palanca documentada |
| Kling tiene `elements` (frontal + multiángulo) y `voice_id` | esquema fal | Es nuestra hoja de personaje y nuestro AUDIO LOCK, nativos, sin usar |
| Kling exige `start_image_url` | esquema fal | El router podía elegir Kling para un plano sin referencias |
| Prompt de Kling: 2.500 caracteres | esquema fal | Sin validar |
| Guía oficial: 60–100 palabras, negativos `avoid X` | BytePlus (2.ª mano) | Nuestro prompt de ejemplo eran ~300 palabras y R-08 prohibía los «avoid» |
| `0-5s:` se honra literalmente y degrada | ambienceai | Nuestro bloque `SEGMENTS` usaba exactamente ese formato |
| «fast» es la palabra que más degrada | guía oficial (2.ª mano) | No estaba en la denylist |
| `generate_audio` no cambia el precio | esquema fal | Confirma la decisión de dejarlo siempre activo |
| Seedance 2.0 llega a 4k y 2.5 a 1080p | esquema fal | La decisión «generar a 720p máx» sigue siendo razonable por coste, pero el motivo escrito («no genera 1080p nativo») ya no es exacto |

## 8. Lo que sigue sin verificar

- La guía oficial de BytePlus, **leída directamente**: la página no se deja leer por
  fetch. Hay que abrirla en la consola y contrastar los puntos de la sección 4.
- **Ninguna llamada real todavía.** Todo lo de arriba es el contrato declarado, no el
  comportamiento observado. `showrunner humo --video` es el primer paso.
- Precios: los de `config/modelos.yaml` siguen `estimado`/`verificar` (issue #4).
- Si `@Image1` funciona mejor pegado a un sustantivo, y cuánto: hipótesis de terceros.
- Si el mínimo de 4 s se puede esquivar generando 4 s y recortando a 1 s en montaje.

## Fuentes

- fal OpenAPI (contrato real, consultado el 2026-09-11):
  `https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=bytedance/seedance-2.5/reference-to-video`,
  `…seedance-2.0/reference-to-video`, `…fal-ai/kling-video/v3/standard/image-to-video`
- BytePlus ModelArk · Dreamina Seedance 2.0 series prompt guide — https://docs.byteplus.com/en/docs/ModelArk/2222480
- BytePlus ModelArk · Dreamina Seedance 2.5 tutorial — https://docs.byteplus.com/en/docs/ModelArk/2607688
- fal · Seedance 2.5 reference-to-video — https://fal.ai/models/bytedance/seedance-2.5/reference-to-video
- Ambience AI · Seedance prompting guide (pruebas propias) — https://www.ambienceai.com/tutorials/seedance-prompting-guide
- Ambience AI · Kling prompting guide (pruebas propias) — https://www.ambienceai.com/tutorials/kling-prompting-guide
- Apiyi · interpretación de la guía oficial de Seedance 2.0 — https://help.apiyi.com/en/seedance-2-0-prompt-guide-video-generation-camera-style-tips-en.html
- Atlas Cloud · Kling AI video prompt guide — https://www.atlascloud.ai/blog/guides/kling-ai-video-prompt-guide
