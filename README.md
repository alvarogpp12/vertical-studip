# Showrunner IA

**Productora 100 % IA de series verticales.** Un agente que convierte una idea básica en la biblia de una serie y la produce episodio a episodio con modelos de vídeo IA, al menor coste, para publicar en TikTok, YouTube Shorts e Instagram Reels.

```
idea → biblia → casting → episodios (borrador → QC → finales → montaje) → publicación → retención → siguientes guiones
```

---

## Empezar (Mac Apple Silicon)

### 1. Instalar
```bash
git clone https://github.com/TU_USUARIO/TU_REPO.git showrunner-ia
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
| `showrunner` (CLI) | doctor · modelos · nuevo · estimar · generar · qc | ✅ |
| Router de modelos | Elige el modelo más barato del nivel pedido (borrador / trabajo / clave) | ✅ |
| Control de gasto | Límite por tarea y por día; cada generación queda en `runs/ledger.jsonl` | ✅ |
| Conector fal.ai | Kling 3.0, Seedance 2.5 | ✅ pendiente de 1.ª llamada real |
| Conector BytePlus ModelArk | Seedance 2.0 Fast, 2.0, 2.5 (API oficial de ByteDance) | ⚠️ verificar con llamada real |
| QC técnico | Formato 9:16, fps, cortes, fotogramas clave, paleta hex, deriva de color ΔE | ✅ |
| Plantilla de serie | biblia, style, voces, registry, temporada, shotlist | ✅ |
| Skills del agente | director-vertical v0.1 · qc-continuidad v0.1 · showrunner v0.0 | 🧱 |
| Orquestador autónomo, montaje, publicación | Claude Agent SDK + FFmpeg + APIs de plataformas | ⏳ |

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
```

## Estructura
```
CLAUDE.md                 instrucciones para Claude Code
docs/                     estado, plan de acciones, flujo de trabajo, investigación
config/modelos.yaml       catálogo de modelos y precios
src/showrunner/           código: proveedores, router, ledger, qc, cli
templates/proyecto/       plantilla de cada serie
proyectos/<serie>/        una carpeta por serie
.claude/                  skills y permisos de Claude Code
```

## Reglas del repo
- `main` siempre funciona: 1 issue = 1 rama = 1 PR, con la CI en verde. Ver [docs/FLUJO_DE_TRABAJO.md](docs/FLUJO_DE_TRABAJO.md).
- Nunca se suben claves, `.env`, vídeos ni imágenes.
- Todo el contenido publicado se etiqueta como generado con IA. Sin caras, voces ni propiedad intelectual de terceros.

## Hoja de ruta
0 · Cimientos → 1 · Biblia → 2 · Prueba de modelos → 3 · Episodio piloto → 4 · Publicación. El detalle está en los milestones de GitHub y en [CLAUDE.md](CLAUDE.md).
