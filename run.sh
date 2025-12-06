#!/bin/bash
# Start InG AI Sales Department Agents using venv

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Remove stale PID
if [ -f "data/state/main.pid" ]; then
    rm -f "data/state/main.pid"
    echo "Removed stale PID file"
fi

# Activate venv and start agents
echo "Starting agents..."
./venv/Scripts/python.exe main.py



