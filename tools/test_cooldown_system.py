#!/usr/bin/env python3
"""
Test the new cooldown system
"""
import os
import sys
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))
sys.path.append('src')

from src.integrations.multi_account_linkedin import MultiAccountLinkedInSender
from src.utils.config_loader import load_config
from datetime import datetime, timedelta

def test_cooldown_system():
    """Test the cooldown system functionality."""
    print("🔧 Testing cooldown system...")
    
    try:
        config = load_config()
        sender = MultiAccountLinkedInSender(config)
        
        print(f"✅ Loaded {len(sender.accounts)} accounts")
        
        # Check each account availability
        for i, account in enumerate(sender.accounts):
            available, reason = sender._is_account_available(account['name'])
            status = "✅ AVAILABLE" if available else f"❌ {reason}"
            print(f"   {account['name']} ({account['account_id']}): {status}")
        
        # Check global cooldown
        if sender.global_cooldown_until:
            print(f"🕐 Global cooldown until: {sender.global_cooldown_until}")
        else:
            print("✅ No global cooldown active")
        
        # Test finding available account
        result = sender._find_available_account()
        if result:
            index, account = result
            print(f"\n🎯 Selected account: {account['name']} (index {index})")
            print("✅ SYSTEM IS READY FOR LINKEDIN OUTREACH!")
        else:
            print("\n❌ No available accounts found")
            
        # Show current state
        print(f"\n📊 Current state:")
        for account_name in ['Account_1', 'Account_2']:
            stats = sender._get_account_stats(account_name)
            cooldown = stats.get('cooldown_until', 'None')
            print(f"   {account_name}: error_count={stats['error_count']}, cooldown_until={cooldown}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cooldown_system()


