@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion
title Qwen GEO One Click Pipeline
cd /d "%~dp0"

rem ============================================================
rem User config
rem ============================================================

set "INPUT_CSV=input\questions_w3_8.csv"
set "OUTPUT_ROOT=output"

set "PRODUCT_ID=hongmao"
set "PRODUCT_NAME=鸿茅药酒"

set "TARGET_ID=hongmao"
set "TARGET_ALIAS_1=鸿茅药酒"
set "TARGET_ALIAS_2=鸿茅"

set "OLLAMA_MODEL=qwen2.5:7b"
set "GEO_ROOT=D:\geo_analysis_system"


rem ============================================================
rem Fixed paths
rem ============================================================

set "QWEN_PYTHON=%~dp0.venv\Scripts\python.exe"
set "GEO_PYTHON=%GEO_ROOT%\.venv\Scripts\python.exe"
set "CENTRAL_IMPORTER=%GEO_ROOT%\scripts\import_platform_package.py"

set "OLLAMA_URL=http://127.0.0.1:11434/api/tags"
set "CDP_URL=http://127.0.0.1:9222/json/version"

if not exist "%OUTPUT_ROOT%" (
    mkdir "%OUTPUT_ROOT%"
)

set "STATE_FILE=%OUTPUT_ROOT%\.qwen_last_run.env"


rem ============================================================
rem Main menu
rem ============================================================

:MENU

echo.
echo ============================================================
echo Qwen GEO Collector
echo ============================================================
echo [1] Start new collection
echo [2] Resume last unfinished collection
echo [0] Exit
echo ============================================================
echo.

set "RUN_MODE="
set /p "RUN_MODE=Select: "

if "%RUN_MODE%"=="1" goto :NEW_RUN
if "%RUN_MODE%"=="2" goto :RESUME_RUN
if "%RUN_MODE%"=="0" exit /b 0

echo.
echo [ERROR] Invalid selection.
goto :MENU


rem ============================================================
rem New run
rem ============================================================

:NEW_RUN

for /f %%I in (
    'powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"'
) do (
    set "RUN_TS=%%I"
)

set "BATCH_ID=qwen-!RUN_TS!"
set "OUTPUT_DIR=%OUTPUT_ROOT%\run_!RUN_TS!"
set "PACKAGE_PATH=%OUTPUT_ROOT%\qwen_geo_!RUN_TS!.zip"

set "PACKAGE_ABS=%~dp0!PACKAGE_PATH!"

set "RESUME_ARG="
set "IS_RESUME=0"

goto :RUN_PIPELINE


rem ============================================================
rem Resume run
rem ============================================================

:RESUME_RUN

if not exist "%STATE_FILE%" (
    echo.
    echo [ERROR] No unfinished Qwen run was found.
    echo [STATE FILE] %STATE_FILE%
    echo.
    pause
    goto :MENU
)

set "RUN_TS="
set "BATCH_ID="
set "OUTPUT_DIR="
set "PACKAGE_PATH="

for /f "usebackq tokens=1,* delims==" %%A in (
    "%STATE_FILE%"
) do (
    set "%%A=%%B"
)

if not defined RUN_TS goto :INVALID_STATE
if not defined BATCH_ID goto :INVALID_STATE
if not defined OUTPUT_DIR goto :INVALID_STATE
if not defined PACKAGE_PATH goto :INVALID_STATE

if not exist "!OUTPUT_DIR!" (
    echo.
    echo [ERROR] Saved output directory does not exist:
    echo !OUTPUT_DIR!
    goto :INVALID_STATE
)

set "PACKAGE_ABS=%~dp0!PACKAGE_PATH!"

set "RESUME_ARG=--resume"
set "IS_RESUME=1"

echo.
echo [RESUME] Previous unfinished run loaded.
echo.

goto :RUN_PIPELINE


rem ============================================================
rem Common pre-checks
rem ============================================================

:RUN_PIPELINE

