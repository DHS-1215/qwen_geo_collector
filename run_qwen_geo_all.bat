@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Qwen GEO One Click Pipeline
cd /d "%~dp0"

rem ===== User config =====
set "INPUT_CSV=input\questions_w3_8.csv"
set "OUTPUT_ROOT=output"
set "PRODUCT_ID=hongmao"
set "PRODUCT_NAME=ºèÃ©Ò©¾Æ"
set "TARGET_ID=hongmao"
set "TARGET_ALIAS_1=ºèÃ©Ò©¾Æ"
set "TARGET_ALIAS_2=ºèÃ©"
set "OLLAMA_MODEL=qwen2.5:7b"
set "GEO_ROOT=D:\geo_analysis_system"

rem ===== Fixed paths =====
set "QWEN_PYTHON=%~dp0.venv\Scripts\python.exe"
set "GEO_PYTHON=%GEO_ROOT%\.venv\Scripts\python.exe"
set "CENTRAL_IMPORTER=%GEO_ROOT%\scripts\import_platform_package.py"
set "OLLAMA_URL=http://127.0.0.1:11434/api/tags"
set "CDP_URL=http://127.0.0.1:9222/json/version"

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "RUN_TS=%%I"

set "BATCH_ID=qwen-%RUN_TS%"
set "OUTPUT_DIR=%OUTPUT_ROOT%\run_%RUN_TS%"
set "PACKAGE_PATH=%OUTPUT_ROOT%\qwen_geo_%RUN_TS%.zip"
set "PACKAGE_ABS=%~dp0%PACKAGE_PATH%"

echo ============================================================
echo Qwen GEO One Click Pipeline
echo ============================================================
echo [INPUT] %INPUT_CSV%
echo [OUTPUT] %OUTPUT_DIR%
echo [BATCH] %BATCH_ID%
echo [ZIP] %PACKAGE_PATH%
echo.

if not exist "%QWEN_PYTHON%" (
    echo [ERROR] Qwen virtualenv python not found:
    echo %QWEN_PYTHON%
    goto :FAIL
)

if not exist "%INPUT_CSV%" (
    echo [ERROR] Input CSV not found:
    echo %INPUT_CSV%
    goto :FAIL
)

if not exist "%OUTPUT_ROOT%" mkdir "%OUTPUT_ROOT%"

echo [1/4] Check Ollama
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri '%OLLAMA_URL%' -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    set "OLLAMA_EXE="
    for /f "delims=" %%O in ('where ollama.exe 2^>nul') do (
        if not defined OLLAMA_EXE set "OLLAMA_EXE=%%O"
    )

    if not defined OLLAMA_EXE (
        echo [ERROR] Ollama API is not running and ollama.exe was not found.
        echo Please start Ollama manually, then run this BAT again.
        goto :FAIL
    )

    echo [INFO] Starting Ollama server...
    start "" /min "!OLLAMA_EXE!" serve

    powershell -NoProfile -Command "$ok=$false; for($i=0;$i -lt 20;$i++){ try { Invoke-RestMethod -Uri '%OLLAMA_URL%' -TimeoutSec 2 | Out-Null; $ok=$true; break } catch { Start-Sleep -Seconds 1 } }; if($ok){exit 0}else{exit 1}"
    if errorlevel 1 (
        echo [ERROR] Ollama API did not become ready.
        goto :FAIL
    )
)

powershell -NoProfile -Command "$r=Invoke-RestMethod -Uri '%OLLAMA_URL%' -TimeoutSec 5; if(($r.models.name -join \"`n\") -match '^%OLLAMA_MODEL%(:|$)' -or ($r.models.model -join \"`n\") -match '^%OLLAMA_MODEL%(:|$)'){exit 0}else{exit 1}"
if errorlevel 1 (
    echo [ERROR] Ollama model not found: %OLLAMA_MODEL%
    echo Run this command first:
    echo ollama pull %OLLAMA_MODEL%
    goto :FAIL
)
echo [PASS] Ollama ready
echo.

echo [2/4] Check Chrome CDP 9222
curl.exe -fsS "%CDP_URL%" >nul 2>&1
if errorlevel 1 (
    set "CHROME_EXE="

    if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
    if not defined CHROME_EXE if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
    if not defined CHROME_EXE if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"

    if not defined CHROME_EXE (
        echo [ERROR] Chrome not found.
        goto :FAIL
    )

    set "CHROME_PROFILE=%~dp0.qwen_chrome_profile"
    echo [INFO] Starting Chrome for Qwen GEO...
    start "" "!CHROME_EXE!" --remote-debugging-port=9222 --user-data-dir="!CHROME_PROFILE!" "https://www.qianwen.com/"

    powershell -NoProfile -Command "$ok=$false; for($i=0;$i -lt 20;$i++){ try { Invoke-RestMethod -Uri '%CDP_URL%' -TimeoutSec 2 | Out-Null; $ok=$true; break } catch { Start-Sleep -Seconds 1 } }; if($ok){exit 0}else{exit 1}"
    if errorlevel 1 (
        echo [ERROR] Chrome CDP did not become ready.
        goto :FAIL
    )

    echo.
    echo If this is the first run, sign in to Qwen in the Chrome window.
    echo After the Qwen chat page is ready, return here.
    pause
)
echo [PASS] Chrome CDP ready
echo.

echo [3/4] Run Qwen collection, analysis and package export
"%QWEN_PYTHON%" -m app.qwen.pipeline --input "%INPUT_CSV%" --output "%OUTPUT_DIR%" --package "%PACKAGE_PATH%" --batch-id "%BATCH_ID%" --product-id "%PRODUCT_ID%" --product-name "%PRODUCT_NAME%" --target-id "%TARGET_ID%" --target-alias "%TARGET_ALIAS_1%" --target-alias "%TARGET_ALIAS_2%"

if errorlevel 1 (
    echo.
    echo [ERROR] Qwen GEO pipeline failed.
    echo Partial output:
    echo %OUTPUT_DIR%
    goto :FAIL
)

if not exist "%PACKAGE_PATH%" (
    echo [ERROR] ZIP was not created:
    echo %PACKAGE_PATH%
    goto :FAIL
)
echo [PASS] Qwen pipeline completed
echo.

echo [4/4] Validate ZIP with GEO Analysis System
if not exist "%GEO_PYTHON%" (
    echo [ERROR] GEO virtualenv python not found:
    echo %GEO_PYTHON%
    goto :FAIL
)

if not exist "%CENTRAL_IMPORTER%" (
    echo [ERROR] GEO central importer not found:
    echo %CENTRAL_IMPORTER%
    goto :FAIL
)

"%GEO_PYTHON%" "%CENTRAL_IMPORTER%" --package "%PACKAGE_ABS%" --validate-only
if errorlevel 1 (
    echo.
    echo [ERROR] GEO central validation failed.
    goto :FAIL
)

echo.
echo ============================================================
echo SUCCESS
echo ============================================================
echo ZIP is ready for GEO frontend import:
echo %PACKAGE_ABS%
echo ============================================================
echo.

explorer.exe /select,"%PACKAGE_ABS%"
pause
exit /b 0

:FAIL
echo.
echo ============================================================
echo FAILED
echo ============================================================
echo Please read the error above.
echo ============================================================
pause
exit /b 1
