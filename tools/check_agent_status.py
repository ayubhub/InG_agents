#!/usr/bin/env python3
"""Comprehensive agent status check"""
import os
import sys
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

import psutil
import time

results = []
results.append("="*70)
results.append("ING AI SALES DEPARTMENT - AGENT STATUS REPORT")
results.append("="*70)
results.append("")

# Check PID file
pid_file = Path('data/state/main.pid')
if pid_file.exists():
    try:
        pid = int(pid_file.read_text().strip())
        if psutil.pid_exists(pid):
            try:
                proc = psutil.Process(pid)
                cmdline = ' '.join(proc.cmdline())
                if 'main.py' in cmdline or 'InG_agents' in cmdline:
                    results.append(f"✅ Main process RUNNING")
                    results.append(f"   PID: {pid}")
                    results.append(f"   Status: {proc.status()}")
                    results.append(f"   Started: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(proc.create_time()))}")
                else:
                    results.append(f"⚠️ PID {pid} exists but is not our process")
                    results.append(f"   Command: {cmdline[:100]}")
            except Exception as e:
                results.append(f"❌ Error checking process {pid}: {e}")
        else:
            results.append(f"❌ Stale PID file: Process {pid} does not exist")
    except Exception as e:
        results.append(f"❌ Invalid PID file: {e}")
else:
    results.append("❌ No PID file - Agents are NOT running")

results.append("")

# Check log file
log_file = Path('data/logs/agents.log')
if log_file.exists():
    size = log_file.stat().st_size
    results.append(f"✅ Log file exists: {size} bytes")
    if size > 0:
        results.append("")
        results.append("RECENT LOG ENTRIES:")
        results.append("-"*70)
        content = log_file.read_text()
        # Show last 50 lines
        lines = content.split('\n')
        recent = lines[-50:] if len(lines) > 50 else lines
        results.append('\n'.join(recent))
        results.append("-"*70)
    else:
        results.append("⚠️ Log file is empty - Agents may not have started logging yet")
else:
    results.append("❌ Log file does not exist - Agents have not started logging")

results.append("")

# Check for Python processes
results.append("Python processes:")
python_procs = []
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if 'python' in proc.info['name'].lower():
            cmdline = ' '.join(proc.info.get('cmdline', []))
            if 'main.py' in cmdline or 'InG_agents' in cmdline:
                python_procs.append(proc)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

if python_procs:
    results.append(f"✅ Found {len(python_procs)} Python process(es) running agents:")
    for proc in python_procs:
        results.append(f"   PID {proc.info['pid']}: {proc.info['name']}")
else:
    results.append("❌ No Python processes found running agents")

results.append("")

# Check configuration files
results.append("Configuration files:")
env_file = Path('.env')
config_file = Path('config/agents.yaml')
results.append(f"  .env: {'✅ EXISTS' if env_file.exists() else '❌ MISSING'}")
results.append(f"  config/agents.yaml: {'✅ EXISTS' if config_file.exists() else '❌ MISSING'}")

results.append("")
results.append("="*70)

# Print results
output = '\n'.join(results)
print(output)

# Write to file
Path('agent_status_report.txt').write_text(output)


