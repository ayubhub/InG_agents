#!/usr/bin/env python3
"""Get and display agent logs"""
import os
import sys
from pathlib import Path
import time

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

# Wait for agents to initialize
print("Waiting for agents to initialize...")
time.sleep(30)

output = []
output.append("="*70)
output.append("ING AI SALES DEPARTMENT - OPERATIONAL LOGS")
output.append("="*70)
output.append("")

# Check PID file
pid_file = Path("data/state/main.pid")
if pid_file.exists():
    pid = pid_file.read_text().strip()
    output.append(f"✅ Main process PID: {pid}")
else:
    output.append("❌ No PID file found")

output.append("")

# Check log file
log_file = Path("data/logs/agents.log")
if log_file.exists():
    size = log_file.stat().st_size
    output.append(f"✅ Log file exists: {size} bytes")
    if size > 0:
        output.append("")
        output.append("LOG CONTENT:")
        output.append("-"*70)
        content = log_file.read_text()
        output.append(content)
        output.append("-"*70)
    else:
        output.append("⚠️ Log file is empty")
else:
    output.append("❌ Log file does not exist")

output.append("")
output.append("="*70)

# Write to file
result_file = Path("operational_logs.txt")
result_file.write_text("\n".join(output))

# Also print
print("\n".join(output))


