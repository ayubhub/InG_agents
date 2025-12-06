#!/usr/bin/env python3
"""
Complete reset of LinkedIn accounts - clears all cooldowns and fixes single account setup.
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

def reset_complete():
    """Complete reset - fix single account and clear all cooldowns."""
    print("="*70)
    print("Complete LinkedIn Accounts Reset")
    print("="*70)
    
    # Check configured accounts
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
    
    print(f"\nConfigured accounts:")
    print(f"  Account_1: {'YES' if account_1_configured else 'NO'}")
    print(f"  Account_2: {'YES' if account_2_configured else 'NO'}")
    
    # Create clean state
    now = datetime.now()
    account_stats = {}
    
    if account_1_configured:
        account_stats["Account_1"] = {
            "daily_sent": 0,
            "hourly_sent": 0,
            "last_reset_date": now.date().isoformat(),
            "last_reset_hour": now.hour,
            "total_sent": 0,
            "error_count": 0,
            "last_used": None,
            "cooldown_until": None
        }
        print(f"\n  ✅ Account_1 reset: {os.getenv('UNIPILE_ACCOUNT_ID')}")
    
    if account_2_configured:
        account_stats["Account_2"] = {
            "daily_sent": 0,
            "hourly_sent": 0,
            "last_reset_date": now.date().isoformat(),
            "last_reset_hour": now.hour,
            "total_sent": 0,
            "error_count": 0,
            "last_used": None,
            "cooldown_until": None
        }
        print(f"  ✅ Account_2 reset: {os.getenv('UNIPILE_ACCOUNT_ID_2')}")
    
    clean_state = {
        "account_stats": account_stats,
        "current_account_index": 0,
        "global_cooldown_until": None,
        "last_updated": now.isoformat()
    }
    
    # Save state
    state_file = Path("data/state/multi_account_state.json")
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, 'w') as f:
        json.dump(clean_state, f, indent=2)
    
    print(f"\n✅ State file reset: {state_file}")
    print(f"   Accounts in state: {list(account_stats.keys())}")
    print(f"   Current account index: 0")
    print(f"   Global cooldown: None")
    
    if account_1_configured and not account_2_configured:
        print(f"\n✅ Single account setup confirmed:")
        print(f"   - Only Account_1 is configured and active")
        print(f"   - All cooldowns cleared")
        print(f"   - Account ready to use!")
    elif account_1_configured and account_2_configured:
        print(f"\n✅ Multiple accounts setup:")
        print(f"   - Account_1 and Account_2 are configured")
        print(f"   - All cooldowns cleared")
    else:
        print(f"\n❌ ERROR: Account_1 not configured!")
        print("   Please set UNIPILE_DSN, UNIPILE_API_KEY, and UNIPILE_ACCOUNT_ID")
    
    print("\n" + "="*70)
    print("Reset complete! Restart the application.")
    print("="*70)

if __name__ == "__main__":
    reset_complete()


