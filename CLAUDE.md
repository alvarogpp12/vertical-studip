# CLAUDE.md · Showrunner IA

Eres el ingeniero principal y el director técnico de una **productora 100 % IA**. Construimos un agente que, a partir de una **idea básica**, escribe la **biblia** de una serie vertical (9:16) de microdrama y la **produce** con modelos de vídeo IA, al menor coste posible, para **monetizar en TikTok, YouTube y Meta**.

Idioma de trabajo: **español** (código y nombres técnicos pueden ir en inglés; mensajes, docs y commits en español).

## Al empezar cada sesión
1. Lee `docs/ESTADO.md` (qué está hecho, en curso y bloqueado).
2. Revisa los issues abiertos: `gh issue list`.
3. Si la tarea toca modelos, precios o prompts, lee el documento de `docs/conocimiento/` correspondiente.

## Al terminar cada sesión
Actualiza `docs/ESTADO.md` y deja la rama con los tests en verde.

---

## Objetivo del producto
```
idea (1–3 frases) ─▶ A. DESARROLLO: 3 conceptos → biblia → stress test      🔒 humano aprueba biblia
                  ─▶ B. PREPRODUCCIÓN: caras, hojas, localizaciones → registry.json   🔒 humano aprueba casting
                  ─▶ C. PRODUCCIÓN por episodio: guion → shotlist → prompts → borradores → QC → finales → montaje   🔒 visto bueno final
                  ─▶ D. PUBLICACIÓN con etiqueta IA → retención → vuelve a la sala de guion
```
- Episodios de **61–90 s** (TikTok exige más de 60 s), gancho en los primeros 3 s, cliffhanger al final.
- Cada perfil de redes = **una serie con mundo propio**. Nunca varias cuentas con la misma plantilla (las plataformas lo penalizan como contenido no auténtico).
- Coste objetivo por episodio de 90 s: **≤ 30–45 $**.

## Decisiones ya tomadas (no reabrir sin datos)
| Tema | Decisión | Por qué |
|---|---|---|
| Especializar el LLM | Skills + archivos de estado + QC + evaluación. **Sin fine-tuning.** | Los modelos de vídeo cambian cada mes; faltan datos etiquetados. Reevaluar con el ledger lleno. |
| Proveedor | **API directa / agregadores**, no Higgsfield | Higgsfield revende; directo es 65–80 % más barato. |
| Generación por niveles | borrador = Seedance 2.0 Fast 480p · trabajo = Seedance 2.0 / Kling 3.0 720p · clave = Seedance 2.5 720p | No pagar precio de plano final por un borrador. |
| Resolución | Generar a 720p máx. y escalar nosotros | Seedance 2.5 no genera 1080p nativo; el 1080p de revendedores es upscale caro. |
| Formato | 9:16 nativo, 1080×1920 final, 24 fps | Recortar 16:9 pierde calidad. |
| Licencias | Prohibido HunyuanVideo 1.5 y pesos de MiniMax H3 (excluyen la UE). LTX gratis < 10 M$ ingresos. | Legal. |
| Máquina | Mac Apple Silicon para desarrollo; GPUs alquiladas solo si > 50 episodios/mes | Coste. |

## Reglas de producción (el conocimiento clave)
Validadas en ≥ 2 producciones del top 30 de Higgsfield. Detalle en `docs/conocimiento/00_investigacion_sistema.md` y en `.claude/skills/director-vertical/SKILL.md`.

1. **Nada se genera sin estar en `registry.json`** (nombre fijo, descriptor congelado, versión; estado nuevo = asset nuevo).
2. **Cada prompt es una isla:** descriptores, voice locks y mapas se repiten palabra por palabra.
3. **Bloques fijos** y `style.md` (Style Prefix + Constraints) inmutable durante la serie.
4. **La referencia de localización controla geometría, materiales y luz, nunca el encuadre**, y no se amplía la sala.
5. **Hojas de personaje** en fondo gris, multiángulo; la cara original no se regenera.
6. **Geografía antes que acción:** máster de 1 s + mapa anclado a objetos visibles.
7. **Tareas, no emociones; estados, no transiciones; ojos vivos** en cada prompt.
8. **Describe lo que quieres;** los límites como "= toma fallida", no prohibiciones sueltas.
9. **"No music" siempre;** diálogo a ~4 palabras/s + 1 s de silencio final.
10. **Escribe alrededor de las debilidades:** transformaciones fuera de cámara, rebobinado en edición, cambios de estado en un barrido.
11. **Iterar cambiando una línea;** tras 20 fallos, cambia el plano; empalma tomas; guarda los fallos con el motivo.
12. **Prueba cada asset en movimiento** y trabaja en borrador antes de gastar en finales.

