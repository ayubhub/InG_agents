#!/usr/bin/env python3
"""
Analyze errors in Notes and Response Status columns of Google Sheets.
Identifies patterns, duplicates, and issues.
"""

import os
import sys
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

import gspread
from google.oauth2.service_account import Credentials
from collections import defaultdict, Counter
from datetime import datetime
import re

def analyze_notes_errors():
    """Analyze errors in Notes and Response Status columns."""
    
    print("Analyzing Notes errors...\n")
    
    # Load credentials
    creds_path = "config/google-credentials.json"
    if not os.path.exists(creds_path):
        print(f"[ERROR] {creds_path} not found")
        return False
    
    # Get spreadsheet ID from environment
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "1o2i71wYPkqut_ItTtfsVqu9ywYD7g-vuWU47DV33YD0")
    
    try:
        # Authenticate
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(creds_path, scopes=scope)
        client = gspread.authorize(creds)
        
        print(f"[OK] Connected to Google Sheets\n")
        
        # Open spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        sheet = spreadsheet.worksheet('Leads')
        
        # Get all data
        all_data = sheet.get_all_records()
        
        print(f"Total leads: {len(all_data)}\n")
        
        # Analyze Notes column
        notes_errors = []
        notes_patterns = Counter()
        
        error_types = {
            "Failed": [],
            "Invitation": [],
            "Message": [],
            "LinkedIn ID": [],
            "Other": []
        }
        
        for i, row in enumerate(all_data, start=2):  # Start from row 2 (row 1 is header)
            lead_id = row.get("Lead ID", "")
            name = row.get("Name", "")
            notes = row.get("Notes", "").strip()
            contact_status = row.get("Contact Status", "").strip()
            
            # Analyze Notes
            if notes:
                # Check for error patterns
                if "Failed:" in notes or "failed" in notes.lower():
                    error_types["Failed"].append({
                        "row": i,
                        "lead_id": lead_id,
                        "name": name,
                        "notes": notes,
                        "contact_status": contact_status
                    })
                    notes_errors.append({
                        "row": i,
                        "lead_id": lead_id,
                        "name": name,
                        "error": notes
                    })
                
                if "Invitation" in notes:
                    error_types["Invitation"].append({
                        "row": i,
                        "lead_id": lead_id,
                        "name": name,
                        "notes": notes
                    })
                
                if "Message ID:" in notes:
                    error_types["Message"].append({
                        "row": i,
                        "lead_id": lead_id,
                        "name": name,
                        "notes": notes
                    })
                
                if "LinkedIn ID" in notes or "could not find" in notes.lower():
                    error_types["LinkedIn ID"].append({
                        "row": i,
                        "lead_id": lead_id,
                        "name": name,
                        "notes": notes
                    })
                
                # Extract error pattern
                if "Failed:" in notes:
                    match = re.search(r'Failed:\s*(.+)', notes, re.IGNORECASE)
                    if match:
                        error_msg = match.group(1).strip()
                        notes_patterns[error_msg[:100]] += 1  # First 100 chars
        
        # Print analysis
        print("=" * 80)
        print("NOTES COLUMN ANALYSIS")
        print("=" * 80)
        
        print(f"\n[OK] Total leads with Notes: {sum(1 for row in all_data if row.get('Notes', '').strip())}")
        print(f"[ERROR] Total leads with error Notes: {len(notes_errors)}")
        
        print(f"\nError Types in Notes:")
        print(f"  - Failed errors: {len(error_types['Failed'])}")
        print(f"  - Invitation messages: {len(error_types['Invitation'])}")
        print(f"  - Message IDs: {len(error_types['Message'])}")
        print(f"  - LinkedIn ID errors: {len(error_types['LinkedIn ID'])}")
        print(f"  - Other: {len(error_types['Other'])}")
        
        if notes_errors:
            print(f"\n[ERROR] Failed Errors in Notes ({len(error_types['Failed'])}):")
            for error in error_types['Failed'][:10]:  # Show first 10
                print(f"\n  Row {error['row']} - {error['lead_id']} ({error['name']}):")
                print(f"    Contact Status: {error['contact_status']}")
                print(f"    Notes: {error['notes'][:200]}...")
            if len(error_types['Failed']) > 10:
                print(f"\n  ... and {len(error_types['Failed']) - 10} more")
        
        if error_types['LinkedIn ID']:
            print(f"\n[LINKEDIN] LinkedIn ID Errors in Notes ({len(error_types['LinkedIn ID'])}):")
            for error in error_types['LinkedIn ID'][:5]:
                print(f"\n  Row {error['row']} - {error['lead_id']} ({error['name']}):")
                print(f"    {error['notes'][:150]}...")
        
        if notes_patterns:
            print(f"\nMost Common Error Patterns in Notes:")
            for pattern, count in notes_patterns.most_common(5):
                print(f"  [{count}x] {pattern[:80]}...")
        
        # Summary and recommendations
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        
        recommendations = []
        
        if len(error_types['Failed']) > 0:
            recommendations.append(f"[ERROR] Fix {len(error_types['Failed'])} failed LinkedIn operations")
        
        if len(error_types['LinkedIn ID']) > 0:
            recommendations.append(f"[LINKEDIN] Verify {len(error_types['LinkedIn ID'])} LinkedIn URLs")
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        else:
            print("[OK] No critical issues found!")
        
        print("\n" + "=" * 80)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    analyze_notes_errors()


