# Rúbrica de continuidad, dimensión por dimensión

> **Procedencia.** Las dimensiones y R-05/R-11 son **[V]**. Los umbrales concretos son
> hipótesis (**[H]**) que se calibran midiendo tu acuerdo con el juez en la fase 5:
> hasta entonces el QC automático informa, no decide.

Mira los fotogramas **siete veces, una por dimensión**. Mezclarlas es exactamente cómo
se cuelan los fallos: el ojo se queda en lo más llamativo y da por buena la toma.

## 1. Identidad
Compara **primer fotograma contra último**, no contra la referencia: la deriva dentro
de la toma es lo que se ve en pantalla.

| Rechaza | Acepta |
|---|---|
| Falta un ancla (cicatriz, anillo, mechón) | La marca está, aunque la luz la aplane |
| Cambia la forma de la mandíbula o de la nariz entre fotogramas | Cambia la expresión |
| Cambia el color o el largo del pelo | El pelo se mueve |
| Aparenta otra edad | Las ojeras se marcan más con esa luz |

Código: `IDENTIDAD_DISTINTA`. Es el fallo más frecuente y el menos perdonable: el
espectador no lo razona, pero deja de creerse la serie.

## 2. Vestuario
| Rechaza | Acepta |
|---|---|
| Cambia el color de una prenda | Cambia cómo cae al moverse |
| Aparece o desaparece una capa (chaqueta, bufanda) | Se abre o se cierra |
| Cambia el tipo de cuello o de botonadura | Se arruga distinto |

Código: `VESTUARIO_DISTINTO`.

## 3. Props y su estado
| Rechaza | Acepta |
|---|---|
| El objeto salta de mano sin acción que lo justifique | Lo cambia de mano y se ve |
| Cambia de estado (cerrado→abierto) sin que ocurra en cámara | Se abre y se ve abrirse |
| Aparece un objeto que no estaba | Entra en cuadro por el borde |

Códigos: `PROP_CAMBIA_DE_MANO`, `PROP_CAMBIA_DE_ESTADO`.

## 4. Geografía y eje
Compara con el **mapa espacial** de la localización, que tienes en la ficha.

| Rechaza | Acepta |
|---|---|
| El personaje está al otro lado del objeto de referencia | Se desplaza y se ve el desplazamiento |
| La ventana pasa de un hombro al otro | La cámara se acerca |
| Aparece una puerta, una pared o una sala que la referencia no muestra | Se ve un trozo distinto de lo que sí muestra |

Código: `EJE_ROTO`. Es el que más caro sale: rompe el plano **y** su contraplano.

## 5. Artefactos
Aquí es donde tu confianza tiene que bajar: en fotogramas sueltos se detectan mal.

| Mira | Umbral |
|---|---|
| Manos: cuenta los dedos en cada fotograma donde salgan | Seis dedos = rechazo inmediato |
| Dientes: número y alineación al hablar | Si «bailan», rechazo |
| Contorno de cara contra el fondo | Si ondula, es morphing |
| Texto en cualquier superficie | Si es legible y está mal, rechazo |
| Pelo contra el fondo | Un poco de ruido es normal |

Código: `ARTEFACTO_EN_MANOS`, `ARTEFACTO_EN_CARA`. **Si dudas, `confianza ≤ 0,6` y
`requiere_humano = true`.** Eso es lo correcto, no una rendición.

## 6. Zona segura vertical
En 1080×1920: 130 px arriba y 320 px abajo son interfaz de la plataforma.

| Rechaza | Acepta |
|---|---|
| Los ojos caen en el centro o por debajo | Los ojos en el tercio superior |
| La acción importante ocurre en el quinto inferior | El quinto inferior tiene cuerpo o fondo |
| Un elemento clave queda bajo los 320 px de abajo | El encuadre respira |

Código: `FUERA_DE_ZONA_SEGURA`.

## 7. Interpretación
La única dimensión donde juzgas intención, no continuidad.

| Rechaza | Acepta |
|---|---|
| Hace una mueca en vez de la tarea del prompt | Hace la tarea y se le nota el estado |
| No parpadea en toda la toma | Parpadea una o dos veces |
| Mira a cámara sin que el prompt lo pida | Mira fuera de campo |
| Los ojos están muertos, sin brillo | Hay catch-lights |

Código: `INTERPRETACION_PLANA`.

## Los tres veredictos

**`aceptada`** — ninguna dimensión falla.

**`empalmable`** — el principio sirve y el fallo llega después. Di **cuántos segundos
del principio** son buenos. Un plano de 5 s del que sirven 3 no es un fallo: es dinero
salvado, porque el montaje corta ahí y no hay que volver a generar.

**`rechazada`** — motivo en una frase y código en mayúsculas. El motivo se guarda: es
el dato con el que se afinan las skills y con el que se mide la métrica que importa,
intentos por plano aceptado.

## Calibración de la confianza **[H]**

| Confianza | Cuándo |
|---|---|
| 0,9–1,0 | El fallo (o su ausencia) se ve sin ampliar |
| 0,7–0,9 | Lo ves, pero depende de un fotograma concreto |
| 0,5–0,7 | Artefactos finos, dedos, microexpresiones. **Escala al modelo grande** |
| < 0,5 | No puedes decidir. `requiere_humano = true` |

Los dos errores no cuestan lo mismo: rechazar una toma buena cuesta un reintento;
aceptar una mala se descubre en el montaje, cuando ya se han rodado los planos de al
lado. Ante la duda **real**, no elijas: escala.

## Lo que nunca decides tú

- **Regenerar la cara de referencia.** Está congelada (R-05). Si la identidad falla, se
  cambia el prompt o se crea una versión nueva del asset.
- **Seguir intentando tras 20 tiradas.** El sistema bloquea el plano solo (R-11). Si
  llegas ahí, el problema es el plano; lo cambia el guionista.
- **Lo técnico.** 9:16, fps, duración, ΔE y cortes ya vienen decididos por el
  validador. Léelos, no los repitas a ojo.
