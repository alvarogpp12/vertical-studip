# Estado del proyecto
> Claude Code: lee este archivo al empezar cada sesión y actualízalo al terminar (qué se hizo, qué falta, bloqueos).

## Última actualización
2026-09-11 · Fases A–G de la arquitectura de agentes: núcleo de datos, validadores, casting, los cuatro agentes con su evaluación, y el orquestador con montaje. 105 tests y `ruff` en verde.

## Hecho
- Investigación: sistema director, 12 reglas del top 30 de Higgsfield, vertical 9:16, proveedores y costes, políticas de plataformas.
- v0.1: CLI `showrunner`, router de modelos por nivel, límites de gasto, conectores fal y BytePlus (este sin verificar), proveedor mock, QC técnico, plantillas de serie, skills base, CI.
- Corregido un fallo del QC: `fotogramas.extraer()` pedía un fotograma en `t == dur`. PR #1.

### Fase A · Núcleo de datos (`src/showrunner/dominio/`)
- **Un solo id de plano: `s01_ep01_sh003`.** La forma corta `ep01_sh001` queda retirada.
- `registro.py` convierte `registry.json` en contrato ejecutable: R-01 y R-02 son aplicables por código por primera vez.
- `shotlist.py` cierra el contrato del plano. El **estado no se guarda**: se pliega del log.
- `serie.py` añade `proyecto.json`: plataforma, duración objetivo y **aprobaciones con firma, fecha y versión**.
- `eventos.py` sustituye `runs/ledger.jsonl` por `runs/eventos.sqlite`. Cierra el TOCTOU del presupuesto, **registra los fallos** y da gratis las métricas del proyecto. Migra el ledger antiguo y lo reexporta sin pérdida.
- Arreglos menores: `slugify` con normalización Unicode, `BUDGET_MAX_PER_DAY` a 60 $, catálogo cacheado, plantillas rellenadas de verdad.

### Fase B · Validadores (`src/showrunner/valida/`)
- Cinco familias sin LLM y sin coste: `prompt`, `plano`, `toma`, `episodio` y `biblia`.
- Los umbrales pasan de la prosa al código. Tolerancia del 9:16 a 0,02 (496×864 es nativa de Seedance 2.5).
- `config/denylist.yaml` y hook `PreToolUse` para que el linter valga también a mano.

### Fase C · Casting
- `providers/imagen.py` + `providers/subida.py` con `fal_client.upload_file()`: **sin R2 ni Supabase**.
- `casting.py` es el primer código que escribe `registry.json`. Aplica R-04, R-05 y R-12.

### Fase D–E · Los cuatro agentes (`src/showrunner/agentes/`) y su evaluación (`evals/`)
- Cada agente es **una función tipada**, no una sesión: `(entrada, contexto) -> Resultado | Rechazo`. Las llamadas caras quedan fuera, en el orquestador.
- **Los `SKILL.md` son el system prompt.** Una sola fuente: se siguen afinando a mano en Claude Code y el pipeline los carga y los cachea (`cache_control` de 1 h, un solo punto de corte al final de `system`).
- Salidas estructuradas nativas con JSON Schema apretado (todas las propiedades en `required`, sin propiedades extra). El esquema es el contrato, no una instrucción en prosa.
- **Rechazos tipados**: unión discriminada con `destinatario` y `motivo_codigo` en mayúsculas, sacados de R-01…R-12 y de los códigos del linter. Se registran como eventos, así que son contables.
- Cada agente pasa su salida por un validador determinista y **reintenta una sola vez** con las incidencias delante; si sigue mal, rechaza al humano con el código. Corregir texto es barato; generar vídeo no.
- El director escribe el prompt y el linter lo revisa **antes** de que salga: es el antídoto del fallo conocido («el LLM se cree director»).
- El QC escala de `claude-sonnet-5` a `claude-opus-5` cuando la confianza es baja, que es justo donde los modelos con visión fallan.
- El coste de cada llamada al LLM queda en el log (`llm_llamada`) y cuenta para el tope diario.
- `evals/`: un script por agente, sin frameworks. El golden set del director (24 prompts, cada uno una mutación que rompe una regla concreta) pasa 24/24 y corre en CI, gratis.

