"""
Google Sheets integration for reading and writing lead data.
"""

import os
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.core.models import Lead
from src.utils.logger import setup_logger

class GoogleSheetsError(Exception):
    """Raised when Google Sheets operations fail."""
    pass

class GoogleSheetsIO:
    """Interface for Google Sheets operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Google Sheets client.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = setup_logger("GoogleSheetsIO")
        
        # Get credentials path
        creds_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "config/google-credentials.json")
        if not os.path.exists(creds_path):
            raise FileNotFoundError(f"Google credentials file not found: {creds_path}")
        
        # Authenticate
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(creds_path, scopes=scope)
        self.client = gspread.authorize(creds)
        
        # Get spreadsheet ID
        spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
        if not spreadsheet_id:
            raise ValueError("GOOGLE_SHEETS_SPREADSHEET_ID environment variable not set")
        
        # Open spreadsheet
        try:
            self.spreadsheet = self.client.open_by_key(spreadsheet_id)
            self.leads_sheet = self.spreadsheet.worksheet("Leads")
        except Exception as e:
            raise GoogleSheetsError(f"Failed to open spreadsheet: {e}")
    
    def read_leads(self, filters: Optional[Dict[str, Any]] = None) -> List[Lead]:
        """
        Read leads from Google Sheets.
        
        Args:
            filters: Optional filters (e.g., {"contact_status": "Not Contacted"})
        
        Returns:
            List of Lead objects
        """
        try:
            # Get all records
            records = self.leads_sheet.get_all_records()
            
            leads = []
            for record in records:
                # Skip empty rows
                if not record.get("Lead ID"):
                    continue
                
                # Apply filters
                if filters:
                    match = True
                    for key, value in filters.items():
                        if record.get(key) != value:
                            match = False
                            break
                    if not match:
                        continue
                
                # Convert to Lead object
                lead = self._record_to_lead(record)
                leads.append(lead)
            
            return leads
            
        except Exception as e:
            self.logger.error(f"Error reading leads: {e}")
            raise GoogleSheetsError(f"Failed to read leads: {e}")
    
    def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update lead in Google Sheets.
        
        Args:
            lead_id: Lead ID
            updates: Dictionary of fields to update
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find row by Lead ID
            cell = self.leads_sheet.find(lead_id, in_column=1)  # Column 1 is Lead ID
            if not cell:
                self.logger.warning(f"Lead not found: {lead_id}")
                return False
            
            row = cell.row
            
            # Get header row to find column indices
            headers = self.leads_sheet.row_values(1)
            
            # Update fields
            for field, value in updates.items():
                if field in headers:
                    col_index = headers.index(field) + 1  # gspread uses 1-based indexing
                    self.leads_sheet.update_cell(row, col_index, value)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating lead {lead_id}: {e}")
            return False
    
    def _record_to_lead(self, record: Dict[str, Any]) -> Lead:
        """
        Convert Google Sheets record to Lead object.
        
        Args:
            record: Record dictionary from Google Sheets
        
        Returns:
            Lead object
        """
        # Parse datetime strings
        def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
            if not dt_str:
                return None
            try:
                # Try ISO format first (with Z timezone)
                if 'Z' in dt_str:
                    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                # Try standard ISO format
                return datetime.fromisoformat(dt_str)
            except (ValueError, AttributeError):
                # Try alternative formats (Google Sheets might return different formats)
                try:
                    # Format: "2025-01-15 10:30:00"
                    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        # Format: "2025-01-15T10:30:00"
                        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
                    except ValueError:
                        self.logger.warning(f"Could not parse datetime: {dt_str}")
                        return None
        
        return Lead(
            id=record.get("Lead ID", ""),
            name=record.get("Name", ""),
            position=record.get("Position", ""),
            company=record.get("Company", ""),
            linkedin_url=record.get("LinkedIn URL", ""),
            classification=record.get("Classification"),
            quality_score=float(record.get("Quality Score")) if record.get("Quality Score") else None,
            contact_status=record.get("Contact Status", "Not Contacted"),
            allocated_to=record.get("Allocated To"),
            allocated_at=parse_datetime(record.get("Allocated At")),
            message_sent=record.get("Message Sent"),
            message_sent_at=parse_datetime(record.get("Message Sent At")),
            response=record.get("Response"),
            response_received_at=parse_datetime(record.get("Response Received At")),
            response_sentiment=record.get("Response Sentiment"),
            response_intent=record.get("Response Intent"),
            created_at=parse_datetime(record.get("Created At")) or datetime.now(),
            last_updated=parse_datetime(record.get("Last Updated")) or datetime.now(),
            notes=record.get("Notes")
        )

