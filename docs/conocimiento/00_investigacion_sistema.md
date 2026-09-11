# Fase 0 — Investigación: sistema "Director IA" para película vertical 9:16 de 5 min
Fecha: 2026-09-10 · Informe visual: https://claude.ai/code/artifact/4aca0836-003d-4588-884b-04b85c90f870

## Decisiones
- NO fine-tuning. Pericia = Agent Skill versionada + registro de assets (JSON) + ledger + bucle de QC + golden set de evaluación.
- Conocimiento del proyecto = biblia de la película (guion, personajes, paleta). Skill = procedimientos.
- Formato: 9:16 nativo (1080×1920, 24 fps). No recortar 16:9.
- Festival Higgsfield: solo 16:9/21:9, cierra 14 sep 2026 23:59 UTC → la película vertical NO entra.

## Datos verificados (fuentes Higgsfield)
- MCP oficial: https://mcp.higgsfield.ai/mcp (requiere suscripción). Incluye generación en todos los modelos, Soul Characters, Elements, upscale, reframe, audio y saldo.
- Claude Code: CLI `npm i -g @higgsfield/cli` → `higgsfield auth login` → `npx skills add higgsfield-ai/skills`.
- MCP/CLI SIEMPRE cobran créditos (el acceso ilimitado es solo web).
- Seedance 2.5: hasta 30 s, 480/720/1080p (4K = upscale), de 9:16 a 21:9, hasta 50 refs (30 img/10 vídeo/10 audio), audio en la misma pasada. 10 s = 30/65/90 créditos (480/720/1080p), ≈0,05 $/crédito.
- Pendiente de verificar: nombres de herramientas del MCP, si expone Seedream 5.0 Pro / Cinema Studio 4.0 / @tags / clips de 30 s, resolución nativa real (ffprobe).

## 12 reglas del top 30 (validadas por ≥2 producciones)
R-01 Nada se rueda sin estar en el registro (nombre fijo, descriptor congelado, versión; estado nuevo = asset nuevo).
R-02 Cada prompt es una isla (repetir descriptores/voz/mapa palabra por palabra; eliminar tags heredados).
R-03 Bloques fijos + Style Prefix y Constraints inmutables por proyecto.
R-04 La referencia de localización manda en geometría/materiales/luz, nunca en el encuadre; prohibido ampliar la sala.
R-05 Hojas de personaje: fondo gris, multiángulo; el primer plano original de la cara no se regenera.
R-06 Geografía antes que acción: plano máster de 1 s + mapa espacial anclado a objetos visibles (o diagrama por colores).
R-07 Tareas, no emociones; estados, no transiciones; ojos vivos en cada prompt.
R-08 Nombrar algo lo invoca: especificación positiva + "= toma fallida", no prohibiciones sueltas.
R-09 "Sin música" siempre; diálogo a ~4 palabras/s + 1 s de cola limpia.
R-10 Escribir alrededor de las debilidades (transformación fuera de cámara, rebobinado en edición, cambio de estado en barrido, artefactos justificados en la historia).
R-11 Cambiar una línea por intento; tras 20 fallos, cambiar el plano; empalmar tomas; guardar fallos con el motivo en el nombre.
R-12 Prueba de estrés de cada asset en movimiento; montar a 480p y escalar solo las finales.
Abierto: continuidad por referencia (The Prompter) vs encadenar últimos 3–4 s como @video (New Girl) → A/B.
Fallo conocido: Claude "se cree director" (añade detalles, cambia cortes) → linter/hook antes de cada llamada.

## Vertical 9:16
- Zonas seguras: 130 px arriba, 320 px abajo, 60 px laterales; ojos en el tercio superior.
- Diálogo: plano/contraplano o escalonamiento en profundidad (no two-shot lateral). Planos medios/primeros planos, 50/85 mm.
- Cámara: tilts y acercamientos/alejamientos; evitar travellings laterales y cámara en mano.
- 5 min = 3–5 capítulos de 60–90 s, gancho en los primeros 3 s y final antes de resolver.
- No se traslada: truco anamórfico 2.39:1, planos corales anchos; los diagramas se dibujan en vertical y vista frontal.

## Arquitectura
Guion/biblia → registry.json → escritor de prompts (skill, fases silenciosas + comprobaciones de fallo) → linter/hook → Higgsfield MCP/CLI → QC automático (ffmpeg, PySceneDetect, similitud facial, paleta ΔE) → crítico visual (subagente con rúbrica, una dimensión cada vez) → aceptar/regenerar → ledger.jsonl → revisión semanal de la skill.

## Hoja de ruta
1. Sem 1: conectar MCP + CLI, listar herramientas, 3 clips de prueba 9:16 + ffprobe, revisar términos, tope de créditos.
2. Sem 1–2: skill director v0.1 + esquemas registry/shotlist/ledger.
3. Sem 2–3: golden set de ~30 planos (8 categorías); baseline con/sin skill; A/B de continuidad.
4. Sem 3–4: QC automático + hooks; calibrar el crítico con veredictos humanos.
5. Sem 4–5: piloto de un capítulo de 60–90 s.
6. Sem 6–9: película de 5 min (4 capítulos).
Presupuesto de vídeo estimado: ≈9.000 créditos (ajustado) a ≈23.000 (realista). Referencia: Azul Cobalto 5:30 = 18.422.

## Riesgos
Filtros de persona real/NSFW por vocabulario · referencias invalidadas sin aviso · AI Act art. 50 (desde 2 ago 2026: aviso de IA) · autoría humana a documentar · licencia de entrenamiento en los términos de Higgsfield · InsightFace requiere licencia comercial · Suno solo en plan de pago · evitar CapCut con material de clientes.
