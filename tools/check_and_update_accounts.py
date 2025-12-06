#!/usr/bin/env python3
"""
Check and update Unipile LinkedIn accounts configuration.
Fetches all accounts from API and updates .env file.
"""

import os
import sys
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

import requests
import re
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_all_accounts(dsn: str, api_key: str) -> List[Dict]:
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
        
        # If accounts is still empty, check if data is a list
        if not accounts and isinstance(data, list):
            accounts = data
        
        print(f"Total accounts found: {len(accounts)}")
        if accounts:
            print(f"First account keys: {list(accounts[0].keys())}")
        
        # Filter only LinkedIn accounts
        linkedin_accounts = []
        for acc in accounts:
            provider = acc.get('provider', '').lower()
            acc_type = acc.get('type', '').lower()
            # Check if it's a LinkedIn account
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

def print_accounts(accounts: List[Dict]):
    """Print account details."""
    if not accounts:
        print("No LinkedIn accounts found")
        return
    
    print("\n" + "="*60)
    print("LinkedIn Accounts:")
    print("="*60)
    for i, account in enumerate(accounts, 1):
        print(f"\nAccount {i}:")
        print(f"  ID: {account.get('id', 'N/A')}")
        print(f"  Name: {account.get('name', 'N/A')}")
        print(f"  Type: {account.get('type', 'N/A')}")
        print(f"  Username: {account.get('username', 'N/A')}")
        print(f"  Display Name: {account.get('display_name', 'N/A')}")
        print(f"  Status: {account.get('status', 'N/A')}")
        print(f"  Provider: {account.get('provider', 'N/A')}")
        if account.get('connection_params'):
            print(f"  Connection: {account.get('connection_params', {}).get('username', 'N/A')}")

def get_current_env_config() -> Dict:
    """Get current Unipile configuration from environment."""
    config = {
        'dsn': os.getenv('UNIPILE_DSN', ''),
        'api_key': os.getenv('UNIPILE_API_KEY', ''),
        'account_ids': []
    }
    
    # Get all account IDs
    account_num = 1
    while True:
        account_id = os.getenv(f'UNIPILE_ACCOUNT_ID_{account_num}' if account_num > 1 else 'UNIPILE_ACCOUNT_ID')
        if account_id:
            config['account_ids'].append(account_id)
            account_num += 1
        else:
            break
    
    return config

def update_env_file(accounts: List[Dict], dsn: str, api_key: str) -> bool:
    """Update .env file with account configuration."""
    env_file = ".env"
    
    if not os.path.exists(env_file):
        print(f"\n.env file not found. Creating new one...")
        # Create new .env file
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# Unipile Configuration\n")
            f.write(f"UNIPILE_DSN={dsn}\n")
            f.write(f"UNIPILE_API_KEY={api_key}\n")
            if accounts:
                f.write(f"UNIPILE_ACCOUNT_ID={accounts[0].get('id', '')}\n")
            if len(accounts) > 1:
                f.write(f"UNIPILE_DSN_2={dsn}\n")
                f.write(f"UNIPILE_API_KEY_2={api_key}\n")
                f.write(f"UNIPILE_ACCOUNT_ID_2={accounts[1].get('id', '')}\n")
        print(f"Created {env_file}")
        return True
    
    # Read current .env file
    print(f"\nReading {env_file}...")
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Track which variables we've updated
    updated_vars = set()
    new_lines = []
    
    # Process each line
    for line in lines:
        stripped = line.strip()
        
        # Keep comments and empty lines
        if not stripped or stripped.startswith('#'):
            new_lines.append(line)
            continue
        
        # Check for Unipile variables
        updated = False
        
        # Primary account (no number)
        if stripped.startswith('UNIPILE_DSN=') and 'UNIPILE_DSN_' not in updated_vars:
            new_lines.append(f"UNIPILE_DSN={dsn}\n")
            updated_vars.add('UNIPILE_DSN')
            updated = True
            print(f"  Updated UNIPILE_DSN")
        
        elif stripped.startswith('UNIPILE_API_KEY=') and 'UNIPILE_API_KEY' not in updated_vars:
            new_lines.append(f"UNIPILE_API_KEY={api_key}\n")
            updated_vars.add('UNIPILE_API_KEY')
            updated = True
            print(f"  Updated UNIPILE_API_KEY")
        
        elif stripped.startswith('UNIPILE_ACCOUNT_ID=') and not '_' in stripped.split('=')[0][19:]:
            if accounts:
                new_lines.append(f"UNIPILE_ACCOUNT_ID={accounts[0].get('id', '')}\n")
                updated_vars.add('UNIPILE_ACCOUNT_ID')
                updated = True
                print(f"  Updated UNIPILE_ACCOUNT_ID={accounts[0].get('id', '')}")
            else:
                new_lines.append(line)
        
        # Numbered accounts (Account_2, Account_3, etc.)
        else:
            # Check for numbered accounts
            match = re.match(r'UNIPILE_(DSN|API_KEY|ACCOUNT_ID)(_(\d+))?=', stripped)
            if match:
                var_type = match.group(1)
                account_num_str = match.group(3)
                
                if account_num_str:
                    account_num = int(account_num_str)
                    idx = account_num - 1
                    
                    if var_type == 'DSN':
                        new_lines.append(f"UNIPILE_DSN_{account_num}={dsn}\n")
                        updated_vars.add(f'UNIPILE_DSN_{account_num}')
                        updated = True
                        print(f"  Updated UNIPILE_DSN_{account_num}")
                    elif var_type == 'API_KEY':
                        new_lines.append(f"UNIPILE_API_KEY_{account_num}={api_key}\n")
                        updated_vars.add(f'UNIPILE_API_KEY_{account_num}')
                        updated = True
                        print(f"  Updated UNIPILE_API_KEY_{account_num}")
                    elif var_type == 'ACCOUNT_ID':
                        if idx < len(accounts):
                            new_lines.append(f"UNIPILE_ACCOUNT_ID_{account_num}={accounts[idx].get('id', '')}\n")
                            updated_vars.add(f'UNIPILE_ACCOUNT_ID_{account_num}')
                            updated = True
                            print(f"  Updated UNIPILE_ACCOUNT_ID_{account_num}={accounts[idx].get('id', '')}")
                        else:
                            # Account doesn't exist, remove the line
                            print(f"  Removed UNIPILE_ACCOUNT_ID_{account_num} (account not found)")
                            updated = True
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        if not updated and not any(stripped.startswith(f'UNIPILE_{var}') for var in ['DSN', 'API_KEY', 'ACCOUNT_ID']):
            new_lines.append(line)
    
    # Add missing accounts
    if accounts:
        # Ensure primary account is set
        if 'UNIPILE_DSN' not in updated_vars:
            new_lines.append(f"UNIPILE_DSN={dsn}\n")
            print(f"  Added UNIPILE_DSN")
        if 'UNIPILE_API_KEY' not in updated_vars:
            new_lines.append(f"UNIPILE_API_KEY={api_key}\n")
            print(f"  Added UNIPILE_API_KEY")
        if 'UNIPILE_ACCOUNT_ID' not in updated_vars:
            new_lines.append(f"UNIPILE_ACCOUNT_ID={accounts[0].get('id', '')}\n")
            print(f"  Added UNIPILE_ACCOUNT_ID={accounts[0].get('id', '')}")
        
        # Add additional accounts
        for i in range(1, len(accounts)):
            account_num = i + 1
            if f'UNIPILE_ACCOUNT_ID_{account_num}' not in updated_vars:
                new_lines.append(f"UNIPILE_DSN_{account_num}={dsn}\n")
                new_lines.append(f"UNIPILE_API_KEY_{account_num}={api_key}\n")
                new_lines.append(f"UNIPILE_ACCOUNT_ID_{account_num}={accounts[i].get('id', '')}\n")
                print(f"  Added Account_{account_num}: {accounts[i].get('id', '')}")
    
    # Write updated file
    print(f"\nWriting updated {env_file}...")
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"Successfully updated {env_file}")
    return True

