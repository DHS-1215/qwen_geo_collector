@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] .venv Python not found.
    pause
    exit /b 1
)

"%PYTHON_EXE%" scripts\build_ollama_model_package.py

if errorlevel 1 (
    echo.
    echo [ERROR] Ollama model package build failed.
    pause
    exit /b 1
)

echo.
echo [PASS] Ollama offline model package created.
pause
