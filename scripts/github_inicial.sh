#!/usr/bin/env bash
# Crea etiquetas, fases (milestones) e issues iniciales en tu repo de GitHub.
# Requisitos: gh instalado y autenticado (gh auth login), ejecutado dentro de la carpeta del repo.
set -euo pipefail
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Configurando $REPO"

echo "==> Etiquetas"
gh label create "conector"   --color 1D76DB --description "Proveedores de modelos" --force
gh label create "skill"      --color 5319E7 --description "Conocimiento del agente" --force
gh label create "qc"         --color 0E8A16 --description "Control de calidad" --force
gh label create "coste"      --color FBCA04 --description "Precios y presupuesto" --force
gh label create "serie"      --color D93F0B --description "Contenido de una serie" --force
gh label create "bloqueado"  --color B60205 --description "Espera una acción externa" --force

echo "==> Fases"
milestone() { gh api "repos/$REPO/milestones" -f title="$1" -f description="$2" >/dev/null 2>&1 || true; }
milestone "Fase 0 · Cimientos"        "Conectores verificados, precios reales, referencias en R2, CI verde"
milestone "Fase 1 · Biblia"           "Skill showrunner: idea → biblia, probada con 3 ideas"
milestone "Fase 2 · Prueba de modelos" "Mismos 10 planos en cada modelo: calidad y coste por plano aceptado"
milestone "Fase 3 · Episodio piloto"  "Assets automáticos, orquestación con Agent SDK y montaje automático"
milestone "Fase 4 · Publicación"      "Publicación con etiqueta IA y analítica de retención"

echo "==> Issues"
issue() { gh issue create --title "$1" --label "$2" --milestone "$3" --body "$4" >/dev/null && echo "  + $1"; }
issue "Verificar conector BytePlus con una llamada real" "conector" "Fase 0 · Cimientos" \
  "Ejecutar la generación de prueba de docs/PLAN_ACCIONES.md (D3) y ajustar src/showrunner/providers/byteplus.py a la respuesta real."
issue "Poner precios reales de la consola en config/modelos.yaml" "coste" "Fase 0 · Cimientos" \
  "Sustituir los precios estimados de BytePlus por los que muestra la consola y marcar estado: confirmado."
issue "Subida automática de referencias a Cloudflare R2" "conector" "Fase 0 · Cimientos" \
  "Los modelos necesitan URLs públicas. Comando que sube una imagen y devuelve la URL, integrado en generar."
issue "Skill showrunner: idea → biblia completa" "skill" "Fase 1 · Biblia" \
  "Completar .claude/skills/showrunner con criterios de gancho, producibilidad y stress test. Probar con 3 ideas reales."
issue "Prueba de modelos con 10 planos verticales" "qc,coste" "Fase 2 · Prueba de modelos" \
  "Mismos prompts y referencias en Seedance 2.0 Fast, 2.0, 2.5 y Kling 3.0. Tabla: calidad, intentos y coste por plano aceptado."
issue "Generación automática de assets de personaje y localización" "skill" "Fase 3 · Episodio piloto" \
  "Desde registry.json: cara, hoja multiángulo, localizaciones, prueba en movimiento."
issue "Orquestador de episodio con Claude Agent SDK" "skill" "Fase 3 · Episodio piloto" \
  "Guion → shotlist → prompts → generar → QC → reintento, con los 3 controles humanos."
issue "Montaje automático con FFmpeg (subtítulos desde guion)" "qc" "Fase 3 · Episodio piloto" \
  "Ensamblar tomas aprobadas según shotlist, subtítulos en zona segura, export 1080x1920."
echo "Listo. Revisa: gh issue list"
