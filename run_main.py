#!/usr/bin/env python3
"""
Simple wrapper to run main.py using venv Python.
This script automatically uses the venv Python interpreter.
Works on Windows, Linux, and Git Bash.
"""
import sys
import os
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

# Determine venv Python path based on OS
if sys.platform == "win32":
    venv_python = script_dir / "venv" / "Scripts" / "python.exe"
else:
    venv_python = script_dir / "venv" / "bin" / "python"

# Check if venv Python exists
if not venv_python.exists():
    print(f"Error: venv Python not found at {venv_python}")
    print("Please ensure venv is set up correctly.")
    print(f"Current directory: {os.getcwd()}")
    sys.exit(1)

# Run main.py with venv Python
import subprocess
result = subprocess.run([str(venv_python), "main.py"] + sys.argv[1:])
sys.exit(result.returncode)

