"""
Google Sheets integration for reading and writing lead data.
"""

import os
import re
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
        lead_finder_cfg = self.config.get("lead_finder", {})
        self.default_quality_score = lead_finder_cfg.get("default_quality_score", 5.0)
        
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
                if not record.get("Lead ID"):
                    continue
                
                lead = self._record_to_lead(record)
                
                if filters and not self._lead_matches_filters(lead, filters):
                    continue
                
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
    
    def _lead_matches_filters(self, lead: Lead, filters: Dict[str, Any]) -> bool:
        """Check if lead matches provided filters."""
        for key, expected_value in filters.items():
            value = getattr(lead, key, None)
            
            if isinstance(expected_value, str):
                if (value or "").strip().lower() != expected_value.strip().lower():
                    return False
            else:
                if value != expected_value:
                    return False
        
        return True
    
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
            
            value = str(dt_str).strip()
            if not value:
                return None
            
            # Normalize stray unicode whitespace
            value = re.sub(r"\s+", " ", value)
            
            iso_candidate = value
            try:
                if 'Z' in iso_candidate:
                    return datetime.fromisoformat(iso_candidate.replace('Z', '+00:00'))
                return datetime.fromisoformat(iso_candidate)
            except (ValueError, AttributeError):
                pass
            
            fallback_formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%d.%m.%Y %H:%M:%S",
                "%d.%m.%Y %H:%M",
                "%d.%m.%Y",
                "%d/%m/%Y %H:%M:%S",
                "%d/%m/%Y %H:%M",
                "%d/%m/%Y",
            ]
            
            for fmt in fallback_formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            
            # Try fixing common typos like 5-digit years (e.g., "17.11.20225")
            match = re.match(r"(\d{1,2})[./](\d{1,2})[./](\d{4,5})(?:\s+(\d{1,2}:\d{2}(:\d{2})?))?", value)
            if match:
                day, month, year, time_part, _ = match.groups()
                
                if len(year) != 4:
                    fixed_year = None
                    if len(year) > 4:
                        for idx in range(len(year)):
                            candidate = year[:idx] + year[idx+1:]
                            if len(candidate) == 4 and candidate.isdigit() and 1900 <= int(candidate) <= 2100:
                                fixed_year = candidate
                                break
                    if not fixed_year and len(year) > 4:
                        fixed_year = year[:4]
                    year = fixed_year or year
                
                normalized = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
                if time_part:
                    normalized = f"{normalized} {time_part}"
                for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y"):
                    try:
                        return datetime.strptime(normalized, fmt)
                    except ValueError:
                        continue
            
            self.logger.warning(f"Could not parse datetime: {value}")
            return None
        
        def parse_quality_score(value: Optional[Any]) -> float:
            if value in (None, ""):
                return self.default_quality_score
            str_value = str(value).strip().replace(",", ".")
            try:
                return float(str_value)
            except ValueError:
                self.logger.warning(
                    f"Invalid quality score '{value}', using default {self.default_quality_score}"
                )
                return self.default_quality_score
        
        def parse_contact_status(value: Optional[str]) -> str:
            default_status = "Not Contacted"
            if not value:
                return default_status
            
            normalized = str(value).strip()
            valid_statuses = {
                "Not Contacted",
                "Allocated",
                "Message Sent",
                "Responded",
                "Closed",
                "Failed",
            }
            
            if normalized in valid_statuses:
                return normalized
            
            self.logger.warning(f"Unknown contact status '{value}', defaulting to {default_status}")
            return default_status
        
        raw_classification = record.get("Classification")
        classification = raw_classification.strip() if isinstance(raw_classification, str) else raw_classification
        if classification and classification.lower() == "not contacted":
            classification = None
        
        return Lead(
            id=record.get("Lead ID", ""),
            name=record.get("Name", ""),
            position=record.get("Position", ""),
            company=record.get("Company", ""),
            linkedin_url=record.get("LinkedIn URL", ""),
            classification=classification,
            quality_score=parse_quality_score(record.get("Quality Score")),
            contact_status=parse_contact_status(record.get("Contact Status")),
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