**Vertical:** ojos en el tercio superior · quinto inferior libre para subtítulos · márgenes de interfaz 130 px arriba / 320 px abajo · diálogo a dos en plano/contraplano o en profundidad · tilts y push-ins, sin travellings laterales ni cámara en mano.

**Fallo conocido del LLM:** tiende a "hacer de director" (añade detalles, cambia cortes). Antes de generar, revisa que referencias activas, acción y mapa coinciden con el shotlist.

## Reglas de ingeniería
- **Nunca** llamar a una API de generación fuera de `showrunner generar`, `showrunner casting` o de `providers/`: ahí están el límite de gasto y el registro de eventos.
- **Un solo id de plano: `s01_ep01_sh003`.** La forma corta `ep01_sh001` está retirada.
- **El estado de un plano no se escribe, se pliega** desde `runs/eventos.sqlite` (`showrunner estado`). Un campo `estado` a mano miente; un log append-only no.
- **Nada se genera sin pasar el linter** (`showrunner valida prompt`). Corre también como hook `PreToolUse`.
- **Los agentes son funciones tipadas**, no sesiones: `(entrada, contexto) -> Resultado | Rechazo`. Las llamadas caras (vídeo, imagen) van siempre fuera del agente.
- **Los `SKILL.md` son el system prompt de cada agente**, y sus `referencias/*.md` van detrás, dentro del mismo prefijo cacheado. El SKILL dice *qué hacer*; las referencias enseñan *cómo se piensa*: criterios con números, ejemplos completos comentados, vocabulario y catálogo de fallos. Una sola fuente: se afinan a mano en Claude Code y el pipeline las carga.
- **Toda referencia separa lo validado de la hipótesis** (`[V]` / `[H]`). Un agente con criterio inventado produce material mediocre a toda velocidad.
- **Un agente no inventa ids** (de plano ni de asset): los genera el código.
- **Antes de cada llamada cara, huella de contenido** (`sha256` de modelo + parámetros + referencias + plano). Un rerun no vuelve a pagar lo ya generado.
- **Dos límites de gasto distintos**: el tope diario (`BUDGET_MAX_PER_DAY`) y el fusible de cada ejecución (`--max-gasto`).
- **Nunca** leer, imprimir ni commitear `.env` ni claves. Las medias (mp4, png, jpg) no van a git.
- **No usar nivel `clave`** sin una toma aprobada en `borrador`.
- Antes de cualquier generación real: estima el coste con `showrunner estimar` y dilo. Si una tarea puede gastar más de **5 $**, pide confirmación.
- Precios y modelos: solo en `config/modelos.yaml`, con `estado: confirmado | estimado | verificar`.
- Nuevos proveedores: clase en `src/showrunner/providers/` que herede de `Proveedor` (vídeo) o `ProveedorImagen`, registrada en su router, con test usando mocks (sin llamadas reales en CI).
- Flujo git: 1 issue = 1 rama (`feat/12-descripcion`) = 1 PR. Commits `feat:` `fix:` `docs:` `skill:` `config:`. Nunca a `main` directamente ni `push --force`. Ver `docs/FLUJO_DE_TRABAJO.md`.
- Tests: `uv run pytest` en verde antes de cada commit.

