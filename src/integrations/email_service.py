"""
Email service for sending daily reports.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict
from src.utils.logger import setup_logger

class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self, config: Dict):
        """
        Initialize email service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = setup_logger("EmailService")
        
        email_config = config.get("email", {})
        self.smtp_host = os.getenv("SMTP_HOST", email_config.get("smtp_host", "smtp.gmail.com"))
        self.smtp_port = int(os.getenv("SMTP_PORT", email_config.get("smtp_port", 587)))
        self.smtp_user = os.getenv("SMTP_USER", email_config.get("smtp_user", ""))
        self.smtp_password = os.getenv("SMTP_PASSWORD", email_config.get("smtp_password", ""))
        self.from_address = os.getenv("SMTP_FROM", email_config.get("from_address", self.smtp_user))
        
        # Get recipients
        to_addresses = email_config.get("to_addresses", [])
        if isinstance(to_addresses, str):
            to_addresses = [to_addresses]
        self.to_addresses = [os.getenv("SMTP_TO", addr) for addr in to_addresses if addr]
    
    def send_daily_report(self, subject: str, body: str, recipients: Optional[List[str]] = None) -> bool:
        """
        Send daily report email.
        
        Args:
            subject: Email subject
            body: Email body (plain text)
            recipients: Optional list of recipients (uses config if None)
        
        Returns:
            True if successful, False otherwise
        """
        recipients = recipients or self.to_addresses
        
        if not recipients:
            self.logger.warning("No email recipients configured")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = self.from_address
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"Daily report sent to {len(recipients)} recipient(s)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            # Log to file as backup
            self._log_report_to_file(subject, body)
            return False
    
    def _log_report_to_file(self, subject: str, body: str) -> None:
        """Log report to file as backup."""
        from pathlib import Path
        from datetime import datetime
        
        log_file = Path("data/logs") / f"report_{datetime.now().strftime('%Y%m%d')}.txt"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"{subject}\n")
            f.write(f"{datetime.now().isoformat()}\n")
            f.write(f"{'='*60}\n")
            f.write(body)
            f.write(f"\n{'='*60}\n\n")

