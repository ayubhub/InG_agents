#!/usr/bin/env python3
"""
Lead monitoring dashboard - View lead status, messages, and responses
"""

import os
import sys
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

import sqlite3
from datetime import datetime
import json

def monitor_leads():
    """Monitor lead activity from database and logs"""
    
    print("🎯 InG LEAD MONITORING DASHBOARD")
    print("=" * 50)
    
    # Check if database exists
    db_path = "data/state/agents.db"
    if not os.path.exists(db_path):
        print("❌ Database not found. Agents may not be running yet.")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all leads
        cursor.execute("""
            SELECT lead_id, name, company, position, contact_status, 
                   classification, quality_score, allocated_to, 
                   message_sent, response, created_at, last_updated
            FROM leads 
            ORDER BY last_updated DESC
        """)
        
        leads = cursor.fetchall()
        
        if not leads:
            print("📭 No leads found in database yet.")
            print("   Agents may still be initializing...")
            return
        
        print(f"📊 FOUND {len(leads)} LEADS:")
        print("-" * 80)
        
        for lead in leads:
            lead_id, name, company, position, status, classification, score, allocated_to, message, response, created, updated = lead
            
            print(f"\n👤 {name} ({lead_id})")
            print(f"   🏢 {company} - {position}")
            print(f"   📊 Status: {status}")
            print(f"   🎯 Classification: {classification or 'Not classified'}")
            print(f"   ⭐ Score: {score or 'Not scored'}")
            print(f"   👨‍💼 Allocated to: {allocated_to or 'None'}")
            
            if message:
                print(f"   📧 Message sent: {message[:100]}...")
            else:
                print(f"   📧 Message: Not sent yet")
            
            if response:
                print(f"   💬 Response: {response[:100]}...")
            else:
                print(f"   💬 Response: No response yet")
            
            print(f"   🕐 Last updated: {updated}")
        
        # Get recent activity from logs
        print(f"\n📋 RECENT AGENT ACTIVITY:")
        print("-" * 50)
        
        log_path = "data/logs/agents.log"
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Get last 10 lines with lead activity
            lead_lines = []
            for line in reversed(lines):
                if any(keyword in line.lower() for keyword in ['lead', 'message', 'response', 'classified', 'allocated']):
                    lead_lines.append(line.strip())
                    if len(lead_lines) >= 10:
                        break
            
            if lead_lines:
                for line in reversed(lead_lines):
                    print(f"   {line}")
            else:
                print("   No recent lead activity found")
        else:
            print("   Log file not found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")

def watch_logs():
    """Show command to watch logs in real-time"""
    
    print(f"\n🔍 REAL-TIME MONITORING COMMANDS:")
    print("-" * 40)
    print("📋 Watch all agent activity:")
    print("   tail -f data/logs/agents.log")
    print("")
    print("🎯 Watch only lead-related activity:")
    print("   tail -f data/logs/agents.log | grep -i 'lead\\|message\\|response\\|classified'")
    print("")
    print("📊 Check lead status every 30 seconds:")
    print("   watch -n 30 'python tools/monitor_leads.py'")
    print("")
    print("💾 View database directly:")
    print("   sqlite3 data/state/agents.db 'SELECT * FROM leads;'")

if __name__ == "__main__":
    monitor_leads()
    watch_logs()
    
    print(f"\n🔄 Run this script anytime with: python tools/monitor_leads.py")