def main():
    """Main function."""
    print("="*60)
    print("Unipile LinkedIn Accounts Checker & Updater")
    print("="*60)
    
    # Get current configuration
    current_config = get_current_env_config()
    
    # Try to use current DSN and API key, or use new fallback credentials
    dsn = current_config['dsn'] or os.getenv('UNIPILE_DSN', '')
    api_key = current_config['api_key'] or os.getenv('UNIPILE_API_KEY', '')
    
    # Current fallback credentials
    NEW_DSN = "api22.unipile.com:15229"
    NEW_API_KEY = "pmrqNERD.I2FFFtqp3BGdkagj8cbKp3Z/f8hR7T48XG0+y1+cnuM="
    
    # If no credentials found, try new ones
    if not dsn or not api_key:
        print("\n[INFO] No credentials in environment, trying new fallback credentials...")
        dsn = NEW_DSN
        api_key = NEW_API_KEY
    else:
        # Try current credentials first, then fallback to new ones if they fail
        print(f"\nTrying current credentials first...")
        accounts = get_all_accounts(dsn, api_key)
        if not accounts:
            print(f"\n[INFO] Current credentials failed, trying new fallback credentials...")
            dsn = NEW_DSN
            api_key = NEW_API_KEY
    
    print(f"\nCurrent Configuration:")
    print(f"  DSN: {dsn}")
    print(f"  API Key: {api_key[:20]}...")
    print(f"  Current Account IDs: {current_config['account_ids']}")
    
    # Fetch accounts
    print("\n" + "="*60)
    accounts = get_all_accounts(dsn, api_key)
    
    if not accounts:
        print("\n[WARNING] No LinkedIn accounts found!")
        print("Please check:")
        print("  1. API key is correct")
        print("  2. DSN endpoint is accessible")
        print("  3. LinkedIn accounts are added in Unipile dashboard")
        return
    
    # Print account details
    print_accounts(accounts)
    
    # Update .env file
    print("\n" + "="*60)
    print("Updating .env file...")
    success = update_env_file(accounts, dsn, api_key)
    
    if success:
        print("\n" + "="*60)
        print("[OK] Configuration updated successfully!")
        print("\nSummary:")
        print(f"  Total LinkedIn accounts: {len(accounts)}")
        for i, account in enumerate(accounts, 1):
            print(f"  Account_{i}: {account.get('id', 'N/A')}")
        print("\n[IMPORTANT] Please restart the application for changes to take effect.")
    else:
        print("\n[ERROR] Failed to update configuration")

if __name__ == "__main__":
    main()


