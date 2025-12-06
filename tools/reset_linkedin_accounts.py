#!/usr/bin/env python3
"""
Manual reset script for LinkedIn accounts
Run this anytime both accounts are blocked
"""
import os
import sys
from pathlib import Path
import json
from datetime import datetime

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

def reset_linkedin_accounts():
    """Reset all LinkedIn account error counts and limits."""
    state_file = "data/state/multi_account_state.json"
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        
        # Reset state with clean accounts
        now = datetime.now()
        clean_state = {
            "account_stats": {
                "Account_1": {
                    "daily_sent": 0,
                    "hourly_sent": 0,
                    "last_reset_date": now.date().isoformat(),
                    "last_reset_hour": now.hour,
                    "total_sent": 0,
                    "last_error": None,
                    "error_count": 0,
                    "last_used": None,
                    "cooldown_until": None
                },
                "Account_2": {
                    "daily_sent": 0,
                    "hourly_sent": 0,
                    "last_reset_date": now.date().isoformat(),
                    "last_reset_hour": now.hour,
                    "total_sent": 0,
                    "last_error": None,
                    "error_count": 0,
                    "last_used": None,
                    "cooldown_until": None
                }
            },
            "current_account_index": 0,
            "global_cooldown_until": None,
            "last_updated": now.isoformat()
        }
        
        with open(state_file, 'w') as f:
            json.dump(clean_state, f, indent=2)
            
        print("✅ RESET COMPLETE!")
        print("✅ Account_1: error_count=0, daily_sent=0, cooldown=None")
        print("✅ Account_2: error_count=0, daily_sent=0, cooldown=None")
        print("✅ Global cooldown cleared")
        print("✅ Both accounts are now available for LinkedIn outreach")
        print("✅ System will start with Account_1")
        
    except Exception as e:
        print(f"❌ Error resetting accounts: {e}")

if __name__ == "__main__":
    reset_linkedin_accounts()


