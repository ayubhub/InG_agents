# Start InG AI Sales Department Agents
# Get script directory and change to it
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Remove stale PID
if (Test-Path "data\state\main.pid") {
    Remove-Item "data\state\main.pid" -Force
    Write-Host "Removed stale PID file"
}

# Activate venv and start agents
Write-Host "Starting agents..."
& .\venv\Scripts\python.exe main.py

