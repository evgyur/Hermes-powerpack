#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"

"$PYTHON_BIN" -m venv "$VENV_DIR"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -e .

mkdir -p "$HOME/.local/bin"
ln -sf "$ROOT/$VENV_DIR/bin/hermes" "$HOME/.local/bin/hermes"

case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc" ;;
esac

echo "Hermes Powerpack installed. Next:"
echo "  export PATH=\"$HOME/.local/bin:\$PATH\""
echo "  hermes setup"
echo "  hermes doctor"
