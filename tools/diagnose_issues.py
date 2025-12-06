#!/usr/bin/env python3
"""Diagnose all potential issues preventing agents from starting"""
import sys
import os
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

print("="*70)
print("DIAGNOSTIC REPORT - AGENT STARTUP ISSUES")
print("="*70)
print()

# Check 1: Virtual environment
print("1. VIRTUAL ENVIRONMENT CHECK")
print(f"   Python executable: {sys.executable}")
print(f"   Virtual env active: {'venv' in sys.executable}")
print()

# Check 2: Dependencies
print("2. DEPENDENCY CHECK")
missing_deps = []
required_deps = ['psutil', 'colorlog', 'gspread', 'google.generativeai', 'dotenv', 'yaml']

for dep in required_deps:
    try:
        __import__(dep)
        print(f"   ✅ {dep}")
    except ImportError:
        print(f"   ❌ {dep} - MISSING")
        missing_deps.append(dep)

if missing_deps:
    print(f"\n   🔧 FIX: pip install {' '.join(missing_deps)}")
print()

# Check 3: Configuration files
print("3. CONFIGURATION FILES")
config_files = {
    '.env': Path('.env'),
    'config/agents.yaml': Path('config/agents.yaml'),
    'venv/Scripts/Activate.ps1': Path('venv/Scripts/Activate.ps1')
}

for name, path in config_files.items():
    if path.exists():
        print(f"   ✅ {name} ({path.stat().st_size} bytes)")
    else:
        print(f"   ❌ {name} - MISSING")
print()

# Check 4: Environment variables
print("4. ENVIRONMENT VARIABLES")
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'GEMINI_API_KEY',
        'GOOGLE_SHEETS_SPREADSHEET_ID', 
        'GOOGLE_SHEETS_CREDENTIALS_PATH'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: SET")
        else:
            print(f"   ❌ {var}: MISSING")
            
except Exception as e:
    print(f"   ❌ Error loading .env: {e}")
print()

# Check 5: Configuration loading
print("5. CONFIGURATION LOADING")
try:
    sys.path.insert(0, '.')
    from src.utils.config_loader import load_config
    config = load_config()
    print("   ✅ Configuration loaded successfully")
except Exception as e:
    print(f"   ❌ Configuration load failed: {e}")
    import traceback
    print(f"   Traceback: {traceback.format_exc()}")
print()

# Check 6: Process status
print("6. PROCESS STATUS")
pid_file = Path('data/state/main.pid')
if pid_file.exists():
    try:
        pid = int(pid_file.read_text().strip())
        import psutil
        if psutil.pid_exists(pid):
            print(f"   ⚠️ Stale process running: PID {pid}")
            print("   🔧 FIX: taskkill /F /PID {pid}")
        else:
            print(f"   ⚠️ Stale PID file: PID {pid} not running")
            print("   🔧 FIX: Remove-Item data\\state\\main.pid")
    except Exception as e:
        print(f"   ❌ Invalid PID file: {e}")
else:
    print("   ✅ No PID file (good for startup)")
print()

print("="*70)
print("SUMMARY")
print("="*70)

if missing_deps:
    print("❌ ISSUE: Missing dependencies")
    print(f"   FIX: pip install {' '.join(missing_deps)}")
    print()

if not Path('.env').exists():
    print("❌ ISSUE: Missing .env file")
    print("   FIX: Copy from C:\\Users\\yanma\\Local_Server_InG\\InG_agents\\.env")
    print()

if pid_file.exists():
    print("❌ ISSUE: Stale PID file blocking startup")
    print("   FIX: Remove-Item data\\state\\main.pid -Force")
    print()

if not missing_deps and Path('.env').exists() and not pid_file.exists():
    print("✅ All checks passed - agents should start successfully")
    print("   RUN: python run_main.py")

print("="*70)


