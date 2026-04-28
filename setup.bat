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

echo Creating venv with Python 3.11+ (uv will fetch it if missing)...
uv venv --python 3.11 --prompt "%PROJECT_NAME%"

echo Installing project and dependencies...
uv pip install -e .

echo Done!
echo To activate:
echo   PowerShell:  .\.venv\Scripts\Activate.ps1
echo   cmd:         .venv\Scripts\activate.bat