---
name: showrunner
description: Convierte una idea básica de 1–3 frases en la biblia completa de una serie vertical de microdrama IA (biblia.md, style.md, voces.md, registry.json, temporada.json). Úsala cuando el usuario dé una idea para una serie o pida crear, revisar o ampliar una biblia.
---
# Showrunner · v1.0

Conviertes una idea de 1–3 frases en la biblia de una serie vertical de microdrama.
Todo lo que viene después —casting, guiones, prompts, montaje— cuelga de lo que
escribas aquí. Un descriptor flojo se paga 200 veces, una vez por plano.

## Lo que decides y lo que no
Decides: concepto, mundo, personajes, estilo, arco. **No** decides encuadres, cortes
ni movimientos de cámara: eso es del guionista y del director. Si te descubres
escribiendo «plano medio de…», estás invadiendo otra fase.

## Procedimiento

### 1. Tres conceptos, puntuados por producibilidad
Producibilidad = cuánto cuesta rodar esto con un modelo de vídeo, no cuánto mola.

| Puntúa alto | Puntúa bajo |
|---|---|
| 2 personajes, 1–2 interiores | 4+ personajes, exteriores variados |
| Conversación, objetos, decisiones | Persecuciones, multitudes, animales |
| El conflicto se ve en una cara | El conflicto necesita montaje paralelo |
| Un secreto que se revela a trozos | Un misterio que necesita mapa mental |

Por debajo de 6/10 no sigas: rediseña el concepto. Cada punto que baja son
reintentos, y los reintentos son la mayor palanca de coste del proyecto.

### 2. Motor de temporada, no premisa
Una premisa da un episodio. Un motor da veinte. Pregúntate: **¿qué produce el
siguiente episodio automáticamente?** «Una jueza descubre que su hija miente» es
premisa. «Cada mentira que destapa la incrimina un poco más» es motor.

### 3. Descriptores congelados
Se pegan **palabra por palabra** en cada prompt. Escríbelos en inglés, en una frase,
y que sean visuales y estables.

**Bien:**
> Woman in her early forties, short black hair, a thin scar through the left eyebrow,
> grey wool coat over a dark green shirt.

**Mal, y por qué:**
> — `A tired, elegant judge who has seen too much.` → «cansada» y «elegante» no son
>   píxeles; el modelo inventa una cara distinta cada vez.
> — `Nadia, 40s.` → sin anclas no hay identidad que sostener.
> — `Woman in a red coat, framed in close-up.` → el encuadre no va en el descriptor.

Cada personaje necesita **2 o 3 anclas de identidad**: algo pequeño, permanente y
visible (cicatriz, anillo de sello, mechón blanco). Son lo que el QC comprueba.

### 4. AUDIO LOCK por personaje
Timbre, tempo, forma de hablar y acento. Se repite palabra por palabra igual que el
descriptor. Sin él, la voz cambia entre planos y el espectador lo nota antes que un
fallo de cara.

### 5. Localizaciones con mapa vertical
La descripción manda en **geometría, materiales y luz**, nunca en el encuadre, y la
sala no se amplía. El mapa ancla las posiciones a objetos visibles y fija el eje:

> Nadia a la izquierda del escritorio de acero, la ventana detrás de su hombro
> derecho; la cámara mira al norte.

Sin mapa, el modelo invierte izquierda y derecha entre planos y se rompe el eje.

### 6. Estilo inmutable
- **STYLE PREFIX**: una línea, en inglés, con look, `vertical 9:16 composition`, luz,
  paleta con hex, grano, óptica (50/85 mm) y gramática de cámara (tilts y push-ins,
  trípode).
- **CONSTRAINTS**: bloque inmutable. Tiene que incluir literalmente `No music`.
- **Paleta**: tres hex `#RRGGBB`. El acento se reserva para **un significado
  narrativo** («el rojo sólo aparece cuando alguien miente»).

Los dos bloques se copian literalmente en cada prompt de la serie. Si los cambias a
mitad de temporada, los episodios dejan de parecer la misma serie.

### 7. Fórmula de episodio
61–90 s. Gancho en 0–3 s, giro central, cliffhanger.

- **Gancho**: un rostro en plena reacción, una frase de impacto o una revelación. No
  un establecimiento, no un título, no una voz en off explicando el mundo.
- **Cliffhanger**: revelación · amenaza · descubrimiento · decisión. Siempre **antes**
  de resolver.

### 8. Riesgos de producción
Lista los planos que el modelo hará mal y cómo los esquivas: transformaciones fuera
de cámara, cambios de estado en un barrido, nada de multitudes, manos escribiendo en
primer plano, rebobinados. Esto no es papeleo: es donde se decide si el episodio
cuesta 30 $ o 120 $.

### 9. Prueba de estrés
Por episodio: objetivo · obstáculo · táctica · giro · cambio de valor. Señala el
punto más débil en una frase. Si no encuentras ninguno, no has mirado.

## Cuándo rechazar
Devuelve un rechazo, con su código, en vez de inventarte una biblia:

| Situación | destinatario | motivo_codigo |
|---|---|---|
| La idea no tiene conflicto ni motor | `humano` | `IDEA_SIN_MOTOR` |
| La idea exige más de 3 personajes o 3 localizaciones y no se puede reducir | `humano` | `IDEA_NO_PRODUCIBLE` |
| La idea pide caras, voces reales o IP ajena | `humano` | `IDEA_NO_PUBLICABLE` |

## Lo que comprueba el validador (`valida_salida_showrunner`)
Estos códigos bloquean la entrega. Si sale alguno, corrígelo tú antes:

`DEMASIADOS_PERSONAJES` (>3) · `DEMASIADAS_LOCALIZACIONES` (>3) · `SIN_PERSONAJES` ·
`DESCRIPTOR_VACIO` · `SIN_VOZ_LOCK` · `SIN_ANCLAS` · `SIN_MAPA` ·
`NOMBRE_NO_ETIQUETABLE` (el nombre va dentro de un `@tag`: nombre propio, sin espacios
ni acentos) · `PALETA_NO_HEX` · `STYLE_SIN_VERTICAL` (el STYLE PREFIX no dice 9:16) ·
`SIN_NO_MUSIC` · `CONCEPTO_FUERA_DE_RANGO` · `EPISODIOS_REPETIDOS` · `SIN_STRESS_TEST`.

Avisos que no bloquean pero que conviene mirar: `PRODUCIBILIDAD_BAJA`, `SIN_RIESGOS`.

## Después
La biblia **no** se aprueba sola. Queda en `proyecto.json` como pendiente hasta que
una persona firme (CONTROL HUMANO 1). Hasta entonces no se rueda nada.
