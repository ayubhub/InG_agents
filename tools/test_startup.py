#!/usr/bin/env python3
"""Test agent startup and capture output"""
import sys
import os
import traceback
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

output = []
output.append("="*70)
output.append("AGENT STARTUP TEST")
output.append("="*70)
output.append("")

# Test 1: Check .env
output.append("1. Checking .env file...")
env_file = Path('.env')
if env_file.exists():
    output.append(f"   ✅ .env exists ({env_file.stat().st_size} bytes)")
    # Check key vars
    from dotenv import load_dotenv
    load_dotenv()
    gemini = os.getenv('GEMINI_API_KEY', '')
    sheets = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID', '')
    output.append(f"   GEMINI_API_KEY: {'SET' if gemini else 'MISSING'}")
    output.append(f"   GOOGLE_SHEETS_SPREADSHEET_ID: {'SET' if sheets else 'MISSING'}")
else:
    output.append("   ❌ .env file not found")

output.append("")

# Test 2: Check config loading
output.append("2. Testing config loading...")
try:
    from src.utils.config_loader import load_config
    config = load_config()
    output.append("   ✅ Config loaded successfully")
except Exception as e:
    output.append(f"   ❌ Config load failed: {e}")
    output.append(f"   Traceback: {traceback.format_exc()}")

output.append("")

# Test 3: Check logger
output.append("3. Testing logger...")
try:
    from src.utils.logger import setup_logger
    logger = setup_logger('test')
    logger.info("Test log message")
    log_file = Path('data/logs/agents.log')
    if log_file.exists():
        output.append(f"   ✅ Log file created ({log_file.stat().st_size} bytes)")
    else:
        output.append("   ⚠️ Log file not created yet")
except Exception as e:
    output.append(f"   ❌ Logger failed: {e}")

output.append("")

# Test 4: Try importing agents
output.append("4. Testing agent imports...")
try:
    from src.agents.sales_manager_agent import SalesManagerAgent
    from src.agents.lead_finder_agent import LeadFinderAgent
    from src.agents.outreach_agent import OutreachAgent
    output.append("   ✅ All agents imported successfully")
except Exception as e:
    output.append(f"   ❌ Agent import failed: {e}")
    output.append(f"   Traceback: {traceback.format_exc()}")

output.append("")
output.append("="*70)

# Write results
result_file = Path('startup_test_results.txt')
result_file.write_text('\n'.join(output))

# Print to console
print('\n'.join(output))


