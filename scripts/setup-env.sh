#!/usr/bin/env bash
set -euo pipefail
PROJECT_PATH="${1:-.}"
PYTHON_EXE="${2:-python3}"

cd "$PROJECT_PATH" || exit 1

if [[ -f "pyproject.toml" || -f "requirements.txt" || -f "setup.py" ]]; then
  echo "Detected Python project in $PROJECT_PATH"
  VENV_PATH="$PROJECT_PATH/.venv"
  if [[ ! -d "$VENV_PATH" ]]; then
    "$PYTHON_EXE" -m venv "$VENV_PATH"
  fi
  PIP="$VENV_PATH/bin/pip"
  if command -v poetry >/dev/null 2>&1 && [[ -f "pyproject.toml" ]]; then
    echo "Using poetry install"
    poetry install
  else
    if [[ -f "requirements.txt" ]]; then
      "$PIP" install --upgrade pip
      "$PIP" install -r requirements.txt
    else
      "$PIP" install --upgrade pip setuptools wheel
      if [[ -f "setup.py" ]]; then
        "$PIP" install -e .
      fi
    fi
  fi
  echo "Python env ready at $VENV_PATH"
  echo "Activate with: source $VENV_PATH/bin/activate"
elif [[ -f "package.json" ]]; then
  echo "Detected Node project in $PROJECT_PATH"
  if [[ -f "package-lock.json" ]]; then
    npm ci
  else
    npm install
  fi
  echo "Node deps installed"
else
  echo "No recognized project files. Skipping $PROJECT_PATH"
fi
