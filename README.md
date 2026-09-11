# Showrunner IA

Agente productor de series verticales (9:16) hechas 100 % con IA: **idea → biblia → producción → publicación**, con el menor coste por episodio.

## Instalación (Mac Apple Silicon)
```bash
git clone <URL-de-tu-repo> showrunner-ia && cd showrunner-ia
bash scripts/setup_mac.sh
```
Después abre `.env` y pega tus claves. Guía completa: [docs/PLAN_ACCIONES.md](docs/PLAN_ACCIONES.md) · Cómo trabajamos: [docs/FLUJO_DE_TRABAJO.md](docs/FLUJO_DE_TRABAJO.md).

## Qué incluye (v0.1)
| Pieza | Estado |
|---|---|
| CLI `showrunner` (doctor, modelos, nuevo, estimar, generar, qc) | ✅ probado |
| Router de modelos por nivel (borrador / trabajo / clave) al menor precio | ✅ probado |
| Límite de gasto por tarea y por día + registro de cada generación (`runs/ledger.jsonl`) | ✅ probado |
| Proveedor **fal.ai** (Kling 3.0, Seedance 2.5) | ✅ implementado · pendiente de primera llamada real |
| Proveedor **BytePlus ModelArk** (Seedance 2.0 Fast / 2.0 / 2.5) | ⚠️ implementado según la API de tareas · verificar con la primera llamada |
| Proveedor de prueba sin coste (`mock`) | ✅ probado |
| QC técnico: formato 9:16, fps, cortes, fotogramas clave, paleta hex, ΔE | ✅ probado |
| Plantilla de serie: biblia, style, voces, registry, temporada, shotlist | ✅ |
| Skills de Claude Code: director-vertical v0.1, qc-continuidad v0.1, showrunner v0.0 | 🧱 base |
| Orquestación autónoma con Claude Agent SDK, montaje automático, publicación | ⏳ fases siguientes |

## Uso rápido
```bash
uv run showrunner doctor
uv run showrunner modelos
uv run showrunner nuevo "Mi serie" --idea "Una frase con la idea"
echo "Prompt de prueba" > /tmp/p.md
uv run showrunner generar /tmp/p.md --salida runs/prueba.mp4 --modelo mock --duracion 3
uv run showrunner qc runs/prueba.mp4
```

## Estructura
```
config/modelos.yaml        catálogo de modelos y precios
src/showrunner/            código (proveedores, router, ledger, qc, cli)
templates/proyecto/        plantilla de cada serie
proyectos/<serie>/         una carpeta por serie
.claude/skills/            conocimiento del agente
runs/ledger.jsonl          registro de generaciones (no se sube a git)
```
