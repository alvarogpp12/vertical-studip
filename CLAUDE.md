# Showrunner IA — contexto para Claude Code

Objetivo: agente que, a partir de una idea básica, crea la biblia de una serie vertical (9:16) de microdrama y la produce con modelos de vídeo IA al menor coste posible, para monetizar en TikTok, YouTube y Meta.

## Reglas del proyecto
- Todo en español. Formato vertical 9:16, episodios de 60–90 s.
- Nunca generar sin pasar por `showrunner generar` (controla presupuesto y escribe en runs/ledger.jsonl).
- Niveles: borrador (barato, 480p) → trabajo → clave. No usar nivel clave sin toma aprobada en borrador.
- Controles humanos obligatorios: aprobar biblia, aprobar casting, visto bueno final de cada episodio.
- Nunca usar caras o voces de personas reales ni propiedad intelectual ajena. Etiquetar como IA al publicar.
- Las medias pesadas no van a git.

## Comandos
- `uv run showrunner doctor` · `uv run showrunner modelos` · `uv run showrunner nuevo "<título>" --idea "…"`
- `uv run showrunner generar prompt.md --salida ruta.mp4 --nivel borrador --duracion 5`
- `uv run showrunner qc ruta.mp4 --referencia ref.png` · `uv run pytest`

## Skills
- `.claude/skills/showrunner` — idea → biblia
- `.claude/skills/director-vertical` — plano → prompt
- `.claude/skills/qc-continuidad` — revisión de tomas
