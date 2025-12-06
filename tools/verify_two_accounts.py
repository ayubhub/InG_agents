#!/usr/bin/env python3
"""
Verify that two LinkedIn accounts are properly configured.
"""

import os
import sys
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

import json
from dotenv import load_dotenv

load_dotenv()

def verify_configuration():
    """Verify two-account configuration."""
    print("="*70)
    print("Verifying Two-Account LinkedIn Configuration")
    print("="*70)
    
    # Check Account_1
    print("\n1. Account_1 (Primary):")
    print("-" * 70)
    account_1_ok = all([
        os.getenv('UNIPILE_DSN'),
        os.getenv('UNIPILE_API_KEY'),
        os.getenv('UNIPILE_ACCOUNT_ID')
    ])
    
    if account_1_ok:
        print(f"  ✅ DSN: {os.getenv('UNIPILE_DSN')}")
        print(f"  ✅ API Key: {os.getenv('UNIPILE_API_KEY', '')[:20]}...")
        print(f"  ✅ Account ID: {os.getenv('UNIPILE_ACCOUNT_ID')}")
    else:
        print("  ❌ Account_1 NOT fully configured")
        print(f"     DSN: {'✅' if os.getenv('UNIPILE_DSN') else '❌'}")
        print(f"     API Key: {'✅' if os.getenv('UNIPILE_API_KEY') else '❌'}")
        print(f"     Account ID: {'✅' if os.getenv('UNIPILE_ACCOUNT_ID') else '❌'}")
    
    # Check Account_2
    print("\n2. Account_2 (Secondary):")
    print("-" * 70)
    account_2_ok = all([
        os.getenv('UNIPILE_DSN_2'),
        os.getenv('UNIPILE_API_KEY_2'),
        os.getenv('UNIPILE_ACCOUNT_ID_2')
    ])
    
    if account_2_ok:
        print(f"  ✅ DSN: {os.getenv('UNIPILE_DSN_2')}")
        print(f"  ✅ API Key: {os.getenv('UNIPILE_API_KEY_2', '')[:20]}...")
        print(f"  ✅ Account ID: {os.getenv('UNIPILE_ACCOUNT_ID_2')}")
    else:
        print("  ❌ Account_2 NOT fully configured")
        print(f"     DSN: {'✅' if os.getenv('UNIPILE_DSN_2') else '❌'}")
        print(f"     API Key: {'✅' if os.getenv('UNIPILE_API_KEY_2') else '❌'}")
        print(f"     Account ID: {'✅' if os.getenv('UNIPILE_ACCOUNT_ID_2') else '❌'}")
    
    # Check state file
    print("\n3. State File:")
    print("-" * 70)
    state_file = Path("data/state/multi_account_state.json")
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        account_stats = state.get("account_stats", {})
        print(f"  Accounts in state: {list(account_stats.keys())}")
        
        if "Account_1" in account_stats:
            acc1 = account_stats["Account_1"]
            print(f"  ✅ Account_1 stats present")
            print(f"     Daily sent: {acc1.get('daily_sent', 0)}")
            print(f"     Cooldown: {acc1.get('cooldown_until', 'None')}")
        else:
            print(f"  ⚠️  Account_1 stats missing")
        
        if "Account_2" in account_stats:
            acc2 = account_stats["Account_2"]
            print(f"  ✅ Account_2 stats present")
            print(f"     Daily sent: {acc2.get('daily_sent', 0)}")
            print(f"     Cooldown: {acc2.get('cooldown_until', 'None')}")
        else:
            print(f"  ⚠️  Account_2 stats missing (will be created on first use)")
        
        print(f"  Current account index: {state.get('current_account_index', 0)}")
        print(f"  Global cooldown: {state.get('global_cooldown_until', 'None')}")
    else:
        print("  ⚠️  State file not found (will be created on first run)")
    
    # Summary
    print("\n" + "="*70)
    print("Summary:")
    print("="*70)
    
    if account_1_ok and account_2_ok:
        print("  ✅ Both accounts are configured!")
        print("  ✅ System is ready for multi-account operation")
        print("\n  Next steps:")
        print("    1. Restart the application")
        print("    2. System will automatically use both accounts")
        print("    3. Automatic failover when limits are reached")
    elif account_1_ok:
        print("  ⚠️  Only Account_1 is configured")
        print("  ⚠️  Account_2 is missing")
        print("\n  To add Account_2:")
        print("    1. Run: python tools/update_second_account.py")
        print("    2. Or manually add to .env:")
        print("       UNIPILE_DSN_2=...")
        print("       UNIPILE_API_KEY_2=...")
        print("       UNIPILE_ACCOUNT_ID_2=...")
    else:
        print("  ❌ Account_1 is not configured!")
        print("  ❌ Please configure at least Account_1")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    verify_configuration()


