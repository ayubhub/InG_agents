#!/usr/bin/env python3
"""
Update configuration for second LinkedIn account from Unipile.
Fetches all accounts and updates .env file with Account_2.
"""

import os
import sys
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

import requests
import re
from dotenv import load_dotenv, find_dotenv

load_dotenv()

def get_all_accounts(dsn: str, api_key: str):
    """Fetch all LinkedIn accounts from Unipile API."""
    url = f"https://{dsn}/api/v1/accounts"
    headers = {
        'X-API-KEY': api_key,
        'accept': 'application/json'
    }
    
    print(f"Fetching accounts from: https://{dsn}/api/v1/accounts")
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"API Response structure: {list(data.keys())}")
        
        # Try different response formats
        accounts = data.get("items", data.get("accounts", data.get("data", [])))
        
        if not accounts and isinstance(data, list):
            accounts = data
        
        print(f"Total accounts found: {len(accounts)}")
        
        # Filter only LinkedIn accounts
        linkedin_accounts = []
        for acc in accounts:
            provider = acc.get('provider', '').lower()
            acc_type = acc.get('type', '').lower()
            if 'linkedin' in provider or 'linkedin' in acc_type or acc.get('object') == 'account':
                linkedin_accounts.append(acc)
        
        print(f"Found {len(linkedin_accounts)} LinkedIn account(s)")
        return linkedin_accounts
        
    except Exception as e:
        print(f"Error fetching accounts: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            try:
                print(f"Response text: {e.response.text[:200]}")
            except:
                pass
        return []

def print_accounts(accounts):
    """Print account details."""
    if not accounts:
        print("No LinkedIn accounts found")
        return
    
    print("\n" + "="*70)
    print("LinkedIn Accounts Found:")
    print("="*70)
    for i, account in enumerate(accounts, 1):
        print(f"\nAccount {i}:")
        print(f"  ID: {account.get('id', 'N/A')}")
        print(f"  Name: {account.get('name', 'N/A')}")
        print(f"  Type: {account.get('type', 'N/A')}")
        print(f"  Username: {account.get('username', 'N/A')}")
        print(f"  Display Name: {account.get('display_name', 'N/A')}")
        print(f"  Status: {account.get('status', 'N/A')}")

def update_env_with_accounts(accounts, dsn, api_key):
    """Update .env file with account configuration."""
    env_file = find_dotenv()
    if not env_file:
        env_file = Path(".env")
        if not env_file.exists():
            print("Creating new .env file...")
            env_file.touch()
    
    print(f"\nUpdating {env_file}...")
    
    # Read current .env
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    
    # Update with accounts
    if accounts:
        # Account_1 (primary)
        env_vars['UNIPILE_DSN'] = dsn
        env_vars['UNIPILE_API_KEY'] = api_key
        env_vars['UNIPILE_ACCOUNT_ID'] = accounts[0].get('id', '')
        print(f"  ✅ Updated Account_1: {accounts[0].get('id', '')}")
        
        # Account_2 (secondary) - if exists
        if len(accounts) > 1:
            env_vars['UNIPILE_DSN_2'] = dsn
            env_vars['UNIPILE_API_KEY_2'] = api_key
            env_vars['UNIPILE_ACCOUNT_ID_2'] = accounts[1].get('id', '')
            print(f"  ✅ Updated Account_2: {accounts[1].get('id', '')}")
        else:
            # Remove Account_2 if it was there but no longer exists
            for key in ['UNIPILE_DSN_2', 'UNIPILE_API_KEY_2', 'UNIPILE_ACCOUNT_ID_2']:
                if key in env_vars:
                    del env_vars[key]
                    print(f"  🗑️  Removed {key} (account not found)")
    
    # Write updated .env
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write("# Unipile Configuration\n")
        f.write(f"UNIPILE_DSN={env_vars.get('UNIPILE_DSN', '')}\n")
        f.write(f"UNIPILE_API_KEY={env_vars.get('UNIPILE_API_KEY', '')}\n")
        f.write(f"UNIPILE_ACCOUNT_ID={env_vars.get('UNIPILE_ACCOUNT_ID', '')}\n")
        
        if 'UNIPILE_ACCOUNT_ID_2' in env_vars:
            f.write(f"\n# Secondary LinkedIn Account\n")
            f.write(f"UNIPILE_DSN_2={env_vars.get('UNIPILE_DSN_2', '')}\n")
            f.write(f"UNIPILE_API_KEY_2={env_vars.get('UNIPILE_API_KEY_2', '')}\n")
            f.write(f"UNIPILE_ACCOUNT_ID_2={env_vars.get('UNIPILE_ACCOUNT_ID_2', '')}\n")
    
    print(f"\n✅ Configuration updated in {env_file}")

def main():
    """Main function."""
    print("="*70)
    print("Updating Second LinkedIn Account Configuration")
    print("="*70)
    
    # Get current credentials
    dsn = os.getenv('UNIPILE_DSN', 'api20.unipile.com:15052')
    api_key = os.getenv('UNIPILE_API_KEY', 'V3QiTBQz.HUxe993yizF3aQgYgtIBvq4bamCzazUbcwPH7YMHthg=')
    
    print(f"\nUsing credentials:")
    print(f"  DSN: {dsn}")
    print(f"  API Key: {api_key[:20]}...")
    
    # Fetch accounts
    accounts = get_all_accounts(dsn, api_key)
    
    if not accounts:
        print("\n❌ No LinkedIn accounts found!")
        print("Please check:")
        print("  1. API key is correct")
        print("  2. DSN endpoint is accessible")
        print("  3. LinkedIn accounts are added in Unipile dashboard")
        return False
    
    # Print accounts
    print_accounts(accounts)
    
    # Update .env
    print("\n" + "="*70)
    update_env_with_accounts(accounts, dsn, api_key)
    
    # Summary
    print("\n" + "="*70)
    print("Summary:")
    print("="*70)
    print(f"  Total LinkedIn accounts: {len(accounts)}")
    for i, account in enumerate(accounts, 1):
        print(f"  Account_{i}: {account.get('id', 'N/A')} ({account.get('name', 'N/A')})")
    
    if len(accounts) >= 2:
        print("\n✅ Second account configured successfully!")
        print("   Please restart the application for changes to take effect.")
    else:
        print("\n⚠️  Only one account found. Second account not configured.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


