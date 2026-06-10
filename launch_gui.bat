@echo off
setlocal enabledelayedexpansion
title Gateway Changer

set "PYTHON_EXE="

:: First check known good paths
set "PYTHON_PATHS="
set PYTHON_PATHS=%PYTHON_PATHS%;C:\Users\Administrator\python-sdk\python3.13.2\python.exe
set PYTHON_PATHS=%PYTHON_PATHS%;C:\Python313\python.exe
set PYTHON_PATHS=%PYTHON_PATHS%;C:\Python312\python.exe
set PYTHON_PATHS=%PYTHON_PATHS%;C:\Program Files\Python313\python.exe
set PYTHON_PATHS=%PYTHON_PATHS%;C:\Program Files\Python312\python.exe
set PYTHON_PATHS=%PYTHON_PATHS%;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe
set PYTHON_PATHS=%PYTHON_PATHS%;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe

:: Search for Python in known paths first
for %%p in (%PYTHON_PATHS%) do (
    if exist "%%p" (
        set PYTHON_EXE=%%p
        goto :RUN_APP
    )
)

:: Then check PATH (last resort, may find Microsoft Store stub)
for %%p in (python.exe) do (
    where %%p >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_EXE=%%p
        goto :RUN_APP
    )
)

:: If still not found
echo ERROR: Python interpreter not found
echo.
echo Please check if Python is installed at:
echo C:\Users\Administrator\python-sdk\python3.13.2\python.exe
echo.
pause
exit /b 1

:RUN_APP
echo Found Python: %PYTHON_EXE%
echo Starting Gateway Changer...
"%PYTHON_EXE%" "%~dp0gateway_gui.py"
endlocal