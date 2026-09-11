#!/usr/bin/env bash
# Instalación en Mac (Apple Silicon). Uso:  bash scripts/setup_mac.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> 1/6 Homebrew"
if ! command -v brew >/dev/null 2>&1; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

echo "==> 2/6 Herramientas del sistema (git, ffmpeg, node, uv)"
brew install git ffmpeg node uv

echo "==> 3/6 Dependencias Python del proyecto"
uv python install 3.12
uv sync --extra dev

echo "==> 4/6 Claude Code"
if ! command -v claude >/dev/null 2>&1; then
  npm install -g @anthropic-ai/claude-code
fi

echo "==> 5/6 Archivo de claves"
[ -f .env ] || cp .env.example .env

echo "==> 6/6 Pruebas y diagnóstico"
uv run pytest -q
uv run showrunner doctor

echo ""
echo "Instalación terminada. Siguiente paso: abre .env y pega tus claves (ver docs/PLAN_ACCIONES.md)."
