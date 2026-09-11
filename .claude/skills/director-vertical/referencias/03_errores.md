# Catálogo de fallos: síntoma en la toma → línea culpable → arreglo

> **Procedencia.** Los síntomas y las reglas son **[V]**; los arreglos concretos son
> hipótesis (**[H]**) hasta que el ledger de rechazos de la fase 5 los confirme.
> **Guarda cada rechazo con su motivo**: esta tabla se corrige con esos datos, no con
> opiniones.

**R-11 manda en todo esto: al corregir se cambia UNA línea.** Cambiar tres a la vez
te deja sin saber cuál funcionó, y la siguiente vez vuelves a empezar de cero.

| Síntoma | Causa habitual | Arreglo (una línea) |
|---|---|---|
| La cara cambia entre el principio y el final | El descriptor no va literal, o falta un ancla | Pega el descriptor congelado entero, con sus anclas |
| Sale otra persona | El descriptor es genérico («a woman in her forties») | Añade las 2–3 anclas de identidad |
| La toma empieza con la sala vacía | No hay `FIRST FRAME` | Añádelo con «already» y el objeto en la mano |
| Entra alguien a media toma | Falta el bloqueo positivo | `A second person entering frame = failed take.` |
| Izquierda y derecha se invierten en el contraplano | No hay `LOCATION MAP` o no fija el eje | Añade «the camera looks north» y la posición anclada a un objeto |
| La sala es más grande de lo que muestra la referencia | El prompt describe espacio que la referencia no tiene | Quita esa frase; R-04: la referencia manda en geometría |
| Muecas en lugar de interpretación | Vocabulario de emoción | Sustituye el adjetivo por una tarea física |
| La cara se derrite a media toma | Una transición (`becomes`, `turns into`, `fades`) | Reescríbelo como estado sostenido |
| Rostro de cera, no parpadea | Falta la cláusula de ojos vivos | `Eyes wet and alive with catch-lights; she blinks twice.` |
| El movimiento de cámara hace algo raro a mitad | Dos movimientos en un plano | Deja uno; el otro es otro plano |
| Tiembla la imagen | El modelo mete cámara en mano por defecto | Añade `tripod` o `locked-off` |
| El diálogo va acelerado o se corta | Más palabras de las que caben | Parte el plano; no aceleres la frase |
| No hay silencio final y el montaje corta feo | Falta el segundo de cola | Añádelo en `SEGMENTS` |
| Aparece música | Falta «No music» | Añádelo literal en `AUDIO` |
| El prop cambia de mano | No se fija dónde está | Ancla la mano en `FIRST FRAME` y bloquea: `The sheet leaving her hands = failed take.` |
| El texto del documento se retuerce | El modelo no sabe escribir texto | Bloquea: `Text readable = failed take.` y gíralo fuera de foco |
| Manos deformes en primer plano | El plano pide manos manipulando | **Devuelve el plano al guionista**: no se arregla con texto |
| La luz cambia entre fotogramas | Dos fuentes contradictorias | Deja una: «single source, no fill» |
| La toma la rechaza el filtro del proveedor | Vocabulario de la denylist | Cambia el plano, no la palabra: rueda la reacción de quien mira |
| Los ojos quedan en el centro del encuadre | No se respeta la zona segura | El bloque CONSTRAINTS ya lo dice: compruébalo copiado literal |

## Cuándo dejar de intentarlo

- **Tras 3 intentos con la misma causa**, el problema no es la redacción: es el plano.
- **Tras 20 intentos**, el sistema bloquea el plano solo (R-11) y decide un humano.
- Empalmar es una victoria, no una derrota: si los 3 primeros segundos de una toma de
  5 s son buenos, el QC la marca `empalmable` y el montaje corta ahí. Eso es dinero
  salvado, no un plano fallido.

## Lo que nunca es el arreglo

- Subir de nivel (`borrador` → `clave`) para «que salga mejor». El nivel cambia la
  calidad de imagen, no arregla un prompt roto, y multiplica el coste por seis.
- Regenerar la cara de referencia. Está congelada (R-05). Si la identidad falla, se
  cambia el prompt o se crea una **versión nueva** del asset.
- Añadir más prohibiciones. Cada una invoca lo que nombra.
