#!/usr/bin/env python3
"""
Test Google Sheets connection and bypass credentials for testing
"""

import os
import sys
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

from dotenv import load_dotenv

def test_sheets_connection():
    """Test if we can connect to Google Sheets"""
    
    load_dotenv()
    
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    print(f"📊 Testing connection to spreadsheet: {spreadsheet_id}")
    
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Try to authenticate
        creds_path = "config/google-credentials.json"
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        
        print(f"🔑 Attempting to load credentials from: {creds_path}")
        
        creds = Credentials.from_service_account_file(creds_path, scopes=scope)
        client = gspread.authorize(creds)
        
        print("✅ Credentials loaded successfully")
        
        # Try to open spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        print(f"✅ Opened spreadsheet: {spreadsheet.title}")
        
        # Try to access Leads sheet
        sheet = spreadsheet.worksheet('Leads')
        print(f"✅ Accessed 'Leads' sheet")
        
        # Get all records
        records = sheet.get_all_records()
        print(f"✅ Found {len(records)} records")
        
        # Show first few records
        for i, record in enumerate(records[:3]):
            if record.get('Name'):
                print(f"   Lead {i+1}: {record.get('Name')} at {record.get('Company')}")
        
        return True, len(records)
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False, 0

def create_bypass_mode():
    """Create a bypass for testing without real credentials"""
    
    print("\n🔧 Creating bypass mode for testing...")
    
    # Modify the GoogleSheetsIO to return test data
    bypass_code = '''
# TEMPORARY BYPASS - Replace GoogleSheetsIO.read_leads method
def mock_read_leads(self, filters=None):
    """Return mock leads for testing"""
    from src.models.lead import Lead
    from datetime import datetime
    
    print("🧪 BYPASS MODE: Returning test leads from your spreadsheet")
    
    mock_leads = [
        Lead(
            lead_id="lead_001",
            name="Nik Rasnowski", 
            position="Senior Staff Talent Researcher L7",
            company="Facebook",
            linkedin_url="https://www.linkedin.com/in/hrdetective/",
            contact_status="Not Contacted",
            created_at=datetime.now(),
            last_updated=datetime.now()
        ),
        Lead(
            lead_id="lead_002",
            name="Neta Meidav",
            position="VP Business & Product Strategy MD of Ethics & Compliance", 
            company="Diligent",
            linkedin_url="https://www.linkedin.com/in/netameidav/",
            contact_status="Not Contacted",
            created_at=datetime.now(),
            last_updated=datetime.now()
        ),
        Lead(
            lead_id="lead_003", 
            name="Mathilde P.",
            position="Global Talent Acquisition Partner",
            company="",
            linkedin_url="https://www.linkedin.com/in/mathilde-p-a392425a/",
            contact_status="Not Contacted",
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
    ]
    
    # Apply filters if provided
    if filters:
        filtered_leads = []
        for lead in mock_leads:
            matches = True
            for key, value in filters.items():
                if hasattr(lead, key) and getattr(lead, key) != value:
                    matches = False
                    break
            if matches:
                filtered_leads.append(lead)
        return filtered_leads
    
    return mock_leads
'''
    
    print("✅ Bypass mode ready - agents will use your 3 real leads for testing")
    return bypass_code

if __name__ == "__main__":
    print("🔍 Testing Google Sheets Connection")
    print("=" * 40)
    
    success, count = test_sheets_connection()
    
    if not success:
        print("\n⚠️  Real credentials not working, creating bypass mode...")
        bypass_code = create_bypass_mode()
        
        print(f"\n📋 BYPASS SOLUTION:")
        print("Since real Google credentials aren't working, I can create a bypass")
        print("that makes your agents process your 3 real leads without Google Sheets.")
        print("")
        print("This will let you test the full agent workflow:")
        print("• LeadFinder will classify your leads")
        print("• SalesManager will allocate them") 
        print("• Outreach will send LinkedIn messages")
        print("")
        print("Would you like me to implement this bypass? (Y/n)")
    else:
        print(f"\n🎉 SUCCESS! Found {count} leads in your spreadsheet")
        print("The agents should be able to process them now.")


