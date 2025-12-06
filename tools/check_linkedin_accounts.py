#!/usr/bin/env python3
"""
Check configured LinkedIn accounts and their status.
Shows what accounts are configured and why they might be unavailable.
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

def check_accounts():
    """Check all configured LinkedIn accounts."""
    print("="*70)
    print("LinkedIn Accounts Configuration Check")
    print("="*70)
    
    # Check environment variables
    print("\n1. Environment Variables:")
    print("-" * 70)
    
    accounts_found = []
    account_num = 1
    
    while True:
        if account_num == 1:
            dsn = os.getenv("UNIPILE_DSN")
            api_key = os.getenv("UNIPILE_API_KEY")
            account_id = os.getenv("UNIPILE_ACCOUNT_ID")
        else:
            dsn = os.getenv(f"UNIPILE_DSN_{account_num}")
            api_key = os.getenv(f"UNIPILE_API_KEY_{account_num}")
            account_id = os.getenv(f"UNIPILE_ACCOUNT_ID_{account_num}")
        
        if dsn and api_key and account_id:
            accounts_found.append({
                "num": account_num,
                "name": f"Account_{account_num}",
                "dsn": dsn,
                "api_key": api_key[:20] + "..." if api_key else None,
                "account_id": account_id
            })
            print(f"  Account_{account_num}:")
            print(f"    DSN: {dsn}")
            print(f"    API Key: {api_key[:20]}..." if api_key else "    API Key: NOT SET")
            print(f"    Account ID: {account_id}")
            account_num += 1
        else:
            if account_num == 1:
                print("  Account_1: NOT CONFIGURED")
            break
    
    print(f"\nTotal accounts configured: {len(accounts_found)}")
    
    # Check state files
    print("\n2. Account State Files:")
    print("-" * 70)
    
    state_file = Path("data/state/multi_account_state.json")
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        account_stats = state.get("account_stats", {})
        current_index = state.get("current_account_index", 0)
        
        print(f"  Current account index: {current_index}")
        print(f"  Accounts in state file: {len(account_stats)}")
        
        for account_name, stats in account_stats.items():
            print(f"\n  {account_name}:")
            print(f"    Daily sent: {stats.get('daily_sent', 0)}")
            print(f"    Hourly sent: {stats.get('hourly_sent', 0)}")
            print(f"    Error count: {stats.get('error_count', 0)}")
            
            cooldown = stats.get('cooldown_until')
            if cooldown:
                print(f"    Cooldown until: {cooldown}")
            
            last_error = stats.get('last_error')
            if last_error:
                error_preview = last_error[:100] + "..." if len(last_error) > 100 else last_error
                print(f"    Last error: {error_preview}")
    else:
        print("  State file not found")
    
    # Check limits
    print("\n3. Rate Limits:")
    print("-" * 70)
    daily_limit = int(os.getenv("LINKEDIN_DAILY_LIMIT", "50"))
    hourly_limit = int(os.getenv("LINKEDIN_HOURLY_LIMIT", "10"))
    print(f"  Daily limit per account: {daily_limit}")
    print(f"  Hourly limit per account: {hourly_limit}")
    
    # Analysis
    print("\n4. Analysis:")
    print("-" * 70)
    
    if len(accounts_found) == 0:
        print("  ❌ ERROR: No accounts configured!")
        print("     Please set UNIPILE_DSN, UNIPILE_API_KEY, and UNIPILE_ACCOUNT_ID in .env")
    elif len(accounts_found) == 1:
        print(f"  ✅ Single account configured: {accounts_found[0]['name']}")
        print(f"     Account ID: {accounts_found[0]['account_id']}")
        
        # Check if Account_2 exists in state but not in env
        if state_file.exists():
            with open(state_file, 'r') as f:
                state = json.load(f)
            account_stats = state.get("account_stats", {})
            if "Account_2" in account_stats:
                print("\n  ⚠️  WARNING: Account_2 found in state file but NOT in environment!")
                print("     This can cause 'all accounts unavailable' errors.")
                print("     Solution: Remove Account_2 from state file or configure it properly.")
    else:
        print(f"  ✅ Multiple accounts configured: {len(accounts_found)}")
        for acc in accounts_found:
            print(f"     - {acc['name']}: {acc['account_id']}")
    
    # Recommendations
    print("\n5. Recommendations:")
    print("-" * 70)
    
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = json.load(f)
        account_stats = state.get("account_stats", {})
        
        # Check for Account_2 without configuration
        if "Account_2" in account_stats and len(accounts_found) == 1:
            print("  🔧 FIX: Remove Account_2 from state file:")
            print("     1. Edit data/state/multi_account_state.json")
            print("     2. Remove 'Account_2' from 'account_stats'")
            print("     3. Set 'current_account_index' to 0")
            print("     4. Or run: python tools/reset_linkedin_accounts.py")
        
        # Check for cooldowns
        for account_name, stats in account_stats.items():
            cooldown = stats.get('cooldown_until')
            if cooldown:
                try:
                    cooldown_dt = datetime.fromisoformat(cooldown.replace('Z', '+00:00'))
                    if cooldown_dt > datetime.now():
                        print(f"  ⏰ {account_name} is in cooldown until {cooldown}")
                except:
                    pass
    
    print("\n" + "="*70)

if __name__ == "__main__":
    check_accounts()


