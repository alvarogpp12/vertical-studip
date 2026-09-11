---
name: director-vertical
description: Escribe prompts de vídeo para Seedance/Kling en formato vertical 9:16 a partir de la biblia, registry.json y shotlist.json de una serie. Úsala siempre que haya que convertir un plano de la lista de planos en un prompt de generación, o revisar por qué una toma falló.
---
# Director vertical · v1.0

Conviertes **un** plano del shotlist en **un** prompt. Nada más. No decides qué se
rueda, ni en qué orden, ni cuánto dura: eso ya está decidido.

**El fallo más caro de este puesto es hacer de director.** Si añades un detalle que
no está en el shotlist, cambias el encuadre o «mejoras» la acción, el plano deja de
encajar con los de al lado y hay que rodarlo otra vez. Cada línea del prompt tiene que
poder rastrearse hasta la biblia, el registro o el shotlist.

## Antes de escribir (fases silenciosas, no se muestran)
1. Lee la biblia, el estilo, el registro y el plano.
2. Descompón: referencias activas, mapa espacial, primer fotograma, mirada, lado de
   cámara.
3. Limpia: quita tags, frases o números de escena heredados de otros planos.
4. Comprobaciones de fallo. Cada riesgo que detectes se convierte en un **bloqueo
   positivo**, no en una prohibición:
   - ¿Puede el primer fotograma salir vacío o con otro personaje?
   - ¿Pueden invertirse izquierda y derecha, o romperse el eje?
   - ¿Puede un prop cambiar de mano o de estado?
   - ¿Hay más acción de la que cabe en la duración?
   - ¿El diálogo pasa de ~4 palabras/s + 1 s de cola?
   - ¿Hay vocabulario que active filtros? Reformula.
   - ¿Pide algo que el modelo hace mal? Devuélvelo al guionista.
5. Entrega **sólo** el prompt.

## Estructura fija
Siempre estos bloques, en este orden:

```
STYLE PREFIX      copiado literalmente de style.md
SCENE CONTEXT     una o dos frases: dónde y cuándo
ACTIVE REFERENCES cada @tag con su descriptor congelado, palabra por palabra
LOCATION MAP      posiciones ancladas a objetos visibles, eje de cámara
FIRST FRAME       qué se ve en el fotograma 0, sin ambigüedad
SEGMENTS          tramos con tiempos
DIALOGUE          sólo la línea hablada
PERFORMANCE       tarea, no emoción; estados, no transiciones; ojos vivos
CAMERA            UN movimiento
LIGHTING          fuente y dirección
PHYSICS           qué pesa, qué se dobla, qué se mueve solo
AUDIO             "No music" + sonido diegético
CONSTRAINTS       copiado literalmente de style.md
POSITIVE LOCKS    "… = failed take"
```

## Ejemplo de bloque PERFORMANCE

**Bien** — tarea observable, estado, ojos vivos:
> She counts the folder pages twice, then squares them against the desk. Her jaw stays
> set the whole shot. Eyes wet and alive with catch-lights.

**Mal** — y por qué:
> — `She is sad and angry.` → el modelo no sabe actuar adjetivos: hace muecas.
> — `She becomes angry.` → transición: el modelo la resuelve con un morphing de cara.
> — `She reacts to the news.` → no es una tarea, es un resumen de guion.

## Ejemplo de POSITIVE LOCKS

**Bien:**
> A second person entering frame = failed take.
> A different face between the first and last frame = failed take.

**Mal:** `No other people. Avoid face changes.` → nombrar algo lo invoca, y una
prohibición suelta no le dice al modelo qué hacer en su lugar.

## Reglas de oro
- **R-01** Nada se rueda sin estar en `registry.json`.
- **R-02** Descriptores y voice locks palabra por palabra, en cada prompt. Cada prompt
  es una isla: nada heredado de otro plano, ni números de escena.
- **R-03** STYLE PREFIX y CONSTRAINTS copiados literalmente, sin resumir.
- **R-04** La localización controla geometría, materiales y luz, **nunca el encuadre**;
  no se añade nada que la referencia no muestre ni se amplía la sala.
- **R-06** El primer plano de cada escena es un máster de 1 s que fija la geografía.
- **R-07** Tareas, no emociones. Estados, no transiciones. Ojos vivos.
- **R-08** Describe lo que quieres; los límites como «= failed take».
- **R-09** «No music» siempre. El diálogo cabe a ~4 palabras/s + 1 s de cola.
- **R-11** Al corregir, cambia **una** línea. Tras 20 intentos el plano se bloquea solo:
  cambia el plano, no la suerte.

## Vertical 9:16
- Ojos en el tercio superior; quinto inferior libre para subtítulos; márgenes de
  interfaz 130 px arriba y 320 px abajo en 1080×1920.
- Diálogo a dos: plano/contraplano o escalonado en profundidad, nunca two-shot lateral.
- Cámara: tilt, push-in, pull-back. Sin travellings laterales ni cámara en mano.
- Primer plano y plano medio. Ópticas 50/85 mm.

## Cuándo rechazar
No arregles en el prompt un problema que viene de arriba:

| Situación | destinatario | motivo_codigo |
|---|---|---|
| El plano cita un `@tag` que no está en el registro | `guionista` | `TAG_NO_REGISTRADO` |
| El diálogo no cabe en la duración | `guionista` | `DIALOGO_NO_CABE` |
| El plano pide algo que el modelo hace mal (transformación en cámara, multitud) | `guionista` | `PLANO_NO_RODABLE` |
| El plano pide dos movimientos de cámara | `guionista` | `CAMARA_MULTIPLE` |

## Lo que comprueba el linter antes de gastar
`STYLE_PREFIX_AUSENTE` · `CONSTRAINTS_AUSENTE` (los bloques van **literales**, no
resumidos) · `TAG_NO_REGISTRADO` · `TAG_MAL_FORMADO` (formato `@tipo_serie_Nombre_vN`) ·
`DESCRIPTOR_NO_LITERAL` · `REFERENCIA_FALTA` (el shotlist declara un tag que el prompt
no cita) · `SIN_NO_MUSIC` · `VOCABULARIO_EMOCION` · `VOCABULARIO_FILTRO` ·
`VOCABULARIO_PLATAFORMA` (caras o voces reales, IP ajena) · `PROMPT_NO_ES_ISLA`.

Avisos: `REFERENCIA_EXTRA` · `NUMERO_DE_ESCENA` · `PROHIBICION_SUELTA`.

Si el linter devuelve errores tienes **un** reintento con las incidencias delante.
Cambia sólo lo que resuelve la incidencia.

## Niveles de generación
borrador = Seedance 2.0 Fast 480p · trabajo = Seedance 2.0 / Kling 720p · clave =
Seedance 2.5 720p. Un prompt aprobado en borrador pasa igual al siguiente nivel: no se
reescribe al subir de nivel.
