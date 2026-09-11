# Objetivo: Agente Showrunner (idea básica → biblia → producción)
Fecha: 2026-09-11

## Decisión de negocio
- Ingresos: solo monetización de plataformas (TikTok, YouTube, Meta), con varios perfiles.
- Cada perfil = una serie con biblia propia (mundo, personajes, estilo). Nunca varios perfiles con la misma plantilla; ese patrón es el que persigue la política de "contenido no auténtico".
- Economía por episodio (90 s, vertical, Seedance 2.5 en Higgsfield, estimación): ~1.500–2.500 créditos ≈ 75–125 $. Validar ingresos frente a coste en los 10 primeros episodios antes de escalar perfiles.

## Entradas y salidas
Entrada: idea básica (1–3 frases) + plataforma/perfil.
Salida: biblia aprobada → assets registrados → episodios montados, etiquetados como IA y publicados → aprendizaje con la retención.

## Etapas
A. Desarrollo (autónomo): 3 conceptos → puntuación de producibilidad con IA → biblia (mundo, Style Prefix, Constraints, paleta hex, personajes con descriptor congelado + bloqueo de voz + perfil de actuación, localizaciones con mapa vertical, props, reglas de continuidad, fórmula de episodio con gancho de 0–3 s y cliffhanger, arco de temporada) → stress test.
  CONTROL HUMANO 1: aprobar la biblia (una vez por proyecto).
B. Preproducción (autónomo): prompts de assets → Higgsfield (Soul / Nano Banana Pro / Seedream) → hojas → prueba de estrés en movimiento → registry.json.
  CONTROL HUMANO 2: casting de caras (una vez por proyecto).
C. Producción por episodio (autónomo): guion → shotlist.json → prompts (skill director) → linter → render a 480p → QC → re-render → finales → montaje automático con FFmpeg (subtítulos desde el guion, audio) → export.
  CONTROL HUMANO 3: visto bueno final (2–5 min por episodio).
D. Publicación y aprendizaje: APIs de las plataformas con etiqueta de IA → retención → memoria de la serie → siguientes guiones.

## Estructura de archivos
proyectos/<slug>/ biblia.md · style.md · voces.md · registry.json · temporada.json · ledger.jsonl · analytics.json
proyectos/<slug>/episodios/epNN/ guion.md · shotlist.json · prompts/ · tomas/ · qc.json · final.mp4

## Tecnología
Prototipo en Claude Code → Claude Agent SDK (orquestador + subagentes: guionista, prompter/DoP, QC, montador) · skills: showrunner, director-vertical, qc · Higgsfield CLI (lotes) · FFmpeg · programador de tareas.

## Orden de construcción
1. Skill showrunner (idea → biblia), probada con 3 ideas reales.
2. Preproducción automática de assets.
3. Producción de 1 episodio de principio a fin.
4. Montaje automático + publicación + analítica.
