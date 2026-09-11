# Plan de pruebas

> Todo lo que hay en el repo está verificado **con dobles de prueba**. Eso demuestra
> que la fontanería encaja; no demuestra que el sistema produzca series que alguien
> quiera ver, ni que los conectores respondan, ni que la caché funcione.
>
> Este documento separa las dos cosas y ordena lo que falta de menos a más caro.

## Lo que ya está verificado (gratis, en CI)

| Qué | Cómo | Qué demuestra |
|---|---|---|
| Contratos (`dominio/`) | 15 tests | Que un `registry.json` o un `shotlist.json` inválido no pasa |
| Presupuesto y log | 11 tests, incluida concurrencia | Que dos generaciones en paralelo no pueden pasar del tope; que un ledger antiguo migra y se reexporta sin pérdida |
| Validadores (`valida/`) | 19 tests + golden set de 24 prompts | Que cada regla R-01…R-09 tiene una comprobación que la implementa |
| Agentes | 16 tests con `ClienteFalso` | Que el reintento, el rechazo tipado y el escalado del QC hacen lo que dicen |
| Orquestador | 8 tests, piloto completo con mocks | Que un episodio sale de punta a punta, en 9:16 y de más de 61 s |
| Hook y CLI | 8 tests | Que un prompt inválido no llega a la red |

**Lo que NO demuestra nada de esto:** que la API acepte nuestros esquemas, que la
caché lea, que los conectores de vídeo respondan, que los precios sean los que
creemos, ni —sobre todo— que lo que escriben los agentes sea bueno.

---

## Fase 1 · Humo del cerebro · ~0,03 $

```bash
uv run showrunner humo
```

Dos llamadas reales con el mismo prefijo de sistema.

| Comprueba | Por qué importa | Criterio de aceptación |
|---|---|---|
| La API acepta el esquema del proyecto | Los contratos generan JSON Schema con `$defs`, `anyOf` y una unión discriminada. Si no pasa, todo el diseño de salidas estructuradas se cae | La respuesta valida contra `Sobre[SalidaShowrunner]` |
| El rechazo tipado funciona | Es el canal por el que un agente devuelve trabajo arriba | `tipo == "rechazo"` con su `motivo_codigo` |
| La caché lee | Un invalidador silencioso no da error: sólo multiplica la factura | `cache_read_input_tokens > 0` en la 2.ª llamada |
| El coste estimado se parece al real | Si no, todas las estimaciones del proyecto mienten | Diferencia < 20 % |

**Si la caché no lee**, el prefijo tiene algo que cambia entre llamadas. Sospechosos
por orden: un `datetime.now()`, un JSON sin ordenar, un archivo de conocimiento que
se relee distinto. Sin esto arreglado, el director cuesta 10 veces más.

---

## Fase 2 · Humo del vídeo · ~0,05 $

```bash
uv run showrunner humo --video
uv run showrunner humo --video --modelo-video seedance-2.0-fast@byteplus   # issue #3
```

Un plano de 3 s contra un muro gris. No tiene valor artístico; tiene valor de
fontanería.

