#!/bin/bash
set -e

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

echo "Creating venv and installing dependencies..."
uv sync

echo ""
echo "Done! Run experiments with:"
echo "  uv run python -m surface_code_study.experiments.exp3_platform_compare --d 3 5 7"
echo "  uv run pytest surface_code_study/tests/ -v"
