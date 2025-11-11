"""
LinkedIn message sender integration (Dripify/Gojiberry).
"""

import os
import requests
from typing import Optional, Dict, List
from datetime import datetime
from src.core.models import SendResult
from src.utils.logger import setup_logger

class LinkedInAPIError(Exception):
    """Raised when LinkedIn API operations fail."""
    pass

class LinkedInSender:
    """Unified interface for LinkedIn automation services."""
    
    def __init__(self, config: Dict):
        """
        Initialize LinkedIn sender.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = setup_logger("LinkedInSender")
        
        # Get service type
        linkedin_config = config.get("linkedin", {})
        self.service = os.getenv("LINKEDIN_SERVICE", linkedin_config.get("service", "dripify"))
        
        if self.service == "dripify":
            self.api_key = os.getenv("DRIPIFY_API_KEY")
            self.api_url = os.getenv("DRIPIFY_API_URL", "https://api.dripify.io/v1")
        elif self.service == "gojiberry":
            self.api_key = os.getenv("GOJIBERRY_API_KEY")
            self.api_url = os.getenv("GOJIBERRY_API_URL", "https://api.gojiberry.com/v1")
        else:
            raise ValueError(f"Unknown LinkedIn service: {self.service}")
        
        if not self.api_key:
            raise ValueError(f"{self.service.upper()}_API_KEY environment variable not set")
        
        # Setup headers
        if self.service == "dripify":
            self.headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
        else:  # gojiberry
            self.headers = {
                'X-API-Key': self.api_key,
                'Content-Type': 'application/json'
            }
    
    def send_message(self, linkedin_url: str, message: str) -> SendResult:
        """
        Send LinkedIn message.
        
        Args:
            linkedin_url: LinkedIn profile URL
            message: Message text
        
        Returns:
            SendResult object
        """
        try:
            if self.service == "dripify":
                return self._send_via_dripify(linkedin_url, message)
            else:
                return self._send_via_gojiberry(linkedin_url, message)
        except Exception as e:
            self.logger.error(f"Error sending LinkedIn message: {e}")
            return SendResult(
                success=False,
                error_message=str(e),
                timestamp=datetime.now(),
                service_used=self.service
            )
    
    def _send_via_dripify(self, linkedin_url: str, message: str) -> SendResult:
        """Send message via Dripify API."""
        url = f"{self.api_url}/messages/send"
        
        payload = {
            'linkedin_profile_url': linkedin_url,
            'message': message,
            'account_id': os.getenv("DRIPIFY_ACCOUNT_ID", "")
        }
        
        response = requests.post(url, json=payload, headers=self.headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return SendResult(
            success=True,
            message_id=result.get('message_id'),
            timestamp=datetime.now(),
            service_used='dripify'
        )
    
    def _send_via_gojiberry(self, linkedin_url: str, message: str) -> SendResult:
        """Send message via Gojiberry API."""
        url = f"{self.api_url}/send-message"
        
        payload = {
            'profile_url': linkedin_url,
            'text': message
        }
        
        response = requests.post(url, json=payload, headers=self.headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return SendResult(
            success=True,
            message_id=result.get('id'),
            timestamp=datetime.now(),
            service_used='gojiberry'
        )
    
    def check_responses(self) -> List[Dict]:
        """
        Check for new responses.
        
        Returns:
            List of response dictionaries
        """
        try:
            if self.service == "dripify":
                url = f"{self.api_url}/messages/responses"
                params = {'account_id': os.getenv("DRIPIFY_ACCOUNT_ID", "")}
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                return response.json().get('responses', [])
            else:
                # Gojiberry implementation (adjust based on actual API)
                url = f"{self.api_url}/responses"
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                return response.json().get('responses', [])
        except Exception as e:
            self.logger.error(f"Error checking responses: {e}")
            return []

