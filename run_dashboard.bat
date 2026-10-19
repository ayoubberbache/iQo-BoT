@echo off
TITLE IQO Bot - Chemistry AI Terminal Dashboard
color 0F
cls
cd /d "%~dp0"
set PYTHONPATH=%CD%

if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
) else (
    set PYTHON_EXE=python
)

%PYTHON_EXE% chemistry_ai\dashboard.py

echo.
pause >nul
