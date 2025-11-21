"""
LinkedIn message sender integration (Dripify/Gojiberry/Unipile).
"""

import os
import json
import requests
from typing import Optional, Dict, List
from datetime import datetime, timedelta, timezone
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
            self.headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
        elif self.service == "gojiberry":
            self.api_key = os.getenv("GOJIBERRY_API_KEY")
            self.api_url = os.getenv("GOJIBERRY_API_URL", "https://api.gojiberry.com/v1")
            self.headers = {
                'X-API-Key': self.api_key,
                'Content-Type': 'application/json'
            }
        elif self.service == "unipile":
            self.dsn = os.getenv("UNIPILE_DSN")
            self.api_key = os.getenv("UNIPILE_API_KEY")
            self.account_id = os.getenv("UNIPILE_ACCOUNT_ID")
            if not self.dsn or not self.api_key or not self.account_id:
                raise ValueError("Unipile requires UNIPILE_DSN, UNIPILE_API_KEY, and UNIPILE_ACCOUNT_ID")
            self.base_url = f"https://{self.dsn}/api/v1"
            self.headers = {
                'X-API-KEY': self.api_key,
                'accept': 'application/json',
                'Content-Type': 'application/json'
            }
            # Cache file for tracking last check timestamp
            storage_config = config.get("storage", {})
            data_dir = storage_config.get("data_directory", "data")
            self.timestamp_cache_file = os.path.join(data_dir, "state", "unipile_last_check.txt")
        else:
            raise ValueError(f"Unknown LinkedIn service: {self.service}")
        
        if self.service != "unipile" and not self.api_key:
            raise ValueError(f"{self.service.upper()}_API_KEY environment variable not set")
    
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
            elif self.service == "gojiberry":
                return self._send_via_gojiberry(linkedin_url, message)
            elif self.service == "unipile":
                return self._send_via_unipile(linkedin_url, message)
            else:
                raise ValueError(f"Unknown service: {self.service}")
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
    
    def _send_via_unipile(self, linkedin_url: str, message: str) -> SendResult:
        """
        Send message via Unipile API.
        Handles: user search → invite (if needed) → create chat → send message
        """
        try:
            # Step 1: Search for user in contacts
            user = self._find_unipile_user(linkedin_url)
            
            if not user:
                # User not in contacts → send invitation
                return self._send_unipile_invitation(linkedin_url, message)
            
            # Step 2: Create or find chat
            chat_id = self._get_or_create_chat(user["id"])
            
            # Step 3: Send message
            return self._send_unipile_message(chat_id, message)
            
        except Exception as e:
            self.logger.error(f"Unipile send error: {e}")
            return SendResult(
                success=False,
                error_message=str(e),
                timestamp=datetime.now(),
                service_used='unipile'
            )
    
    def _find_unipile_user(self, linkedin_url: str) -> Optional[Dict]:
        """Search for user in Unipile contacts by LinkedIn URL."""
        try:
            url = f"{self.base_url}/users"
            params = {
                "account_id": self.account_id,
                "provider": "LINKEDIN"
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            users = response.json().get("items", [])
            
            # Try to find user by LinkedIn URL match
            for user in users:
                user_url = user.get("provider_id", "")
                if linkedin_url in user_url or user_url in linkedin_url:
                    return user
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error finding Unipile user: {e}")
            return None
    
    def _send_unipile_invitation(self, linkedin_url: str, message: str) -> SendResult:
        """Send LinkedIn invitation via Unipile."""
        try:
            url = f"{self.base_url}/users/invite"
            payload = {
                "account_id": self.account_id,
                "linkedin_url": linkedin_url,
                "message": message
            }
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            invite_id = result.get("id", result.get("invite_id", ""))
            
            self.logger.info(f"Invitation sent via Unipile: {invite_id}")
            
            return SendResult(
                success=False,  # Not a message send, just invitation
                message_id=invite_id,
                timestamp=datetime.now(),
                service_used='unipile',
                status='invitation_sent'
            )
            
        except Exception as e:
            self.logger.error(f"Error sending Unipile invitation: {e}")
            raise
    
    def _get_or_create_chat(self, user_id: str) -> str:
        """Get existing chat or create new one with user."""
        try:
            url = f"{self.base_url}/chats"
            payload = {
                "account_id": self.account_id,
                "attendees_ids": [user_id],
                "provider": "LINKEDIN"
            }
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            chat_id = result.get("id")
            
            if not chat_id:
                raise ValueError("No chat_id returned from Unipile")
            
            return chat_id
            
        except Exception as e:
            self.logger.error(f"Error creating Unipile chat: {e}")
            raise
    
    def _send_unipile_message(self, chat_id: str, message: str) -> SendResult:
        """Send message to Unipile chat."""
        try:
            url = f"{self.base_url}/chats/{chat_id}/messages"
            payload = {
                "account_id": self.account_id,
                "text": message,
                "type": "text"
            }
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            message_id = result.get("id")
            
            self.logger.info(f"Message sent via Unipile: {message_id}")
            
            return SendResult(
                success=True,
                message_id=message_id,
                timestamp=datetime.now(),
                service_used='unipile',
                status='sent'
            )
            
        except Exception as e:
            self.logger.error(f"Error sending Unipile message: {e}")
            raise
    
    def check_invitation_status(self, invite_id: str, linkedin_url: str) -> str:
        """
        Check if invitation was accepted (polling).
        
        Args:
            invite_id: Invitation ID (may not be used, kept for compatibility)
            linkedin_url: LinkedIn profile URL to check
            
        Returns:
            "pending", "accepted", "declined", or "expired"
        """
        if self.service != "unipile":
            return "pending"
        
        try:
            # Check if user is now in contacts (invitation accepted)
            user = self._find_unipile_user(linkedin_url)
            if user and user.get("connection_status") == "connected":
                return "accepted"
            return "pending"
            
        except Exception as e:
            self.logger.error(f"Error checking invitation status: {e}")
            return "pending"
    
    def _get_last_check_timestamp(self) -> str:
        """Get timestamp of last response check from cache file."""
        try:
            if os.path.exists(self.timestamp_cache_file):
                with open(self.timestamp_cache_file, 'r') as f:
                    timestamp = f.read().strip()
                    if timestamp:
                        return timestamp
        except Exception as e:
            self.logger.warning(f"Error reading timestamp cache: {e}")
        
        # Default: 24 hours ago (conservative, to catch any missed messages)
        # Format: ISO 8601 with UTC timezone (Unipile API format)
        default_time = datetime.now(timezone.utc) - timedelta(hours=24)
        return default_time.replace(microsecond=0).isoformat()
    
    def _update_last_check_timestamp(self) -> None:
        """Save current timestamp as last check time."""
        try:
            os.makedirs(os.path.dirname(self.timestamp_cache_file), exist_ok=True)
            # Save timestamp without microseconds, with UTC timezone (Unipile API format)
            timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            with open(self.timestamp_cache_file, 'w') as f:
                f.write(timestamp)
        except Exception as e:
            self.logger.warning(f"Error updating timestamp cache: {e}")
    
    def _get_chat_info(self, chat_id: str) -> Dict:
        """Get chat details to extract sender LinkedIn URL."""
        try:
            url = f"{self.base_url}/chats/{chat_id}"
            params = {"account_id": self.account_id}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            chat = response.json()
            
            # Extract LinkedIn URL from attendees
            attendees = chat.get("attendees", [])
            for attendee in attendees:
                if attendee.get("id") != self.account_id:  # Not our account
                    return {
                        "sender_linkedin_url": attendee.get("provider_id", "")
                    }
            
            return {}
            
        except Exception as e:
            self.logger.warning(f"Error getting chat info: {e}")
            return {}
    
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
            elif self.service == "gojiberry":
                # Gojiberry implementation (adjust based on actual API)
                url = f"{self.api_url}/responses"
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                return response.json().get('responses', [])
            elif self.service == "unipile":
                return self._check_unipile_responses()
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error checking responses: {e}")
            return []
    
    def _check_unipile_responses(self) -> List[Dict]:
        """
        Poll for new messages from Unipile API.
        Unipile doesn't have a direct /messages endpoint, so we:
        1. Get list of chats
        2. For each chat, get messages
        3. Filter for incoming messages (is_sender=0) since last check
        """
        try:
            # Get timestamp of last check
            since_str = self._get_last_check_timestamp()
            # Normalize to UTC timezone-aware datetime
            if 'Z' in since_str:
                since_dt = datetime.fromisoformat(since_str.replace('Z', '+00:00'))
            elif '+' in since_str or since_str.count('-') > 2:  # Has timezone
                since_dt = datetime.fromisoformat(since_str)
            else:  # Naive datetime, assume UTC
                since_dt = datetime.fromisoformat(since_str).replace(tzinfo=timezone.utc)
            
            # Step 1: Get list of chats
            chats_url = f"{self.base_url}/chats"
            chats_params = {
                "account_id": self.account_id,
                "limit": 100
            }
            
            chats_response = requests.get(chats_url, headers=self.headers, params=chats_params, timeout=30)
            
            if chats_response.status_code == 503:
                self.logger.warning("Unipile API temporarily unavailable (503) when fetching chats. Will retry on next check.")
                return []
            
            chats_response.raise_for_status()
            chats = chats_response.json().get("items", [])
            
            # Step 2: Get messages for each chat and filter for new incoming messages
            all_responses = []
            
            for chat in chats:
                chat_id = chat.get("id")
                if not chat_id:
                    continue
                
                try:
                    # Get messages for this chat
                    messages_url = f"{self.base_url}/chats/{chat_id}/messages"
                    messages_params = {
                        "account_id": self.account_id,
                        "limit": 50  # Get recent messages per chat
                    }
                    
                    messages_response = requests.get(messages_url, headers=self.headers, params=messages_params, timeout=30)
                    
                    if messages_response.status_code == 503:
                        self.logger.warning(f"Unipile API temporarily unavailable (503) for chat {chat_id}. Skipping.")
                        continue
                    
                    messages_response.raise_for_status()
                    messages = messages_response.json().get("items", [])
                    
                    # Filter for incoming messages (is_sender=0) that are newer than last check
                    for msg in messages:
                        if msg.get("is_sender") == 0:  # Incoming message
                            msg_timestamp_str = msg.get("timestamp", "")
                            if msg_timestamp_str:
                                try:
                                    # Normalize message timestamp to UTC timezone-aware datetime
                                    if 'Z' in msg_timestamp_str:
                                        msg_dt = datetime.fromisoformat(msg_timestamp_str.replace('Z', '+00:00'))
                                    elif '+' in msg_timestamp_str or msg_timestamp_str.count('-') > 2:  # Has timezone
                                        msg_dt = datetime.fromisoformat(msg_timestamp_str)
                                    else:  # Naive datetime, assume UTC
                                        msg_dt = datetime.fromisoformat(msg_timestamp_str).replace(tzinfo=timezone.utc)
                                    
                                    if msg_dt > since_dt:
                                        # Get sender LinkedIn URL
                                        # sender_id is LinkedIn profile ID (e.g., "ACoAAASCRCQBFAgCKtUUV5UTjIoiFVUEYIBMdDE")
                                        sender_id = msg.get("sender_id", "")
                                        linkedin_url = f"https://www.linkedin.com/in/{sender_id}/" if sender_id else ""
                                        
                                        all_responses.append({
                                            "message_id": msg.get("id"),
                                            "text": msg.get("text", ""),
                                            "linkedin_url": linkedin_url,
                                            "timestamp": msg_timestamp_str
                                        })
                                except (ValueError, TypeError) as e:
                                    self.logger.warning(f"Error parsing message timestamp: {e}")
                                    continue
                
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code != 503:
                        self.logger.warning(f"Error fetching messages for chat {chat_id}: {e}")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error processing chat {chat_id}: {e}")
                    continue
            
            # Update last check timestamp only if we got successful responses
            if all_responses:
                self._update_last_check_timestamp()
            
            return all_responses
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code != 503:
                self.logger.error(f"HTTP error checking Unipile responses: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error checking Unipile responses: {e}")
            return []

