# El inglés que entiende un modelo de vídeo

> **Procedencia.** **[P]** = documentación del proveedor (guía oficial de BytePlus u
> OpenAPI de fal, consultados el 2026-09-11 · `docs/conocimiento/04_apis_y_prompting.md`).
> **[V]** = validado en ≥2 producciones del top 30 de Higgsfield
> (`docs/conocimiento/00_investigacion_sistema.md`). **[H]** = hipótesis de trabajo: se
> confirma o se tira en la fase 5, con el ledger de rechazos delante.
>
> **Antes que esto, lee `00_contrato-de-api`**: ahí están los límites que la API acepta
> y cómo se citan las referencias. Esto es el estilo; aquello es el contrato.

El modelo no entiende intenciones. Entiende **sustantivos concretos, verbos de acción
física y relaciones espaciales**. Todo lo demás lo rellena inventando, y lo que
inventa cambia en cada tirada. Esa varianza es el coste del proyecto.

## 1. Actuación: verbos de tarea, no adjetivos de estado **[V]**

Un adjetivo emocional produce una mueca. Una tarea produce una interpretación.

| En vez de | Escribe |
|---|---|
| `She is nervous` | `She turns the ring on her finger twice, then stops` |
| `He is angry` | `He sets the glass down harder than he means to` |
| `She is exhausted` | `She holds the doorframe for a second before letting go` |
| `He looks suspicious` | `His eyes go to the door, then back, a half-beat late` |
| `She is in love` | `She keeps looking at his hands instead of his face` |
| `He is lying` | `He answers a fraction too fast and looks straight at her` |

La regla debajo: **una emoción se ve porque la tarea se ejecuta mal**. Escribe la
tarea y qué la estropea.

## 2. Estados, no transiciones **[V]**

El modelo resuelve las transiciones con morphing: la cara se derrite. Dale un estado
sostenido y deja que el cambio ocurra entre planos.

| En vez de | Escribe |
|---|---|
| `She becomes furious` | `Her jaw stays set the whole shot` |
| `He calms down` | `His breathing is already slow and even` |
| `Her smile fades` | `She is not smiling; her mouth is a flat line` |
| `He turns into someone else` | (fuera de cámara: dos planos y un barrido) |

## 3. Ojos vivos **[V]**

Un rostro sin esto sale de cera y es el fallo más frecuente en primeros planos:

```
Eyes wet and alive with catch-lights. She blinks twice in the shot; breath visible in
the shoulders.
```

## 4. Cámara: un movimiento, nombrado **[V]**

| Se traslada al vertical | No se traslada |
|---|---|
| `Slow push-in from medium to close-up, tripod` | `Handheld` (tiembla y rompe la zona segura) |
| `Slow pull-back revealing the desk, tripod` | `Lateral tracking shot` (el encuadre 9:16 no da recorrido) |
| `Slow tilt down from her eyes to her hands` | `Crane shot` · `Dolly zoom` |
| `Static, locked-off` | Dos movimientos en el mismo plano |

`tripod` o `locked-off` al final es barato y reduce el temblor que el modelo mete por
defecto. **[H]**

La guía oficial nombra ocho movimientos —push-in, pull-out, pan, tracking, orbit,
aerial, handheld, fixed— y repite la regla: **una sola instrucción de cámara**. En
vertical sólo se usan cuatro de los ocho. **[P]**

Para la velocidad, `slow` · `gentle` · `gradual`. **Nunca `fast`**: es la palabra que
más degrada la calidad según la guía oficial. **[P]**

## 5. Luz: una fuente, una dirección **[H, derivado de R-04]**

```
Cold north light from the tall window camera-left, single source, no fill.
```

Dos fuentes contradictorias hacen que la luz cambie entre fotogramas. Si la
localización ya define la luz, **repítela igual**, no la reinterpretes.

## 6. Física: qué pesa y qué se dobla **[H]**

El modelo delata la falsedad en los objetos, no en las caras:

```
Paper bends and settles; the wool coat holds its folds; the glass stays where she left it.
```

Tres cláusulas bastan. Nombra sólo lo que aparece y se mueve.

## 7. Audio **[V]**

Siempre, literalmente:

```
No music — diegetic sound only. Paper, breath, the radiator.
```

«No music» es la única prohibición que se escribe como prohibición en todo el sistema.
Las demás van como toma fallida.

## 8. Bloqueos positivos, y cuándo sí va un negativo **[V] + [P]**

Nombrar algo lo invoca. `No other people in the room` mete gente. La forma que
funciona es la condición de fallo:

```
A second person entering frame = failed take.
A different face between the first and last frame = failed take.
The envelope changing hands = failed take.
Text on the document readable = failed take.
```

Escribe los bloqueos **de los riesgos que has detectado en este plano**, no una lista
genérica copiada. Tres o cuatro, no diez. **[H]**

## 9. Primer fotograma sin ambigüedad **[V, de R-06]**

El fallo clásico: el plano empieza con la sala vacía y el personaje entra a los 2 s,
comiéndose la mitad de la toma.

```
FIRST FRAME
Nadia already holding the open envelope, both hands visible, papers squared on the desk.
```

«Already» y «both hands visible» hacen mucho trabajo: fijan que el estado inicial es
el de mitad de acción.

## 10. Palabras que degradan, aparte de los filtros **[P]**

No están prohibidas por política: empeoran el resultado.

| No escribas | Por qué |
|---|---|
| `fast`, `quickly`, `rapid` | La que más degrada. Rápido + cortes + escena cargada ≈ jitter |
| `cinematic`, `epic`, `amazing`, `stunning` | Vagas: el modelo rellena a su gusto y la varianza se paga en reintentos |
| `lots of movement`, `dynamic movement` | Sin sujeto ni dirección: no es una instrucción |

Si algo tiene que ir rápido, que sea **una sola** cosa del plano.

## 11. Vocabulario que dispara filtros

Hay una lista viva en `config/denylist.yaml` y el linter la comprueba. La forma de
esquivarla no es suavizar la palabra, es **cambiar el plano**: si la escena necesita
sangre, se ve la reacción de quien la mira.

## 12. Lo que no sabe hacer, pase lo que pase **[V]**

Ninguna redacción arregla esto. Si el plano lo pide, se devuelve al guionista:

- Texto legible en pantalla.
- Manos escribiendo o manipulando mecanismos finos.
- Más de tres personas con identidad.
- Una acción que se deshace (rebobinar, recomponer algo roto).
- Un cambio de vestuario o edad dentro del plano.
- Reflejos coherentes en espejos.
