#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  if command -v uv >/dev/null 2>&1; then
    PYTHON_BIN="$(uv python find 3.11)"
  else
    PYTHON_BIN="$(command -v python3.11 || true)"
  fi
fi

if [[ -z "$PYTHON_BIN" || ! -x "$PYTHON_BIN" ]]; then
  echo "ERROR: Python 3.11 was not found."
  echo "Install/select Python 3.11, or set PYTHON_BIN=/path/to/python3.11."
  exit 1
fi

"$PYTHON_BIN" -c 'import sys; print("Selected Python:", sys.version)'
"$PYTHON_BIN" -c 'import sys; assert sys.version_info[:2] == (3, 11), "Use Python 3.11 for this tested target"'

if [[ ! -d .venv-osken ]]; then
  "$PYTHON_BIN" -m venv .venv-osken
fi

if command -v uv >/dev/null 2>&1; then
  uv pip install --python .venv-osken/bin/python -r requirements.txt
else
  .venv-osken/bin/python -m pip install --upgrade pip
  .venv-osken/bin/python -m pip install -r requirements.txt
fi

.venv-osken/bin/osken-manager --version
.venv-osken/bin/python -c 'import os_ken; print("OS-Ken import: OK")'
echo "Environment setup completed. This does not yet prove controller/OVS integration."
