#!/bin/bash

PROJECT_NAME="QI2026_group_B"

if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v uv &> /dev/null; then
    echo ""
    echo "ERROR: uv was installed but cannot be found in PATH."
    echo "Please close this terminal, open a new one, and re-run setup.sh"
    exit 1
fi

echo "Creating venv with Python 3.11+ (uv will fetch it if missing)..."
uv venv --python 3.11 --prompt "$PROJECT_NAME"

echo "Installing project and dependencies..."
uv pip install -e .

echo "Done! To activate, run: source .venv/bin/activate"