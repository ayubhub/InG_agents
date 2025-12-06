#!/usr/bin/env python3
"""View agent operational logs"""
import os
import sys
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

log_file = Path('data/logs/agents.log')
pid_file = Path('data/state/main.pid')

print('\n' + '='*70)
print('ING AI SALES DEPARTMENT - OPERATIONAL LOGS')
print('='*70)
print()

if pid_file.exists():
    print(f'✅ Main process PID: {pid_file.read_text().strip()}')
else:
    print('⚠️ No PID file found (agents may not be running)')

print()

if log_file.exists():
    size = log_file.stat().st_size
    print(f'✅ Log file exists: {size} bytes')
    print()
    if size > 0:
        print('LOG CONTENT:')
        print('-'*70)
        print(log_file.read_text())
        print('-'*70)
    else:
        print('⚠️ Log file is empty - agents are initializing')
        print('   Logs will appear as agents start processing leads')
else:
    print('⚠️ Log file does not exist yet')
    print('   Agents may still be starting up')

print()
print('='*70)
print()
print('To view logs continuously, run:')
print('  Get-Content data\\logs\\agents.log -Wait -Tail 20')
print()


