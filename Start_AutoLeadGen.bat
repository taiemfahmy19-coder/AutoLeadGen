@echo off
setlocal enabledelayedexpansion

:: Navigate to project directory regardless of execution context
cd /d "%~dp0"

:: 1. Detect Python command
set "PY_CMD="

where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :RUN_APP
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :RUN_APP
)

:: If Python is not found in PATH, check common installation paths
if exist "C:\Python314\python.exe" (
    set "PY_CMD=C:\Python314\python.exe"
    goto :RUN_APP
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :RUN_APP
)

:: Python not found
powershell -Command "[System.Windows.Forms.MessageBox]::Show('لم يتم العثور على Python مثبت على هذا الجهاز. يرجى تثبيت Python 3.10+ للمتابعة.', 'AutoLeadGen - خطأ', [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
)
exit /b 1

:RUN_APP
:: Run the launcher python script
"%PY_CMD%" launch.py

exit /b %errorlevel%
