#!/usr/bin/env python3
"""Check and display agent logs"""
import os
import sys
from pathlib import Path
import time

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

print("Waiting for agents to initialize...")
time.sleep(15)

log_path = Path("data/logs/agents.log")
pid_path = Path("data/state/main.pid")

print("\n" + "="*60)
print("AGENT STATUS CHECK")
print("="*60)

if pid_path.exists():
    print(f"✅ PID file exists: {pid_path.read_text().strip()}")
else:
    print("❌ PID file not found")

if log_path.exists():
    size = log_path.stat().st_size
    print(f"✅ Log file exists: {size} bytes")
    if size > 0:
        print("\n" + "="*60)
        print("AGENTS LOG CONTENT")
        print("="*60)
        print(log_path.read_text())
        print("="*60)
    else:
        print("⚠️ Log file is empty")
else:
    print("❌ Log file does not exist yet")

sys.exit(0)


