# Estado del proyecto
> Claude Code: lee este archivo al empezar cada sesión y actualízalo al terminar (qué se hizo, qué falta, bloqueos).

## Última actualización
2026-09-11 · Fases A, B y C de la arquitectura de agentes: núcleo de datos, validadores deterministas y casting. Tests y linter en verde.

## Hecho
- Investigación: sistema director, 12 reglas del top 30 de Higgsfield, vertical 9:16, proveedores y costes, políticas de plataformas.
- Entorno verificado en Mac: `uv` + Python 3.12.14 + dependencias; `pytest` en verde y `showrunner doctor` sin fallos salvo claves.
- Corregido un fallo del QC: `fotogramas.extraer()` pedía un fotograma en `t == dur`. PR #1.
- v0.1: CLI `showrunner`, router de modelos por nivel, límites de gasto, ledger, conectores fal y BytePlus (este sin verificar), proveedor mock, QC técnico, plantillas de serie, skills base, CI.

### Fase A · Núcleo de datos (`src/showrunner/dominio/`)
- **Un solo id de plano: `s01_ep01_sh003`.** La forma corta `ep01_sh001` de las plantillas queda retirada; convivían dos convenciones incompatibles.
- `registro.py` convierte `registry.json` en contrato ejecutable: resuelve `@tag` → descriptor y URLs, valida versiones y tipos. Es la primera vez que R-01 y R-02 son aplicables por código.
- `shotlist.py` cierra el contrato del plano (`es_master`, `orden_montaje`, `prompt_path`, `seed`, palabras de diálogo). El **estado no se guarda**: se pliega del log.
- `serie.py` añade `proyecto.json`: plataforma de destino, duración objetivo y **aprobaciones con firma, fecha y versión** (antes eran «Aprobada por: —» en texto libre).
- `eventos.py` sustituye `runs/ledger.jsonl` por `runs/eventos.sqlite`, append-only. Cierra el TOCTOU del presupuesto (dos generaciones en paralelo ya no pueden pasar del tope), **registra los fallos** —antes invisibles, y son la mayor palanca de coste— y da gratis las métricas: intentos por plano aceptado, coste por segundo aceptado, % al primer intento. `showrunner eventos --migrar` importa el ledger antiguo y `--export --formato ledger` lo reproduce sin pérdida.
- Arreglos menores: `slugify` con normalización Unicode («Cañón Rojo» daba `ca-n-rojo`), `BUDGET_MAX_PER_DAY` a 60 $ (con 25 $ un episodio de 30–45 $ se autobloqueaba), catálogo de modelos cacheado, `import subprocess` muerto en `cli.py`, plantillas rellenadas de verdad al crear una serie.

### Fase B · Validadores (`src/showrunner/valida/`)
- Cuatro familias, sin LLM y sin coste: `prompt` (R-01, R-02, R-03, R-07, R-08, R-09 + denylist de plataforma), `plano` (R-06, R-09, R-11, R-12 y gramática de cámara vertical), `toma` (9:16, fps, duración, ΔE, cortes) y `episodio` (≥ 61 s de TikTok, etiqueta de IA).
- Los umbrales pasan de la prosa al código. La tolerancia del 9:16 sube de 0,01 a 0,02: 496×864 es nativa de Seedance 2.5 y quedaba fuera.
- `config/denylist.yaml` recoge el vocabulario de emoción, el que dispara los filtros de los modelos y el que penalizan las plataformas.
- Hook `PreToolUse` en `.claude/settings.json` (`scripts/hook_lint_prompt.py`): el linter vale también trabajando a mano en Claude Code.

### Fase C · Casting (el bloqueo duro)
- `providers/imagen.py` (Nano Banana Pro para hojas, Seedream 5.0 Pro para localizaciones, `mock-imagen` sin coste) y `providers/subida.py` con `fal_client.upload_file()`: **sin R2 ni Supabase**. R2 queda documentado como opción para archivo canónico.
- `casting.py` es el primer código que escribe `registry.json`. Aplica R-05 (fondo gris, multiángulo, y la cara original queda congelada: cambiarla exige una versión nueva del asset), R-04 y R-12 (prueba en movimiento antes de dar nada por bueno).

## En curso · Fase 0 · Cimientos
- [ ] Claves en `.env`: Anthropic, BytePlus, fal
- [ ] Issue #3 · Verificar conector BytePlus con llamada real
- [ ] Issue #4 · Precios reales de consola en `config/modelos.yaml` (siguen `estimado`/`verificar`)
- [ ] Verificación pendiente de la fase C: generar una hoja de personaje real, subirla y usar la URL como referencia en un vídeo a nivel borrador (~0,20 $). Cierra la cadena imagen → registro → vídeo.
- [ ] Issue #5 · R2: reevaluar; con `fal_client.upload_file()` ya no bloquea nada.

## Pendiente · fases D a G del plan de agentes
- D · Agente showrunner (idea → biblia) con su eval y golden set.
- E · Agentes guionista, director y QC, cada uno con su eval. Antes de fiarse del juez automático, medir su acuerdo con el etiquetado humano.
- F · Orquestador interactivo: episodio piloto completo con los tres controles humanos.
- G · Desatendido, encima de lo anterior y sin tocar los agentes.

## Pendiente del usuario
- 3 ideas de serie (1–3 frases) · plataforma principal · presupuesto del primer mes.
- **Rotar las claves de Anthropic y ARK** que se pegaron en el chat.
- Confirmar: el log de eventos es global con vistas por serie; `01_objetivo_showrunner.md` especificaba uno por serie.

## Bloqueos
- Ninguno de código. Para verificar de verdad la cadena de casting hace falta `FAL_KEY` y gastar ~0,20 $.
