---
name: qc-continuidad
description: Revisa tomas generadas contra las referencias de la serie (identidad, vestuario, props, geografía, artefactos) usando `showrunner qc` y los fotogramas extraídos. Úsala después de cada generación o cuando haya que aceptar o rechazar tomas.
---
# QC de continuidad · v1.0

Decides si una toma se queda, se empalma o se tira. Los dos errores cuestan distinto:

- **Aceptar una mala** contamina el episodio y se descubre en el montaje, cuando ya se
  han rodado los planos de al lado. Es el error caro.
- **Rechazar una buena** cuesta un reintento. Es el error barato.

Ante la duda real, no elijas: baja la confianza y marca `requiere_humano`.

## Lo técnico ya está decidido
Antes de llegar a ti, un validador ha comprobado 9:16 (tolerancia 0,02), 24 fps,
duración real frente a la pedida, ΔE < 15 frente a la referencia y que haya una sola
escena. Lo recibes hecho, en el bloque de incidencias técnicas. **No lo repitas a
ojo**: tú juzgas lo que una máquina no puede.

## Una dimensión cada vez
Repasa los fotogramas siete veces, una por dimensión. Mezclarlas es cómo se cuelan los
fallos.

| Dimensión | Qué miras | Rechaza si |
|---|---|---|
| `identidad` | Cara, pelo, edad, **las anclas** (cicatriz, anillo, mechón) | Falta un ancla, o la cara cambia entre el primer y el último fotograma |
| `vestuario` | Prenda, color, capas, cómo cae | Cambia el color o aparece/desaparece una prenda |
| `props` | Qué objeto, en qué mano, en qué estado | Salta de mano, cambia de estado sin acción que lo justifique |
| `geografia` | Posiciones frente al mapa, lado de cámara | Se invierte izquierda/derecha, o aparece espacio que la referencia no muestra |
| `artefactos` | Manos, dedos, dientes, morphing, texto | Seis dedos, una cara que respira mal, texto que se retuerce |
| `zona_segura` | Ojos en el tercio superior, quinto inferior libre | La cara se va al centro o el subtítulo taparía la acción |
| `interpretacion` | ¿Hace la tarea del prompt? ¿Ojos vivos? | Mira a cámara sin motivo, no parpadea, hace una mueca en vez de una tarea |

## Los tres veredictos

**`aceptada`** — ninguna dimensión falla. El plano entra en el montaje tal cual.

**`empalmable`** — el principio sirve y el fallo llega después. Di **cuántos segundos**
son buenos (`segundos_utiles`). Un plano de 5 s del que sirven 3 es dinero salvado:
el montaje corta ahí.

**`rechazada`** — hay que volver a rodar. El motivo va en una frase y el código en
mayúsculas: `IDENTIDAD_DISTINTA`, `PROP_CAMBIA_DE_MANO`, `EJE_ROTO`,
`ARTEFACTO_EN_MANOS`, `FUERA_DE_ZONA_SEGURA`, `INTERPRETACION_PLANA`.

## Confianza y cuándo pedir ayuda
`confianza` es 0–1 y es tuya, no del sistema.

- Los **artefactos finos** (dedos, dientes, microexpresiones) se detectan mal en
  fotogramas sueltos: si tu duda está ahí, la confianza no pasa de 0,6.
- Por debajo de 0,7 el veredicto se repite con un modelo más grande antes de decidir
  nada caro.
- `requiere_humano = true` cuando una persona vería en dos segundos algo que tú no
  puedes confirmar: identidad dudosa, tono de piel, si una mirada «funciona».

## Después del veredicto
- El veredicto lo registra `showrunner qc --plano s01_ep01_sh003`; no se edita a mano
  ningún archivo de log.
- Los rechazos se guardan **con su motivo**: son los datos con los que se mide la
  métrica que importa, intentos por plano aceptado.
- **R-11**: al corregir se cambia **una** línea del prompt. Tras 20 intentos el plano se
  bloquea solo. Si llegas ahí, el problema es el plano, no la toma: que lo cambie el
  guionista.
- **R-05**: si el fallo es de identidad, la solución nunca es regenerar la cara de
  referencia. La cara original está congelada; se cambia el prompt o se crea una
  versión nueva del asset.
