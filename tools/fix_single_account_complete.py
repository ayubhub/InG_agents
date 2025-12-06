#!/usr/bin/env python3
"""
Complete fix for single LinkedIn account setup.
- Removes Account_2 from state if not configured
- Clears cooldowns
- Resets limits
- Ensures only Account_1 is used
"""

import os
import sys
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def fix_single_account():
    """Fix state file for single account setup."""
    print("="*70)
    print("Complete Fix for Single LinkedIn Account")
    print("="*70)
    
    # Check what accounts are configured
    print("\n1. Checking configured accounts...")
    accounts_configured = []
    
    if os.getenv("UNIPILE_DSN") and os.getenv("UNIPILE_API_KEY") and os.getenv("UNIPILE_ACCOUNT_ID"):
        accounts_configured.append("Account_1")
        print(f"  ✅ Account_1 configured: {os.getenv('UNIPILE_ACCOUNT_ID')}")
    else:
        print("  ❌ Account_1 NOT configured")
    
    if os.getenv("UNIPILE_DSN_2") and os.getenv("UNIPILE_API_KEY_2") and os.getenv("UNIPILE_ACCOUNT_ID_2"):
        accounts_configured.append("Account_2")
        print(f"  ✅ Account_2 configured: {os.getenv('UNIPILE_ACCOUNT_ID_2')}")
    else:
        print("  ❌ Account_2 NOT configured")
    
    print(f"\nTotal accounts configured: {len(accounts_configured)}")
    
    # Fix state file
    state_file = Path("data/state/multi_account_state.json")
    if not state_file.exists():
        print("\n⚠️  State file not found. Creating new one...")
        state = {
            "account_stats": {},
            "current_account_index": 0,
            "global_cooldown_until": None,
            "last_updated": None
        }
    else:
        with open(state_file, 'r') as f:
            state = json.load(f)
    
    account_stats = state.get("account_stats", {})
    
    print("\n2. Fixing state file...")
    print("-" * 70)
    
    # Remove accounts that are not configured
    accounts_to_remove = []
    for account_name in account_stats.keys():
        if account_name not in accounts_configured:
            accounts_to_remove.append(account_name)
            print(f"  🗑️  Removing {account_name} from state (not configured)")
    
    for account_name in accounts_to_remove:
        del account_stats[account_name]
    
    # Ensure Account_1 exists and reset it
    if "Account_1" in accounts_configured:
        if "Account_1" not in account_stats:
            print("  ➕ Adding Account_1 to state")
            account_stats["Account_1"] = {
                "daily_sent": 0,
                "hourly_sent": 0,
                "last_reset_date": datetime.now().date().isoformat(),
                "last_reset_hour": datetime.now().hour,
                "total_sent": 0,
                "error_count": 0,
                "last_used": None,
                "cooldown_until": None
            }
        else:
            # Reset Account_1 cooldown and errors
            print("  🔧 Resetting Account_1 (clearing cooldown and errors)")
            account_stats["Account_1"]["cooldown_until"] = None
            account_stats["Account_1"]["error_count"] = 0
            account_stats["Account_1"]["last_reset_date"] = datetime.now().date().isoformat()
            account_stats["Account_1"]["last_reset_hour"] = datetime.now().hour
    
    # Fix current_account_index
    if state.get("current_account_index", 0) >= len(accounts_configured):
        print(f"  🔧 Fixing current_account_index (was {state.get('current_account_index')}, setting to 0)")
        state["current_account_index"] = 0
    
    # Clear global cooldown
    if state.get("global_cooldown_until"):
        print(f"  🔧 Clearing global cooldown (was: {state.get('global_cooldown_until')})")
        state["global_cooldown_until"] = None
    
    # Save fixed state
    state["account_stats"] = account_stats
    state["last_updated"] = datetime.now().isoformat()
    
    # Create directory if needed
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"\n✅ State file fixed: {state_file}")
    print(f"   Accounts in state: {list(account_stats.keys())}")
    print(f"   Current account index: {state['current_account_index']}")
    print(f"   Global cooldown: {state.get('global_cooldown_until', 'None')}")
    
    # Show Account_1 status
    if "Account_1" in account_stats:
        acc1 = account_stats["Account_1"]
        print(f"\n   Account_1 status:")
        print(f"     Daily sent: {acc1.get('daily_sent', 0)}")
        print(f"     Hourly sent: {acc1.get('hourly_sent', 0)}")
        print(f"     Error count: {acc1.get('error_count', 0)}")
        print(f"     Cooldown: {acc1.get('cooldown_until', 'None')}")
    
    # Summary
    print("\n3. Summary:")
    print("-" * 70)
    print(f"  Configured accounts: {len(accounts_configured)}")
    print(f"  Accounts in state: {len(account_stats)}")
    
    if len(accounts_configured) == 1:
        print("\n  ✅ Single account setup confirmed")
        print(f"     Using: {accounts_configured[0]}")
        print("     All cooldowns cleared")
        print("     Account ready to use!")
    elif len(accounts_configured) == 0:
        print("\n  ❌ ERROR: No accounts configured!")
        print("     Please set UNIPILE_DSN, UNIPILE_API_KEY, and UNIPILE_ACCOUNT_ID")
    else:
        print(f"\n  ✅ Multiple accounts setup: {accounts_configured}")
    
    print("\n" + "="*70)
    print("Done! You can now restart the application.")
    print("="*70)

if __name__ == "__main__":
    fix_single_account()


