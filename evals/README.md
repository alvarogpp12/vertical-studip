# Evaluación de los agentes

Un script por agente, sin frameworks. La rúbrica sale de `docs/conocimiento/`
(`rubrica.py` la cita con su fuente al lado), no de una sesión de puntuación manual.

```bash
uv run python evals/eval_director.py                  # gratis · golden set de 24 prompts
uv run python evals/eval_showrunner.py                # gratis · puntúa los biblia.json que hay
uv run python evals/eval_guionista.py                 # gratis · puntúa los guion.json que hay
uv run python evals/eval_qc.py                        # necesita veredictos humanos

uv run python evals/eval_showrunner.py --modo ideas --limite 1     # ⚠️ llama al modelo
uv run python evals/eval_guionista.py --modo generar --serie x     # ⚠️ llama al modelo
uv run python evals/eval_director.py --modo agente --serie x       # ⚠️ llama al modelo
```

## Dos números que no significan lo mismo

**Rúbrica** — cuántos casos pasan las comprobaciones deterministas. Barato y
objetivo, pero sólo mide lo que una máquina sabe ver: que el descriptor esté
copiado palabra por palabra, no que la escena funcione.

**Acuerdo juez–humano** — cuánto coincide el veredicto automático con el tuyo,
con exactitud y kappa de Cohen. La exactitud sola engaña cuando una clase domina:
si el 90 % de las tomas son buenas, decir «buena» siempre da 0,90 y no sirve.

**Antes de dejar que el juez automático decida algo, mide su acuerdo contigo.**
Mientras `casos/veredictos.jsonl` esté vacío, `eval_qc.py` lo dice y devuelve error
en lugar de inventarse un número.

## Los golden sets

| Archivo | Qué es | Quién lo etiqueta |
|---|---|---|
| `casos/prompts.jsonl` | 24 prompts, cada uno una mutación del base que rompe una regla concreta | Las etiquetas son mecánicas (R-01…R-09): miden que el linter implementa la regla, no que la regla sea acertada |
| `casos/ideas.jsonl` | 6 ideas de serie para el showrunner | **Tú**, tras leer la biblia que salga |
| `casos/veredictos.jsonl` | Tomas reales ya juzgadas | **Tú**, al revisar cada toma |

Los casos del director se describen como **mutaciones** de `casos/prompt_base.md`
para que cada línea diga en un vistazo qué regla rompe, en vez de repetir el prompt
entero veinticuatro veces.
