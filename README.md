# Showrunner IA

**Productora 100 % IA de series verticales.** Un agente que convierte una idea básica en la biblia de una serie y la produce episodio a episodio con modelos de vídeo IA, al menor coste, para publicar en TikTok, YouTube Shorts e Instagram Reels.

```
idea → biblia → casting → episodios (borrador → QC → finales → montaje) → publicación → retención → siguientes guiones
```

---

## Empezar (Mac Apple Silicon)

### 1. Instalar
```bash
git clone https://github.com/alvarogpp12/vertical-studip.git showrunner-ia
cd showrunner-ia
bash scripts/setup_mac.sh
```
Instala Homebrew, git, ffmpeg, Node, uv, Python 3.12, las librerías y Claude Code. Al final ejecuta los tests y el diagnóstico.

### 2. Claves
```bash
open -e .env
```
Rellena las claves de Anthropic, BytePlus ModelArk, fal.ai y Cloudflare R2. Paso a paso en [docs/PLAN_ACCIONES.md](docs/PLAN_ACCIONES.md).

### 3. Trabajar con Claude Code
```bash
claude
```
Claude Code lee [CLAUDE.md](CLAUDE.md) automáticamente: objetivo, decisiones, reglas de producción, comandos y hoja de ruta. Primer mensaje recomendado:

> Lee docs/ESTADO.md y los issues abiertos. Ejecuta `uv run showrunner doctor` y dime qué falta para cerrar la Fase 0.

---

## Cómo funciona

| Pieza | Qué hace | Estado |
|---|---|---|
| `showrunner` (CLI) | doctor · modelos · nuevo · estimar · generar · qc · valida · casting · estado · eventos · aprobar | ✅ |
| Contratos de datos | `registry.json`, `shotlist.json` y `proyecto.json` validados en código (Pydantic) | ✅ |
| Router de modelos | Elige el modelo más barato del nivel pedido (borrador / trabajo / clave) | ✅ |
| Control de gasto | Límite por tarea y por día, reservado en una transacción; todo en `runs/eventos.sqlite` | ✅ |
| Linter de prompts | R-01…R-09 antes de gastar, y como hook `PreToolUse` en Claude Code | ✅ |
| Casting | Cara + hoja multiángulo, localizaciones, subida a URL pública y escritura del registro | ✅ con `mock`; pendiente 1.ª llamada real |
| Conector fal.ai | Kling 3.0, Seedance 2.5 | ✅ pendiente de 1.ª llamada real |
| Conector BytePlus ModelArk | Seedance 2.0 Fast, 2.0, 2.5 (API oficial de ByteDance) | ⚠️ verificar con llamada real |
| QC técnico | Formato 9:16, fps, cortes, fotogramas clave, paleta hex, deriva de color ΔE | ✅ |
| Plantilla de serie | biblia, style, voces, registry, temporada, shotlist | ✅ |
| Skills del agente | director-vertical v0.1 · qc-continuidad v0.1 · showrunner v0.0 | 🧱 |
| Agentes (showrunner, guionista, director, QC) | Funciones tipadas con salida estructurada y canal de rechazo | ✅ pendiente de 1.ª llamada real |
| Evaluación | Un script por agente, rúbrica de `docs/conocimiento/`, acuerdo juez–humano | ✅ |
| Orquestador | Máquina de estados con gates humanos, idempotencia por huella y fusible de gasto | ✅ |
| Montaje | Concatena las tomas aprobadas, escala a 1080×1920 y saca el `.srt` | ✅ |
| Publicación | APIs de plataformas con etiqueta de IA + analítica de retención | ⏳ |

### Niveles de generación
| Nivel | Modelo | Precio aprox. (USD/s) | Uso |
|---|---|---|---|
| borrador | Seedance 2.0 Fast · 480p | 0,04 | Probar prompts, animatic |
| trabajo | Seedance 2.0 / Kling 3.0 · 720p | 0,13–0,15 | La mayoría de planos |
| clave | Seedance 2.5 · 720p | 0,23 | Ganchos y planos importantes |

Precios estimados a septiembre de 2026; los confirmados viven en `config/modelos.yaml`.

---

## Uso rápido
```bash
uv run showrunner doctor
uv run showrunner modelos
uv run showrunner nuevo "Mi serie" --idea "Una frase con la idea"
uv run showrunner estimar --duracion 5 --resolucion 480p --nivel borrador
uv run showrunner generar prompt.md --salida runs/prueba.mp4 --modelo mock --duracion 3   # gratis
uv run showrunner qc runs/prueba.mp4
uv run showrunner valida shotlist mi-serie --episodio s01_ep01   # gratis, sin red
uv run showrunner estado --serie mi-serie                        # intentos, coste y métricas

uv run showrunner biblia "Mi serie" --idea "Una frase con la idea"   # agente showrunner
uv run showrunner guion mi-serie --episodio s01_ep01                 # agente guionista
uv run showrunner prompts mi-serie --episodio s01_ep01               # agente director
uv run showrunner plan mi-serie                                       # sin gastar
uv run showrunner producir mi-serie --episodio s01_ep01 --max-gasto 5 # hasta el siguiente gate
uv run python evals/eval_director.py                                 # evaluación, gratis
```

## Estructura
```
CLAUDE.md                 instrucciones para Claude Code
docs/                     estado, plan de acciones, flujo de trabajo, investigación
config/modelos.yaml       catálogo de modelos y precios
src/showrunner/dominio/   contratos: ids, registro, shotlist, proyecto, log de eventos
src/showrunner/valida/    linter determinista: prompt, plano, toma, episodio, biblia
src/showrunner/agentes/   los 4 agentes que deciden (el resto es código determinista)
evals/                    evaluación por agente, con golden sets etiquetados
src/showrunner/           código: proveedores, router, casting, orquestador, montaje, qc, cli
templates/proyecto/       plantilla de cada serie
proyectos/<serie>/        una carpeta por serie
.claude/                  skills y permisos de Claude Code
```

## Reglas del repo
- `main` siempre funciona: 1 issue = 1 rama = 1 PR, con la CI en verde. Ver [docs/FLUJO_DE_TRABAJO.md](docs/FLUJO_DE_TRABAJO.md).
- Nunca se suben claves, `.env`, vídeos ni imágenes.
- Un solo id de plano: `s01_ep01_sh003`. El estado de cada plano se pliega del log de eventos, no se escribe a mano.
- Todo el contenido publicado se etiqueta como generado con IA. Sin caras, voces ni propiedad intelectual de terceros.

## Hoja de ruta
0 · Cimientos → 1 · Biblia → 2 · Prueba de modelos → 3 · Episodio piloto → 4 · Publicación. El detalle está en los milestones de GitHub y en [CLAUDE.md](CLAUDE.md).
