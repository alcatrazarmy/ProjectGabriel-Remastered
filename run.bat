@echo off
chcp 65001 > nul 2>&1
setlocal

title ProjectYelena
cd /d "%~dp0"
if not defined YELENA_PARAKEET_RUNTIME_DIR set "YELENA_PARAKEET_RUNTIME_DIR=A:\Tools\yelena-parakeet"
if not defined HF_HOME set "HF_HOME=D:\Caches\huggingface"
if not defined TORCH_HOME set "TORCH_HOME=D:\Caches\torch"
if not defined MPLCONFIGDIR set "MPLCONFIGDIR=D:\Caches\matplotlib"

if not defined YELENA_PYTHON (
    if exist ".venv\Scripts\python.exe" (
        set "YELENA_PYTHON=%~dp0.venv\Scripts\python.exe"
    ) else (
        set "YELENA_PYTHON=A:\Tools\gabriel-venv\Scripts\python.exe"
    )
)

if not exist "%YELENA_PYTHON%" (
    echo   Python environment not found. Set YELENA_PYTHON to its python.exe.
    echo.
    pause
    exit /b 1
)

for %%I in ("%YELENA_PYTHON%") do set "PATH=%%~dpI;%PATH%"
"%YELENA_PYTHON%" -B scripts\ensure_local_voice.py
if errorlevel 1 (
    echo   Voice service is not ready. See the message above.
    pause
    exit /b 1
)
echo   Starting ProjectYelena...
echo   Press Ctrl+C to stop.
echo.

"%YELENA_PYTHON%" supervisor.py
exit /b %errorlevel%
