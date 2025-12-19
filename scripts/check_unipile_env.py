#!/usr/bin/env python3
"""
Script to check Unipile environment variables and test connection.
"""
import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def check_unipile_env():
    """Check Unipile environment variables."""
    print("🔍 Checking Unipile environment variables...\n")

    required_vars = {
        "UNIPILE_DSN": os.getenv("UNIPILE_DSN"),
        "UNIPILE_API_KEY": os.getenv("UNIPILE_API_KEY"),
        "UNIPILE_ACCOUNT_ID": os.getenv("UNIPILE_ACCOUNT_ID"),
    }

    all_ok = True

    for var_name, var_value in required_vars.items():
        if var_value:
            # Show full DSN for debugging
            if "DSN" in var_name:
                display_value = var_value
            elif "KEY" in var_name:
                display_value = var_value[:20] + "..." if len(var_value) > 20 else var_value
            else:
                display_value = var_value
            print(f"✅ {var_name}: {display_value}")
        else:
            print(f"❌ {var_name}: MISSING")
            all_ok = False

    if not all_ok:
        print("\n⚠️  Some required variables are missing!")
        return False

    print("\n✅ All required Unipile variables are set!")

    # Test connection
    print("\n🔗 Testing connection to Unipile API...")
    try:
        import requests

        dsn = required_vars["UNIPILE_DSN"]
        api_key = required_vars["UNIPILE_API_KEY"]
        account_id = required_vars["UNIPILE_ACCOUNT_ID"]

        # Test by getting accounts list
        url = f"https://{dsn}/api/v1/accounts"
        headers = {
            'X-API-KEY': api_key,
            'accept': 'application/json'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            accounts = data.get('items', [])
            print(f"✅ Connection successful! Found {len(accounts)} account(s)")

            # Check if account_id exists in the list
            found_account = None
            for account in accounts:
                if account.get('id') == account_id:
                    found_account = account
                    break

            if found_account:
                print(f"✅ Account ID '{account_id}' found in your accounts")
                print(f"   Account name: {found_account.get('name', 'N/A')}")
                print(f"   Account type: {found_account.get('type', 'N/A')}")
            else:
                print(f"⚠️  Account ID '{account_id}' not found in your accounts")
                if accounts:
                    print(f"   Available account IDs:")
                    for acc in accounts:
                        print(f"     - {acc.get('id')} ({acc.get('name', 'N/A')})")

            return True
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except ImportError:
        print("⚠️  'requests' library not installed. Skipping connection test.")
        print("   Install it with: pip install requests")
        return True  # Variables are OK, just can't test connection
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    success = check_unipile_env()
    sys.exit(0 if success else 1)
