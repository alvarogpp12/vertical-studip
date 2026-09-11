---
name: qc-continuidad
description: Revisa tomas generadas contra las referencias de la serie (identidad, vestuario, props, geografía, artefactos) usando `showrunner qc` y los fotogramas extraídos. Úsala después de cada generación o cuando haya que aceptar o rechazar tomas.
---
# QC de continuidad · v0.1

1. Ejecutar `showrunner qc <video> --referencia <imagen_estilo> --plano s01_ep01_sh003 --duracion <s>`.
2. Las comprobaciones técnicas ya las hace el validador y salen en `validacion` del informe: 9:16 (tolerancia 0,02) · 24 fps · duración real vs pedida · ΔE < 15 · una sola escena. Léelas, no las repitas a ojo.
3. Revisar los fotogramas UNA dimensión cada vez, frente a la hoja del personaje y la localización:
   identidad · vestuario · props y su estado · geografía / eje · artefactos (manos, caras, morphing) · zona segura.
4. Veredicto por toma: aceptada · empalmable (indicar segundos útiles) · rechazada (motivo en una frase).
5. Añadir el motivo al nombre del archivo rechazado. El veredicto lo registra `showrunner qc --plano`; para el juicio visual, `showrunner` guarda el evento `qc_veredicto` con su motivo. Consulta el estado con `showrunner estado --serie <slug>`.
6. R-11: tras 20 intentos el plano se bloquea solo. Si llegas ahí, cambia el plano o escala al humano; no sigas reintentando.
Nota: los LLM con visión detectan mal artefactos finos; ante la duda, marcar para revisión humana.
