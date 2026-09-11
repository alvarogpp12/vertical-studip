# Un episodio completo, comentado

> **Procedencia.** La estructura y las reglas citadas son **[V]**; el reparto concreto
> de este ejemplo es hipótesis (**[H]**) hasta medir retención.

Serie «Cañón Rojo». Assets registrados: `@char_canon-rojo_Nadia_v1`,
`@char_canon-rojo_Sara_v1`, `@loc_canon-rojo_Despacho_v1`.

## Beats

| # | Función | Qué pasa |
|---|---|---|
| 1 | gancho | Nadia lee una firma que es la suya en un documento que no ha firmado |
| 2 | desarrollo | Llama a Sara, su hija, para preguntarle por la fecha. Sara miente sobre dónde estaba |
| 3 | giro | La firma es real: Nadia sí firmó, hace diez años, sin leerlo |
| 4 | cliffhanger | Hay una segunda copia, y no está en el archivo |

Cada beat **cambia el valor de la escena**: seguridad → duda → culpa → amenaza. Un
beat que no cambia el valor es relleno y hay que cortarlo: cuesta dinero.

## Shotlist (75 s, 14 planos)

| orden | dur | tamaño | cámara | refs | diálogo | por qué |
|---|---|---|---|---|---|---|
| 1 | 1 (gen. 4) | plano general | fijo | loc | — | **Máster de geografía** (R-06). Sin diálogo. `duracion: 4, duracion_montaje: 1`: el modelo no genera menos |
| 2 | 3 | primer plano | push-in | char Nadia | — | **Gancho**: su cara al leer, antes de saber nada |
| 3 | 4 | inserto | fijo | loc | — | El papel en la mesa, la firma fuera de foco (no legible) |
| 4 | 5 | primer plano | fijo | char Nadia | «Esta firma no es mía» | 5 palabras = 2,25 s mínimo; 5 s da aire |
| 5 | 6 | plano medio | tilt | char Nadia | «Sara, ¿dónde estabas el catorce?» | Coge el teléfono; una acción, un movimiento |
| 6 | 5 | primer plano | fijo | char Sara | «En casa. Como siempre» | Contraplano, no two-shot (vertical) |
| 7 | 4 | primer plano | push-in | char Nadia | — | Reacción. Sabe que miente. Sin diálogo: la cara basta |
| 8 | 6 | plano medio | fijo | char Sara | «¿Por qué lo preguntas ahora?» | La táctica de Sara: devolver la pregunta |
| 9 | 5 | primer plano | fijo | char Nadia | — | Cuelga. Estado sostenido, no transición (R-07) |
| 10 | 7 | plano medio | pull-back | char Nadia + loc | — | Abre el archivador. **Giro**: encuentra el original |
| 11 | 6 | inserto | fijo | loc | — | La fecha: hace diez años. El papel, no el texto |
| 12 | 8 | primer plano | push-in | char Nadia | «Lo firmé yo. No lo leí» | 6 palabras = 2,5 s; 8 s deja peso al silencio |
| 13 | 8 | plano medio | tilt | char Nadia + loc | — | Busca la copia. No está. **Cliffhanger** |
| 14 | 7 | primer plano | fijo | char Nadia | — | Mira al archivador vacío. Corta sin resolver |

Suma: 75 s. Dentro de 61–90.

## Por qué funciona

- **El máster va primero y dura 1 s en pantalla.** Se generan 4 (el mínimo del modelo) y
  se recortan en el montaje. Evita que los trece siguientes se contradigan.
- **El gancho no explica nada.** Plano 2: una cara. El espectador se queda porque no
  sabe qué pasa, no porque se lo hayan contado.
- **Los insertos (3, 11) no muestran texto.** El modelo no sabe escribir; se ve el
  papel, no lo que pone. Eso es R-10 aplicado en la planificación, no en el prompt.
- **Plano/contraplano (5–6–7–8).** Nunca los dos en cuadro: en vertical salen diminutos.
- **Un solo movimiento por plano.** Mira la columna de cámara: nunca hay dos.
- **Los planos con diálogo tienen holgura.** Ninguno va justo de tiempo.
- **El giro (10–11–12) cuesta 21 s.** Es donde se gasta, porque es donde el episodio
  se gana o se pierde.
- **Termina en una cara, no en una acción.** Es lo que se puede rodar bien y lo que
  deja la pregunta abierta.

## La versión mala del mismo episodio

| orden | dur | cámara | diálogo | qué se rompe |
|---|---|---|---|---|
| 1 | 12 | travelling lateral | «Voz en off: Nadia llevaba diez años…» | `CAMARA_PROHIBIDA` · no hay gancho, hay contexto · el máster no existe |
| 2 | 3 | push-in + tilt | «Llevo diez años firmando lo que me ponen delante y nadie ha preguntado» | `CAMARA_MULTIPLE` · `DIALOGO_NO_CABE` (14 palabras en 3 s) |
| 3 | 10 | fijo | (Nadia y Sara discutiendo en plano) | Two-shot lateral: dos caras diminutas · dos personas discutiendo es de lo que peor hace el modelo |
| 4 | 6 | fijo | — | Nadia rompe el papel y luego lo recompone → acción que se deshace, imposible |

Cuatro planos, 31 s, cinco reglas rotas y dos planos que no se pueden rodar a ningún
precio. Y el episodio ni siquiera llega al mínimo de TikTok: `EPISODIO_CORTO`.

## Continuidad entre episodios

Si la memoria de serie dice que el ep01 cerró con «hay una segunda copia», el ep02
**abre recogiéndolo** en los primeros 10 s, y su cliffhanger es de otro tipo. Repetir
el mismo tipo dos veces seguidas es lo que hace que una serie se sienta una plantilla,
que es exactamente lo que las plataformas penalizan.
