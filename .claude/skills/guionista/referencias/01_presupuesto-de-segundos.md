# El presupuesto de segundos

> **Procedencia.** **[P]** = contrato del proveedor (OpenAPI de fal, 2026-09-11 ·
> `docs/conocimiento/04_apis_y_prompting.md`). **[V]** = validado en el top 30 y en las
> políticas de plataforma. **[H]** = hipótesis: el reparto por tramos y los números de
> planos se corrigen con la retención real en la fase 4.

90 segundos son unos 220 segundos generados con reintentos, y eso son entre 20 y 45 $.
Cada segundo que repartes mal se paga tres veces: en generación, en QC y en montaje.

## Reparto de un episodio de 75 s **[H]**

| Tramo | Seg. | Planos | Qué tiene que pasar |
|---|---|---|---|
| Máster de geografía | 1 | 1 | Dónde está todo. Sin diálogo. Se **genera a 4 s** y se monta a 1 **[P]** |
| Gancho | 3 | 1 | Una cara en plena reacción, o una frase que no se puede ignorar |
| Planteamiento | 18 | 3–4 | Quién quiere qué y qué se lo impide |
| Escalada | 25 | 4–6 | La táctica falla; sube el coste de fallar |
| Giro | 15 | 2–3 | Lo que el espectador creía era falso |
| Cliffhanger | 13 | 2 | Se abre algo y se corta antes de resolver |

Total: 12–17 planos. Fuera de ese rango, revisa: con menos de 10 los planos son muy
largos y el modelo se desordena; con más de 20 el episodio va a tirones y el coste
por segundo aceptado se dispara.

## Duración de un plano

**El mínimo que genera el modelo son 4 segundos** (3 en Kling) **[P]**. Todo lo que dure
menos en pantalla se genera a 4 y se recorta con `duracion_montaje`. Eso significa que
**un plano de 1 s cuesta lo mismo que uno de 4**: los planos muy cortos no son gratis,
son caros por segundo usado.

| En pantalla | Se genera | Cuándo |
|---|---|---|
| 1 s | 4 s | Sólo el máster de geografía |
| 2–3 s | 4 s | Reacción, inserto, corte rápido en la escalada. Úsalos con cabeza |
| 4–6 s | 4–6 s | Lo normal. Una frase y su reacción |
| 7–8 s | 7–8 s | Dos frases o una acción con principio y final |
| > 8 s | igual | Casi nunca. El modelo pierde coherencia y un fallo tardío tira toda la toma |

**Regla económica:** un fallo a los 7 s de un plano de 8 s tira 8 s de generación. Dos
planos de 4 s salen igual de caros de generar y la mitad de caros de repetir. Ante la
duda, parte.

## La cuenta del diálogo **[V, R-09]**

> **Contradicción abierta.** R-09 del proyecto calcula 4 palabras por segundo, o sea 60
> en un clip de 15 s. Las pruebas de terceros que documentan Seedance hablan de **20
> palabras habladas por 15 s y máximo 10 por línea**, y dicen que por encima el audio
> degrada. Son cifras muy distintas y **no está medido cuál vale**. Hasta la fase 5,
> quédate corto: una frase por plano, y si dudas, parte. **[H]**

```
duración mínima = palabras / 4 + 1 segundo de cola limpia
```

| Línea | Palabras | Mínimo |
|---|---|---|
| «No» | 1 | 1,25 s → usa 2 s |
| «Esta firma no es mía» | 5 | 2,25 s → usa 3 s |
| «No pienso firmar ese papel, y lo sabes» | 8 | 3,0 s → usa 4 s |
| «Llevo diez años firmando lo que me ponen delante y nadie ha preguntado nunca» | 14 | 4,5 s → **pártela en dos planos** |

El segundo de cola no es adorno: es lo que permite cortar limpio. Sin él, el montaje
corta sobre la última sílaba y suena a error.

## Cuándo partir un plano

1. El diálogo no cabe → parte por la coma.
2. Hay dos acciones físicas → un plano cada una.
3. Cambia quién habla → plano/contraplano, no un two-shot.
4. Cambia el estado de un prop → el cambio ocurre en el corte, no en cámara **[V, R-10]**.

## Diálogo a dos en vertical **[V]**

En 9:16 un two-shot lateral deja dos caras diminutas y los ojos fuera del tercio
superior. Las dos formas que funcionan:

- **Plano / contraplano**: A habla (primer plano), B responde (primer plano). Cada
  cambio es un plano nuevo del shotlist.
- **Escalonado en profundidad**: A en primer término desenfocado a un lado, B nítido
  al fondo. Sirve para no cortar tanto, pero fija el eje en el mapa o se invierte.

## El gancho de 0–3 s **[V]**

Lo que el espectador ve **antes** de decidir si sigue. Tres formas que funcionan:

| Forma | Ejemplo |
|---|---|
| Rostro en plena reacción | Ella mira algo fuera de campo y deja de respirar |
| Frase de impacto, sin contexto | «Esta firma no es mía» |
| Revelación visual | El sobre abierto, con su nombre |

Lo que **no** es un gancho: un establecimiento de la localización, un título, una voz
en off explicando el mundo, o un personaje entrando por una puerta.

## El cliffhanger **[V]**

Cuatro tipos, y siempre **antes** de resolver:

| Tipo | Qué se abre |
|---|---|
| Revelación | Se sabe algo que cambia todo lo anterior |
| Amenaza | Alguien va a perder algo concreto, pronto |
| Descubrimiento | Aparece un objeto o un dato que no encaja |
| Decisión | El personaje va a elegir y no se ve qué elige |

No repitas tipo dos episodios seguidos: la memoria de serie te dice cuáles se han
usado ya.
