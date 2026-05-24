@echo off
chcp 65001 >nul 2>&1

set "PROJECT_NAME=QI2026_group_B"

where uv >nul 2>&1
if errorlevel 1 (
    echo Installing uv...
    powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

where uv >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: uv was installed but cannot be found in PATH.
    echo Please close this terminal, open a new one, and re-run setup.bat
    exit /b 1
)

echo Creating venv and installing dependencies...
uv sync

echo.
echo Done! Run experiments with:
echo   uv run python -m surface_code_study.experiments.exp3_platform_compare --d 3 5 7
echo   uv run pytest surface_code_study/tests/ -v
