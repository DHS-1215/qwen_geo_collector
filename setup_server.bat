@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Qwen GEO Server Setup
cd /d "%~dp0"

set "OLLAMA_MODEL=qwen2.5:7b"
set "OLLAMA_URL=http://127.0.0.1:11434/api/tags"
set "QWEN_PYTHON=%~dp0.venv\Scripts\python.exe"

echo ============================================================
echo Qwen GEO Server Setup
echo ============================================================
echo Project:
echo %CD%
echo.

rem ============================================================
rem 1/7 Python
rem ============================================================

echo [1/7] Check Python 3.11

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found.
    echo Please install Python 3.11 x64 first.
    goto :FAIL
)

for /f "tokens=2" %%V in ('python --version 2^>^&1') do (
    set "PYTHON_VERSION=%%V"
)

echo [INFO] Python !PYTHON_VERSION!

for /f "tokens=1,2 delims=." %%A in ("!PYTHON_VERSION!") do (
    set "PY_MAJOR=%%A"
    set "PY_MINOR=%%B"
)

if not "!PY_MAJOR!"=="3" (
    echo [ERROR] Python 3.11 is required.
    goto :FAIL
)

if not "!PY_MINOR!"=="11" (
    echo [ERROR] Python 3.11 is required.
    goto :FAIL
)

echo [PASS] Python 3.11 ready
echo.

rem ============================================================
rem 2/7 Chrome
rem ============================================================

echo [2/7] Check Google Chrome

set "CHROME_EXE="

if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
)

if not defined CHROME_EXE (
    if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
        set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
    )
)

if not defined CHROME_EXE (
    if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
        set "CHROME_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"
    )
)

if not defined CHROME_EXE (
    echo [ERROR] Google Chrome was not found.
    echo Install Google Chrome and run setup again.
    goto :FAIL
)

echo [PASS] Chrome found:
echo !CHROME_EXE!
echo.

rem ============================================================
rem 3/7 Ollama
rem ============================================================

echo [3/7] Check Ollama

set "OLLAMA_EXE="

for /f "delims=" %%O in ('where ollama.exe 2^>nul') do (
    if not defined OLLAMA_EXE (
        set "OLLAMA_EXE=%%O"
    )
)

if not defined OLLAMA_EXE (
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
    )
)

if not defined OLLAMA_EXE (
    if exist "%ProgramFiles%\Ollama\ollama.exe" (
        set "OLLAMA_EXE=%ProgramFiles%\Ollama\ollama.exe"
    )
)

if not defined OLLAMA_EXE (
    echo [INFO] Ollama is not installed.
    echo [INFO] Installing Ollama with winget...

    winget --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] winget was not found.
        echo Install Ollama manually, then run setup again.
        goto :FAIL
    )

    winget install --id Ollama.Ollama -e ^
        --accept-source-agreements ^
        --accept-package-agreements

    if errorlevel 1 (
        echo [ERROR] Ollama installation failed.
        goto :FAIL
    )

    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
    )

    if not defined OLLAMA_EXE (
        if exist "%ProgramFiles%\Ollama\ollama.exe" (
            set "OLLAMA_EXE=%ProgramFiles%\Ollama\ollama.exe"
        )
    )
)

if not defined OLLAMA_EXE (
    echo [ERROR] Ollama executable was not found after installation.
    echo Reopen PowerShell or Windows, then run setup again.
    goto :FAIL
)

echo [INFO] Ollama:
echo !OLLAMA_EXE!

powershell -NoProfile -Command ^
"try { [void](Invoke-RestMethod -Uri '%OLLAMA_URL%' -TimeoutSec 2); exit 0 } catch { exit 1 }"

if errorlevel 1 (
    echo [INFO] Starting Ollama server...

    start "" /min "!OLLAMA_EXE!" serve

    powershell -NoProfile -Command ^
    "$ok=$false; for($i=0;$i -lt 30;$i++){ try { [void](Invoke-RestMethod -Uri '%OLLAMA_URL%' -TimeoutSec 2); $ok=$true; break } catch { Start-Sleep -Seconds 1 } }; if($ok){exit 0}else{exit 1}"

    if errorlevel 1 (
        echo [ERROR] Ollama API did not become ready.
        goto :FAIL
    )
)

echo [PASS] Ollama ready
echo.

rem ============================================================
rem 4/7 Ollama model
rem ============================================================

echo [4/7] Prepare Ollama model: %OLLAMA_MODEL%

"!OLLAMA_EXE!" pull "%OLLAMA_MODEL%"

if errorlevel 1 (
    echo [ERROR] Failed to prepare Ollama model.
    goto :FAIL
)

echo [PASS] Ollama model ready
echo.

rem ============================================================
rem 5/7 Virtual environment
rem ============================================================

echo [5/7] Prepare Python virtual environment

if not exist "%QWEN_PYTHON%" (
    python -m venv .venv

    if errorlevel 1 (
        echo [ERROR] Failed to create .venv
        goto :FAIL
    )
)

if not exist "%QWEN_PYTHON%" (
    echo [ERROR] Virtualenv Python was not created.
    goto :FAIL
)

echo [PASS] Virtualenv ready
echo.

rem ============================================================
rem 6/7 Python dependencies
rem ============================================================

echo [6/7] Install Python dependencies

"%QWEN_PYTHON%" -m pip install --upgrade pip

if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    goto :FAIL
)

"%QWEN_PYTHON%" -m pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install requirements.txt
    goto :FAIL
)

echo [PASS] Python dependencies installed
echo.

rem ============================================================
rem 7/7 Self check
rem ============================================================

echo [7/7] Run project self-check

"%QWEN_PYTHON%" -m pip check
if errorlevel 1 (
    echo [ERROR] pip check failed.
    goto :FAIL
)

"%QWEN_PYTHON%" -m compileall app
if errorlevel 1 (
    echo [ERROR] compileall failed.
    goto :FAIL
)

"%QWEN_PYTHON%" -m app.qwen.pipeline --help >nul
if errorlevel 1 (
    echo [ERROR] Qwen pipeline CLI self-check failed.
    goto :FAIL
)

if not exist "output" (
    mkdir output
)

echo.
echo ============================================================
echo SERVER SETUP SUCCESS
echo ============================================================
echo.
echo Next:
echo.
echo 1. Run run_qwen_geo_all.bat
echo 2. Chrome will open automatically if CDP is not running.
echo 3. Sign in to Qwen manually in that Chrome window.
echo 4. Return to the terminal and continue.
echo.
echo Human verification and account switching remain manual.
echo ============================================================
echo.

pause
exit /b 0

:FAIL
echo.
echo ============================================================
echo SERVER SETUP FAILED
echo ============================================================
echo Please read the error above and run setup again.
echo ============================================================
echo.

pause
exit /b 1
