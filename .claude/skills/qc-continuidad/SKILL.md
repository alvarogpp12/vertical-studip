---
name: qc-continuidad
description: Revisa tomas generadas contra las referencias de la serie (identidad, vestuario, props, geografía, artefactos) usando `showrunner qc` y los fotogramas extraídos. Úsala después de cada generación o cuando haya que aceptar o rechazar tomas.
---
# QC de continuidad · v0.1

1. Ejecutar `showrunner qc <video> --referencia <imagen_estilo>`.
2. Comprobaciones técnicas automáticas: vertical_9_16 = true · cortes_detectados coherentes con el plano · ΔE medio < 15 frente a la referencia.
3. Revisar los fotogramas UNA dimensión cada vez, frente a la hoja del personaje y la localización:
   identidad · vestuario · props y su estado · geografía / eje · artefactos (manos, caras, morphing) · zona segura.
4. Veredicto por toma: aceptada · empalmable (indicar segundos útiles) · rechazada (motivo en una frase).
5. Añadir el motivo al nombre del archivo rechazado y actualizar el veredicto en runs/ledger.jsonl.
Nota: los LLM con visión detectan mal artefactos finos; ante la duda, marcar para revisión humana.
