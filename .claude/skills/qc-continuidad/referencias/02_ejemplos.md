# Veredictos de ejemplo

> **Procedencia.** Las reglas son **[V]**; estos veredictos son material de
> calibración (**[H]**). Cuando tengas 20–30 tomas etiquetadas por ti en
> `evals/casos/veredictos.jsonl`, estos ejemplos se sustituyen por los tuyos.

## Aceptada

```json
{"veredicto": "aceptada", "motivo_codigo": "ACEPTADA",
 "motivo": "Identidad, eje y props estables; interpretación cumple la tarea.",
 "hallazgos": [], "segundos_utiles": 0.0, "confianza": 0.92, "requiere_humano": false}
```
> Cicatriz visible en los fotogramas 0 y 3. La ventana sigue detrás del hombro derecho.
> Parpadea dos veces y hay catch-lights. Alinea los papeles, que es la tarea del prompt.

## Empalmable — la más rentable de las tres

```json
{"veredicto": "empalmable", "motivo_codigo": "ARTEFACTO_EN_MANOS",
 "motivo": "Los dedos se deforman al soltar el papel, a partir del segundo 3,2.",
 "hallazgos": [{"dimension": "artefactos", "descripcion": "seis dedos en la mano izquierda",
                "fotograma": 3}],
 "segundos_utiles": 3.0, "confianza": 0.85, "requiere_humano": false}
```
> Los tres primeros segundos son limpios y contienen la frase entera. El montaje corta
> en 3,0 s. **No se regenera nada**: se ha salvado el plano.

## Rechazada por identidad

```json
{"veredicto": "rechazada", "motivo_codigo": "IDENTIDAD_DISTINTA",
 "motivo": "La cicatriz de la ceja desaparece entre el primer y el último fotograma.",
 "hallazgos": [{"dimension": "identidad", "descripcion": "sin cicatriz en la ceja izquierda",
                "fotograma": 4}],
 "segundos_utiles": 0.0, "confianza": 0.88, "requiere_humano": false}
```
> Un ancla que desaparece es rechazo aunque el resto sea perfecto: es lo que hace que
> el espectador deje de creerse la serie. Arreglo probable: el prompt no lleva el
> descriptor literal.

## Rechazada por eje

```json
{"veredicto": "rechazada", "motivo_codigo": "EJE_ROTO",
 "motivo": "La ventana aparece a la izquierda; el mapa la sitúa tras el hombro derecho.",
 "hallazgos": [{"dimension": "geografia", "descripcion": "plano invertido respecto al mapa",
                "fotograma": 0}],
 "segundos_utiles": 0.0, "confianza": 0.94, "requiere_humano": false}
```
> El eje roto no se nota solo: rompe también el contraplano. Cuanto antes se rechace,
> menos planos hay que rehacer.

## Duda honesta — escala

```json
{"veredicto": "rechazada", "motivo_codigo": "ARTEFACTO_EN_CARA",
 "motivo": "El contorno de la mandíbula parece ondular en el fotograma 2, no es concluyente.",
 "hallazgos": [{"dimension": "artefactos", "descripcion": "posible morphing leve",
                "fotograma": 2}],
 "segundos_utiles": 0.0, "confianza": 0.45, "requiere_humano": true}
```
> Confianza por debajo de 0,7: el sistema repite el veredicto con el modelo grande
> antes de tirar la toma. `requiere_humano` porque una persona lo ve en dos segundos y
> tú no puedes confirmarlo desde fotogramas sueltos. **Esto es hacer bien el trabajo**,
> no rendirse.

## El error que hay que evitar

```json
{"veredicto": "aceptada", "motivo_codigo": "ACEPTADA",
 "motivo": "Se ve bien.", "confianza": 0.95, "requiere_humano": false}
```
> Confianza alta sin haber mirado las siete dimensiones. Aceptar una toma mala se
> descubre en el montaje, cuando los planos de al lado ya están rodados y pagados. El
> motivo tiene que decir **qué comprobaste**, no qué impresión te dio.
