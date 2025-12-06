#!/usr/bin/env python3
"""
Test Google Sheets connection with real credentials
"""

import os
import sys
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

from dotenv import load_dotenv

def test_connection():
    """Test if we can connect to Google Sheets with real credentials"""
    
    print("🧪 TESTING GOOGLE SHEETS CONNECTION")
    print("=" * 40)
    
    load_dotenv()
    
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Test credentials
        creds_path = "config/google-credentials.json"
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        
        print("🔑 Loading credentials...")
        creds = Credentials.from_service_account_file(creds_path, scopes=scope)
        client = gspread.authorize(creds)
        print("✅ Credentials loaded successfully!")
        
        # Test spreadsheet access
        spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "1o2i71wYPkqut_ItTtfsVqu9ywYD7g-vuWU47DV33YD0")
        print(f"📊 Connecting to spreadsheet: {spreadsheet_id}")
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        print(f"✅ Connected to spreadsheet: {spreadsheet.title}")
        
        # Test sheet access
        sheet = spreadsheet.worksheet('Leads')
        print("✅ Accessed 'Leads' sheet!")
        
        # Test reading data
        records = sheet.get_all_records()
        print(f"✅ Found {len(records)} records in sheet")
        
        # Show first few records
        for i, record in enumerate(records[:3]):
            if record.get('Name'):
                print(f"   Lead {i+1}: {record.get('Name')} at {record.get('Company')}")
        
        print(f"\n🎉 SUCCESS! Google Sheets connection working!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    
    if success:
        print(f"\n🚀 READY TO START AGENTS!")
        print("Run: python run_main.py")
        print("Agents will now connect to your spreadsheet automatically!")
    else:
        print(f"\n🔧 Need to fix connection issues first")