echo.
echo ============================================================
echo Qwen GEO One Click Pipeline
echo ============================================================
echo [MODE] !IS_RESUME!
echo [INPUT] %INPUT_CSV%
echo [OUTPUT] !OUTPUT_DIR!
echo [BATCH] !BATCH_ID!
echo [ZIP] !PACKAGE_PATH!
echo ============================================================
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


rem ============================================================
rem 1/4 Ollama
rem ============================================================

echo [1/4] Check Ollama

powershell -NoProfile -Command ^
"try { [void](Invoke-RestMethod -Uri '%OLLAMA_URL%' -TimeoutSec 2); exit 0 } catch { exit 1 }"

if errorlevel 1 (

    set "OLLAMA_EXE="

    for /f "delims=" %%O in (
        'where ollama.exe 2^>nul'
    ) do (
        if not defined OLLAMA_EXE (
            set "OLLAMA_EXE=%%O"
        )
    )

    if not defined OLLAMA_EXE (
        echo [ERROR] Ollama API is not running and ollama.exe was not found.
        echo Please start Ollama manually, then run this BAT again.
        goto :FAIL
    )

    echo [INFO] Starting Ollama server...

    start "" /min "!OLLAMA_EXE!" serve

    powershell -NoProfile -Command ^
    "$ok=$false; for($i=0;$i -lt 20;$i++){ try { [void](Invoke-RestMethod -Uri '%OLLAMA_URL%' -TimeoutSec 2); $ok=$true; break } catch { Start-Sleep -Seconds 1 } }; if($ok){exit 0}else{exit 1}"

    if errorlevel 1 (
        echo [ERROR] Ollama API did not become ready.
        goto :FAIL
    )
)

powershell -NoProfile -Command ^
"$r=Invoke-RestMethod -Uri '%OLLAMA_URL%' -TimeoutSec 5; $names=@($r.models.name)+@($r.models.model); if($names -contains '%OLLAMA_MODEL%'){exit 0}else{exit 1}"

if errorlevel 1 (
    echo [ERROR] Ollama model not found: %OLLAMA_MODEL%
    echo Run this command first:
    echo ollama pull %OLLAMA_MODEL%
    goto :FAIL
)

echo [PASS] Ollama ready
echo.


rem ============================================================
rem 2/4 Chrome CDP
rem ============================================================

echo [2/4] Check Chrome CDP 9222

curl.exe -fsS "%CDP_URL%" >nul 2>&1

if errorlevel 1 (

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
        echo [ERROR] Chrome not found.
        goto :FAIL
    )

    set "CHROME_PROFILE=%~dp0.qwen_chrome_profile"

    echo [INFO] Starting Chrome for Qwen GEO...

    start "" "!CHROME_EXE!" ^
        --remote-debugging-port=9222 ^
        --user-data-dir="!CHROME_PROFILE!" ^
        "https://www.qianwen.com/"

    powershell -NoProfile -Command ^
    "$ok=$false; for($i=0;$i -lt 20;$i++){ try { [void](Invoke-RestMethod -Uri '%CDP_URL%' -TimeoutSec 2); $ok=$true; break } catch { Start-Sleep -Seconds 1 } }; if($ok){exit 0}else{exit 1}"

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


rem ============================================================
rem Save state before collection starts
rem ============================================================

if "!IS_RESUME!"=="0" (

    if not exist "!OUTPUT_DIR!" (
        mkdir "!OUTPUT_DIR!"
    )

    >"%STATE_FILE%" (
        echo RUN_TS=!RUN_TS!
        echo BATCH_ID=!BATCH_ID!
        echo OUTPUT_DIR=!OUTPUT_DIR!
        echo PACKAGE_PATH=!PACKAGE_PATH!
    )

    echo [STATE] New run state saved:
    echo %STATE_FILE%
    echo.
)


rem ============================================================
rem 3/4 Qwen pipeline
rem ============================================================

echo [3/4] Run Qwen collection, analysis and package export

