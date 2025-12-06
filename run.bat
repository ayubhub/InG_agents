@echo off
REM Start InG AI Sales Department Agents using venv

cd /d "%~dp0"

REM Remove stale PID
if exist "data\state\main.pid" (
    del /f "data\state\main.pid"
    echo Removed stale PID file
)

REM Activate venv and start agents
echo Starting agents...
.\venv\Scripts\python.exe main.py



