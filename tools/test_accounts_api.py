#!/usr/bin/env python3
"""
Test script to verify both LinkedIn accounts are accessible via Unipile API.
"""

import os
import sys
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

import requests
import json

def test_unipile_accounts():
    """Test both LinkedIn accounts via Unipile API."""
    print("🧪 Testing Unipile Multi-Account Setup")
    print("=" * 50)
    
    # API credentials
    dsn = "api24.unipile.com:15434"
    api_key = "QgVxUUNo.Wn6CEWNFS5SrFDlHbvY9ONM8SU4XvYF13ngfSslfcjA="
    base_url = f"https://{dsn}/api/v1"
    
    headers = {
        'X-API-KEY': api_key,
        'accept': 'application/json'
    }
    
    try:
        # Get all accounts
        print("📋 Fetching all accounts...")
        response = requests.get(f"{base_url}/accounts", headers=headers, timeout=30)
        response.raise_for_status()
        
        accounts = response.json().get("items", [])
        print(f"Found {len(accounts)} accounts:")
        print()
        
        primary_account_id = None
        secondary_account_id = "H4jxL2OBSCu5-jKVhFOzXQ"
        
        for i, account in enumerate(accounts, 1):
            account_id = account.get("id", "")
            provider = account.get("provider", "")
            username = account.get("username", "")
            display_name = account.get("display_name", "")
            
            print(f"🔸 Account {i}:")
            print(f"   ID: {account_id}")
            print(f"   Provider: {provider}")
            print(f"   Username: {username}")
            print(f"   Display Name: {display_name}")
            
            # Identify accounts
            if account_id == secondary_account_id:
                print(f"   ✅ This is the SECONDARY account (teamkuinji@gmail.com)")
            elif not primary_account_id:
                primary_account_id = account_id
                print(f"   ✅ This is likely the PRIMARY account")
            
            print()
        
        # Test chats for both accounts
        if primary_account_id:
            print(f"🔍 Testing PRIMARY account ({primary_account_id}):")
            test_account_chats(base_url, headers, primary_account_id)
            print()
        
        print(f"🔍 Testing SECONDARY account ({secondary_account_id}):")
        test_account_chats(base_url, headers, secondary_account_id)
        
        # Generate updated .env content
        print("\n" + "="*50)
        print("📝 Updated .env configuration:")
        print("="*50)
        print(f"LINKEDIN_SERVICE=unipile")
        print(f"UNIPILE_DSN={dsn}")
        print(f"UNIPILE_API_KEY={api_key}")
        if primary_account_id:
            print(f"UNIPILE_ACCOUNT_ID={primary_account_id}")
        print(f"")
        print(f"# Multi-account support")
        print(f"LINKEDIN_DAILY_LIMIT=50")
        print(f"LINKEDIN_HOURLY_LIMIT=10")
        print(f"UNIPILE_DSN_2={dsn}")
        print(f"UNIPILE_API_KEY_2={api_key}")
        print(f"UNIPILE_ACCOUNT_ID_2={secondary_account_id}")
        
    except Exception as e:
        print(f"❌ Error testing accounts: {e}")
        import traceback
        traceback.print_exc()

def test_account_chats(base_url, headers, account_id):
    """Test getting chats for a specific account."""
    try:
        params = {"account_id": account_id, "limit": 5}
        response = requests.get(f"{base_url}/chats", headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        chats = response.json().get("items", [])
        print(f"   📱 Found {len(chats)} chats")
        
        if chats:
            print(f"   Recent chats:")
            for chat in chats[:3]:  # Show first 3
                attendee_id = chat.get("attendee_provider_id", "")[:20] + "..."
                print(f"     - Chat ID: {chat.get('id', '')[:15]}... | Attendee: {attendee_id}")
        
    except Exception as e:
        print(f"   ❌ Error getting chats: {e}")

if __name__ == "__main__":
    test_unipile_accounts()