## En curso · Fase 0 · Cimientos
- [ ] Claves en `.env`: Anthropic, BytePlus, fal
- [ ] Issue #3 · Verificar conector BytePlus con llamada real
- [ ] Issue #4 · Precios reales de consola en `config/modelos.yaml` (siguen `estimado`/`verificar`)
- [ ] Verificación pendiente de la fase C: hoja de personaje real → subida → referencia en un vídeo borrador (~0,20 $)
- [ ] Issue #5 · R2: reevaluar; con `fal_client.upload_file()` ya no bloquea nada

## En curso · Fase 1 · Biblia
- [ ] Primera llamada real al agente showrunner con tus 3 ideas.
- [ ] **Etiquetar `evals/casos/ideas.jsonl`** tras leer las biblias que salgan. Sin etiquetas no hay acuerdo juez–humano que medir.
- [ ] Comprobar en la primera llamada real que `usage.cache_read_input_tokens` no es 0: un invalidador silencioso de caché no da error, sólo cuesta dinero.
- [ ] Primer piloto con modelos reales: `showrunner producir <serie> --max-gasto 5 --nivel borrador`. El orquestador ya está probado de punta a punta con mocks; lo que falta es la primera factura de verdad para reconciliar el coste estimado con el real.

### Fase F–G · Orquestador y montaje
- `orquestador.py` es una máquina de estados **sin LLM**: no juzga contenido, sólo decide qué toca y cuándo parar.
- **Idempotencia por huella de contenido**: antes de cada llamada cara se calcula `sha256(modelo + parámetros + referencias + plano)`. Si esa huella ya se generó con éxito, se reutiliza el archivo. Un rerun no vuelve a pagar. La huella lleva el plano dentro a propósito: dos planos con el mismo prompt no comparten toma (el episodio tendría un clip repetido), y un reintento tras un rechazo sí vuelve a rodar, porque es una tirada nueva y no un rerun.
- **Dos fusibles distintos**: el tope diario de `.env` y el `--max-gasto` de cada ejecución.
- **Los tres controles humanos son estados**, no una conversación. `showrunner plan` dice dónde está la serie y qué comando toca, sin gastar nada.
- **Modo desatendido (fase G) sin tocar los agentes**: es una `Politica`. No finge una firma humana: registra que la aprobación fue automática **bajo la política de una persona con nombre**. Sin responsable, no hay modo desatendido.
- `montaje.py` concatena las tomas aprobadas, escala a 1080×1920 (se genera a 720p como mucho y se escala en local, que es gratis) y deja el `.srt` aparte, porque el quinto inferior se reserva para los subtítulos de la plataforma.
- Falta de credencial del LLM = paso bloqueado con su remedio, no una traza.
- La plantilla ya no trae un `shotlist.json` de ejemplo: lo escribe el guionista, y el de la plantilla traía además la convención de ids antigua.
- **Verificación**: un episodio piloto completo (idea → biblia → casting → guion → prompts → tomas → montaje) corre de punta a punta en los tests con proveedores mock, sale a 1080×1920 y dura más de 61 s.

## Pendiente · fase 4 · Publicación
- APIs de TikTok, YouTube y Meta con etiqueta de IA, y analítica de retención de vuelta a la sala de guion.

## Pendiente del usuario
- 3 ideas de serie (1–3 frases) · plataforma principal · presupuesto del primer mes.
- Rellenar `evals/casos/veredictos.jsonl` a medida que revises tomas: hasta que el acuerdo juez–humano esté medido, el QC automático informa pero no decide.
- Confirmar: el log de eventos es global con vistas por serie; `01_objetivo_showrunner.md` especificaba uno por serie.
- Las claves de Anthropic y ARK siguen en el historial del chat. Decidiste no rotarlas por ahora.

## Bloqueos
- Ninguno de código. Para verificar de verdad la cadena de casting hace falta `FAL_KEY` y ~0,20 $; para los agentes, `ANTHROPIC_API_KEY`.