| Comprueba | Criterio |
|---|---|
| El conector responde y descarga | Hay un `.mp4` en `runs/` |
| Sale 9:16 nativo | `vertical_9_16 == true` |
| Sale a 24 fps y con la duración pedida | Sin `FPS_DISTINTO` ni `DURACION_DISTINTA` |
| El precio de `config/modelos.yaml` es el real | Contrástalo con la consola del proveedor y cambia `estado: estimado` por `confirmado` (issue #4) |

Esto es lo que cierra la Fase 0 del roadmap. **BytePlus sigue sin una sola llamada
real**: hasta que la haya, su conector es una hipótesis escrita en Python.

---

## Fase 3 · Una biblia de verdad · ~0,30 $

```bash
uv run showrunner biblia "Cañón Rojo" --idea "Una jueza descubre que su hija miente."
uv run python evals/eval_showrunner.py
```

Aquí empieza lo que de verdad no se puede automatizar. La rúbrica te dirá si la
biblia cumple las reglas; **sólo tú puedes decir si el concepto vale**.

Criterios que sí se miden solos: ≤3 personajes, ≤3 localizaciones, descriptores con
anclas, AUDIO LOCK, mapa vertical, paleta en hex, «No music» en CONSTRAINTS.

Criterios que tienes que juzgar tú, y anotar en `evals/casos/ideas.jsonl`:

- ¿El motor de temporada produce el episodio siguiente solo, o es una premisa?
- ¿El gancho de 0–3 s se puede rodar, o necesita contexto que no cabe?
- ¿El acento de la paleta tiene un significado narrativo o es decoración?
- ¿Los riesgos de producción son reales o son relleno?

**Hazlo con las 3 ideas.** Con una no sabes si acertó o tuvo suerte. Cuando tengas
las tres etiquetadas, `eval_showrunner.py` empieza a dar un número con sentido.

---

## Fase 4 · Casting de un personaje · ~0,50 $

```bash
uv run showrunner casting personaje canon-rojo Nadia "<descriptor congelado>"
uv run showrunner casting prueba canon-rojo @char_canon-rojo_Nadia_v1
```

| Comprueba | Criterio |
|---|---|
| La imagen se genera y se sube | La URL de `registry.json` abre en el navegador |
| La URL sirve como referencia de vídeo | La prueba en movimiento no falla por referencia inválida |
| R-12: el asset aguanta en movimiento | La cara no se deforma en 3 s |

**Esta es la prueba que cierra la cadena imagen → registro → vídeo.** Hasta que pase,
ninguna etapa posterior a la biblia es realmente ejecutable.

---

## Fase 5 · Un episodio en borrador · ~3–5 $

```bash
uv run showrunner guion canon-rojo --episodio s01_ep01
uv run showrunner producir canon-rojo --episodio s01_ep01 --nivel borrador --max-gasto 5
```

El primer episodio completo con modelos reales, todo a 480p.

| Métrica | Dónde se lee | Qué buscar |
|---|---|---|
| Intentos por plano aceptado | `showrunner estado --serie canon-rojo` | < 3. Por encima, el problema está en los prompts, no en el modelo |
| % aceptadas al primer intento | idem | > 40 % en borrador |
| Coste por segundo aceptado | idem | Proyectado a 90 s, ¿cabe en 30–45 $? |
| Coste real vs factura | consola del proveedor | Diferencia < 10 % |

**Guarda los rechazos con su motivo.** Son los datos con los que se afinan las skills,
y la hipótesis de `02_proveedores_y_costes.md` —400 s generados por cada 90 s finales—
se confirma o se tira aquí.

Mientras dure, **etiqueta veredictos de QC** en `evals/casos/veredictos.jsonl`: 20–30
tomas con tu juicio. Luego:

```bash
uv run python evals/eval_qc.py
```

Hasta que el acuerdo juez–humano pase del 80 % con kappa decente, el QC automático
**informa pero no decide**. Rechazar una toma buena cuesta un reintento; aceptar una
mala cuesta el episodio.

---

## Fase 6 · Un episodio final · ~30–45 $

Los planos aprobados en borrador se vuelven a rodar en `trabajo` y los de gancho en
`clave`. El prompt no se reescribe al subir de nivel.

```bash
uv run showrunner producir canon-rojo --episodio s01_ep01 --nivel trabajo --max-gasto 40
uv run showrunner montar canon-rojo --episodio s01_ep01
uv run showrunner valida episodio proyectos/canon-rojo/episodios/ep01/final.mp4 \
  --serie canon-rojo --etiqueta-ia
```

Criterio de aceptación: **¿lo publicarías?** Si la respuesta es «casi», anota qué falta
y en qué fase se decidió. Esa es la información que mejora el sistema; el coste por
segundo, solo, no.

---

## Fase 7 · Diez episodios

La decisión de negocio de `01_objetivo_showrunner.md`: validar ingresos frente a coste
en los 10 primeros episodios **antes** de abrir perfiles nuevos. Con el log de eventos
lleno, además, se puede reabrir la decisión de no hacer fine-tuning: ese era el motivo
para aplazarla.

---

## Reglas de gasto durante las pruebas

- Cada fase se cierra antes de abrir la siguiente. Un fallo en la fase 2 con 0,05 $
  vale más que descubrirlo en la fase 6 con 40 $.
- `--max-gasto` es el fusible de cada ejecución; `BUDGET_MAX_PER_DAY`, el del día.
- Si una tarea puede gastar más de 5 $, se confirma antes.
- Los reruns no cuestan: la huella de contenido reutiliza lo ya generado.
