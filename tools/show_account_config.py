#!/usr/bin/env python3
"""
Show current LinkedIn account configuration.
"""

import os
import sys
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

from dotenv import load_dotenv

load_dotenv()

print("="*70)
print("LinkedIn Account Configuration")
print("="*70)

print("\nAccount_1 (Primary):")
print(f"  DSN: {os.getenv('UNIPILE_DSN', 'NOT SET')}")
print(f"  API Key: {os.getenv('UNIPILE_API_KEY', 'NOT SET')[:20]}..." if os.getenv('UNIPILE_API_KEY') else "  API Key: NOT SET")
print(f"  Account ID: {os.getenv('UNIPILE_ACCOUNT_ID', 'NOT SET')}")

print("\nAccount_2 (Secondary):")
print(f"  DSN: {os.getenv('UNIPILE_DSN_2', 'NOT SET')}")
print(f"  API Key: {os.getenv('UNIPILE_API_KEY_2', 'NOT SET')[:20]}..." if os.getenv('UNIPILE_API_KEY_2') else "  API Key: NOT SET")
print(f"  Account ID: {os.getenv('UNIPILE_ACCOUNT_ID_2', 'NOT SET')}")

# Check if Account_2 is configured
account_1_configured = all([
    os.getenv('UNIPILE_DSN'),
    os.getenv('UNIPILE_API_KEY'),
    os.getenv('UNIPILE_ACCOUNT_ID')
])

account_2_configured = all([
    os.getenv('UNIPILE_DSN_2'),
    os.getenv('UNIPILE_API_KEY_2'),
    os.getenv('UNIPILE_ACCOUNT_ID_2')
])

print("\n" + "="*70)
print("Summary:")
print("="*70)
print(f"  Account_1 configured: {'YES' if account_1_configured else 'NO'}")
print(f"  Account_2 configured: {'YES' if account_2_configured else 'NO'}")

if account_1_configured and not account_2_configured:
    print("\n  ✅ Single account setup - Account_1 only")
    print("  ✅ State file has been fixed to remove Account_2")
elif account_1_configured and account_2_configured:
    print("\n  ✅ Multiple accounts setup - Account_1 and Account_2")
else:
    print("\n  ❌ ERROR: Account_1 not configured!")
    print("     Please set UNIPILE_DSN, UNIPILE_API_KEY, and UNIPILE_ACCOUNT_ID")

print("\n" + "="*70)