"%QWEN_PYTHON%" ^
    -m app.qwen.pipeline ^
    --input "%INPUT_CSV%" ^
    --output "!OUTPUT_DIR!" ^
    --package "!PACKAGE_PATH!" ^
    --batch-id "!BATCH_ID!" ^
    --product-id "%PRODUCT_ID%" ^
    --product-name "%PRODUCT_NAME%" ^
    --target-id "%TARGET_ID%" ^
    --target-alias "%TARGET_ALIAS_1%" ^
    --target-alias "%TARGET_ALIAS_2%" ^
    !RESUME_ARG!

set "PIPELINE_EXIT=!ERRORLEVEL!"

if not "!PIPELINE_EXIT!"=="0" (

    echo.

    rem --------------------------------------------------------
    rem Check whether this was an intentional blocked/pause state
    rem --------------------------------------------------------

    if exist "!OUTPUT_DIR!\batch_summary.json" (

        powershell -NoProfile -Command ^
        "$p='!OUTPUT_DIR!\batch_summary.json'; try { $s=ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 $p); if($s.status -eq 'blocked' -or $s.status -eq 'partial'){exit 0}else{exit 1} } catch { exit 1 }"

        if not errorlevel 1 (
            goto :PAUSED
        )
    )

    echo [ERROR] Qwen GEO pipeline failed.
    echo [EXIT CODE] !PIPELINE_EXIT!
    echo [PARTIAL OUTPUT] !OUTPUT_DIR!
    goto :FAIL
)

if not exist "!PACKAGE_PATH!" (
    echo [ERROR] ZIP was not created:
    echo !PACKAGE_PATH!
    goto :FAIL
)

echo [PASS] Qwen pipeline completed
echo.


rem ============================================================
rem 4/4 Validate final ZIP
rem ============================================================

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

"%GEO_PYTHON%" ^
    "%CENTRAL_IMPORTER%" ^
    --package "!PACKAGE_ABS!" ^
    --validate-only

if errorlevel 1 (
    echo.
    echo [ERROR] GEO central validation failed.
    goto :FAIL
)


rem ============================================================
rem Success
rem ============================================================

if exist "%STATE_FILE%" (
    del /q "%STATE_FILE%"
)

echo.
echo ============================================================
echo SUCCESS
echo ============================================================
echo ZIP is ready for GEO frontend import:
echo !PACKAGE_ABS!
echo.
echo Resume state has been cleared.
echo ============================================================
echo.

explorer.exe /select,"!PACKAGE_ABS!"

pause
exit /b 0


rem ============================================================
rem Paused because quota/risk/refusal blocked collection
rem ============================================================

:PAUSED

echo.
echo ============================================================
echo COLLECTION INCOMPLETE
echo ============================================================
echo.
echo The current batch is BLOCKED or PARTIAL.
echo No final ZIP was generated.
echo.
echo Output directory:
echo !OUTPUT_DIR!
echo.
echo Resume state:
echo %STATE_FILE%
echo.
echo If the current Qwen account has no remaining quota:
echo.
echo   1. Open the Qwen Chrome window.
echo   2. Sign out of the current account.
echo   3. Sign in to another authorized account.
echo   4. Confirm Qwen works normally.
echo   5. Run this BAT again.
echo   6. Select [2] Resume last unfinished collection.
echo.
echo Previously PASS tasks will be skipped.
echo Failed or blocked tasks will be executed again.
echo ============================================================
echo.

pause
exit /b !PIPELINE_EXIT!


rem ============================================================
rem Invalid saved state
rem ============================================================

:INVALID_STATE

echo.
echo ============================================================
echo INVALID RESUME STATE
echo ============================================================
echo State file:
echo %STATE_FILE%
echo.
echo Delete the state file if this old run is no longer needed.
echo ============================================================
echo.

pause
exit /b 1


rem ============================================================
rem Generic failure
rem ============================================================

:FAIL

echo.
echo ============================================================
echo FAILED
echo ============================================================
echo Please read the error above.
echo.
echo The resume state is NOT deleted automatically.
echo ============================================================
echo.

pause
exit /b 1
