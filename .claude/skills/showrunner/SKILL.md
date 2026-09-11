---
name: showrunner
description: Convierte una idea básica de 1–3 frases en la biblia completa de una serie vertical de microdrama IA (biblia.md, style.md, voces.md, registry.json, temporada.json). Úsala cuando el usuario dé una idea para una serie o pida crear, revisar o ampliar una biblia.
---
# Showrunner · v0.0 (esqueleto — se completa en la fase 1 con ideas reales)

## Flujo
1. `showrunner nuevo "<título>" --idea "<idea>"` crea la carpeta desde la plantilla.
2. Proponer 3 conceptos. Puntuar producibilidad IA: nº personajes (≤3), nº localizaciones (≤3), acción difícil (evitar), dependencia de efectos.
3. Rellenar `biblia.md` del concepto elegido, luego `style.md`, `voces.md`, `temporada.json`.
4. Stress test por episodio: objetivo · obstáculo · táctica · giro · cambio de valor. Señalar el punto más débil.
5. Detenerse para el CONTROL HUMANO 1 (aprobar biblia).

## Pendiente de construir
- Criterios de gancho y cliffhanger por plataforma.
- Ejemplos de biblias buenas y malas.
- Evaluación con 3 ideas reales.
