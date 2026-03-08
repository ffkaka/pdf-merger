#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[setup] project root: $ROOT_DIR"

mkdir -p output/pdf tmp/pdfs

if ! command -v python3 >/dev/null 2>&1; then
  echo "[setup] error: python3 is required." >&2
  exit 1
fi

if command -v uv >/dev/null 2>&1; then
  echo "[setup] installing Python packages with uv"
  uv pip install --system pypdf pdfplumber reportlab
else
  echo "[setup] installing Python packages with pip"
  python3 -m pip install --upgrade pip
  python3 -m pip install pypdf pdfplumber reportlab
fi

if command -v codex >/dev/null 2>&1; then
  echo "[setup] ensuring codex pdf skill"
  codex skill install pdf || echo "[setup] warning: codex skill install pdf failed (continuing)"
else
  echo "[setup] warning: codex command not found, skipping skill install"
fi

if ! command -v pdftoppm >/dev/null 2>&1; then
  echo "[setup] warning: pdftoppm not found (Poppler required for rendering checks)"
fi

if ! command -v gs >/dev/null 2>&1; then
  echo "[setup] warning: gs not found (Ghostscript recommended for fallback merge/compression)"
fi

chmod +x "$ROOT_DIR/pmerge" "$ROOT_DIR/scripts/setup_env.sh" "$ROOT_DIR/scripts/update_env.sh" 2>/dev/null || true

echo "[setup] complete"
