#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v git >/dev/null 2>&1; then
  echo "[update] error: git is required." >&2
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "[update] error: working tree is not clean. Commit or stash changes first." >&2
  exit 1
fi

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "[update] pulling latest changes for branch: $CURRENT_BRANCH"
git pull --ff-only

echo "[update] running setup"
"$ROOT_DIR/scripts/setup_env.sh"

echo "[update] complete"