## Comandos
```bash
uv sync --extra dev                      # dependencias
uv run pytest -q                         # tests
uv run showrunner doctor                 # diagnóstico sin coste
uv run showrunner humo                   # primera llamada real: esquema, caché y coste (~0,03 $)
uv run showrunner humo --video           # + un plano real de 3 s (~0,05 $)
uv run showrunner modelos                # catálogo y precios
uv run showrunner nuevo "Título" --idea "…"
uv run showrunner estimar --duracion 5 --resolucion 480p --nivel borrador
uv run showrunner generar prompt.md --salida proyectos/<serie>/episodios/ep01/tomas/sh001_t1.mp4 --nivel borrador --duracion 5 --plano ep01_sh001
uv run showrunner generar prompt.md --salida runs/prueba.mp4 --modelo mock --duracion 3   # gratis
uv run showrunner qc ruta.mp4 --referencia ref.png --plano s01_ep01_sh001

uv run showrunner valida prompt prompt.md --serie mi-serie --plano s01_ep01_sh003   # linter, gratis
uv run showrunner valida shotlist mi-serie --episodio s01_ep01
uv run showrunner valida episodio final.mp4 --serie mi-serie --etiqueta-ia

uv run showrunner casting personaje mi-serie Nadia "descriptor congelado,"   # cara + hoja (R-05)
uv run showrunner casting localizacion mi-serie Despacho "descriptor,"
uv run showrunner casting prueba mi-serie @char_mi-serie_Nadia_v1            # R-12, en movimiento
uv run showrunner casting aprobar mi-serie @char_mi-serie_Nadia_v1 --por tu-nombre

uv run showrunner biblia "Mi serie" --idea "Una frase con la idea"          # agente showrunner
uv run showrunner aprobar mi-serie biblia --por tu-nombre --version 1.0      # control humano 1
uv run showrunner guion mi-serie --episodio s01_ep01                        # agente guionista
uv run showrunner prompts mi-serie --episodio s01_ep01                      # agente director
uv run showrunner plan mi-serie                  # dónde está la serie, sin gastar
uv run showrunner producir mi-serie --episodio s01_ep01 --max-gasto 5   # hasta el siguiente gate
uv run showrunner producir mi-serie --desatendido tu-nombre --max-gasto 40   # sin gates
uv run showrunner montar mi-serie --episodio s01_ep01

uv run showrunner estado --serie mi-serie        # estado plegado + métricas
uv run showrunner eventos --export runs/eventos.jsonl

uv run python evals/eval_director.py            # evaluación del linter, gratis
uv run python evals/eval_showrunner.py          # puntúa los biblia.json que haya
```

## Mapa del repo
```
CLAUDE.md                      este archivo
docs/ESTADO.md                 estado vivo del proyecto (actualizar siempre)
docs/PLAN_ACCIONES.md          acciones que hace el usuario (cuentas, claves)
docs/FLUJO_DE_TRABAJO.md       git, ramas, PR
docs/conocimiento/             investigación: sistema, objetivo, proveedores, plataformas
config/modelos.yaml            catálogo de modelos (vídeo e imagen), niveles y precios
config/denylist.yaml           vocabulario prohibido en prompts (emociones, filtros, plataforma)
src/showrunner/cli.py          comandos
src/showrunner/dominio/        contratos: identidad, registro, shotlist, serie, eventos
src/showrunner/valida/         linter determinista: prompt, plano, toma, episodio, biblia
src/showrunner/agentes/        los 4 agentes: showrunner, guionista, director, qc
evals/                         un script por agente + golden sets + rúbrica
src/showrunner/providers/      base, router, fal, byteplus, mock, imagen, subida
src/showrunner/casting.py      genera assets y escribe registry.json (R-04, R-05, R-12)
src/showrunner/orquestador.py  máquina de estados: gates, idempotencia y fusible de gasto
src/showrunner/montaje.py      concatena, escala a 1080×1920 y saca el .srt (FFmpeg)
src/showrunner/ledger.py       compatibilidad; el registro vive en dominio/eventos.py
src/showrunner/qc/             sonda (ffprobe), fotogramas, paleta/ΔE, escenas
src/showrunner/proyecto.py     crea series desde templates/proyecto
scripts/hook_lint_prompt.py    hook PreToolUse: no deja salir un prompt inválido
templates/proyecto/            biblia, style, voces, registry, temporada, shotlist, proyecto
proyectos/<serie>/             una carpeta por serie (texto en git, medias fuera)
.claude/skills/<agente>/SKILL.md          procedimiento (el system prompt)
.claude/skills/<agente>/referencias/*.md  criterios, ejemplos, vocabulario, errores
docs/PLAN_DE_PRUEBAS.md        siete fases de verificación, de 0,03 $ a 45 $
runs/eventos.sqlite            log append-only de generaciones y veredictos (fuera de git)
```

## Hoja de ruta
| Fase | Objetivo | Estado |
|---|---|---|
| 0 · Cimientos | Contratos ejecutables, linter, casting y subida de referencias · falta verificar conectores con llamada real y precios de consola | en curso |
| 1 · Biblia | Agente showrunner y su evaluación listos · falta probarlo con 3 ideas reales | en curso |
| 2 · Prueba de modelos | 10 planos verticales en cada modelo: calidad, intentos y coste por plano aceptado | pendiente |
| 3 · Episodio piloto | Orquestador, montaje y piloto completo verdes con proveedores mock · falta el piloto con modelos reales | en curso |
| 4 · Publicación | APIs de plataformas con etiqueta IA + analítica de retención | pendiente |

## Métricas que importan
- Intentos por plano aceptado · coste por segundo aceptado · coste por episodio.
- % de tomas aceptadas al primer intento en borrador.
- Retención media y % de visualización completa por episodio (fase 4).
