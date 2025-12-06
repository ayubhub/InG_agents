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
        Strategy: 
        1. Try to find existing chat (user in contacts)
        2. If not found, try to send invitation
        3. If invitation sent, return status (message will be sent after invitation accepted)
        """
        try:
            # Step 1: Try to find existing chat (user must be in contacts)
            existing_chat = self._find_unipile_user_in_chats(linkedin_url)
            
            if existing_chat:
                chat_id = existing_chat["id"]
                provider_id = existing_chat.get("provider_id", "")
                self.logger.info(f"Found existing chat {chat_id} for {provider_id}")
                # Step 2: Send message to existing chat
                return self._send_unipile_message(chat_id, message)
            else:
                # User not in contacts - try to get LinkedIn ID and send invitation
                self.logger.info(f"User not in contacts for {linkedin_url}, attempting to get LinkedIn ID and send invitation")
                
                # Step 1: Try to get full LinkedIn ID via profile lookup
                linkedin_id = self._get_linkedin_id_by_identifier(linkedin_url)
                
                if linkedin_id:
                    # Step 2: Send invitation with full LinkedIn ID
                    self.logger.info(f"Found LinkedIn ID {linkedin_id} for {linkedin_url}, sending invitation")
                    try:
                        return self._send_unipile_invitation(linkedin_id, message)
                    except Exception as invite_error:
                        error_msg = (
                            f"Failed to send invitation. LinkedIn URL: {linkedin_url}, ID: {linkedin_id}. "
                            f"Error: {invite_error}"
                        )
                        self.logger.error(error_msg)
                        return SendResult(
                            success=False,
                            error_message=error_msg,
                            timestamp=datetime.now(),
                            service_used='unipile',
                            status='invitation_failed'
                        )
                else:
                    # Could not find LinkedIn ID via search - try sending invitation with URL directly
                    self.logger.warning(f"Could not find LinkedIn ID for {linkedin_url}, trying to send invitation with URL directly")
                    try:
                        # Try sending invitation using LinkedIn URL directly (some Unipile API versions support this)
                        return self._send_unipile_invitation_by_url(linkedin_url, message)
                    except Exception as url_invite_error:
                        # If that also fails, provide helpful error message
                        username = self._extract_linkedin_provider_id(linkedin_url)
                        error_msg = (
                            f"Could not find LinkedIn ID for URL: {linkedin_url} (username: {username}). "
                            f"Tried both ID lookup and direct URL invitation - both failed.\n"
                            f"Error: {url_invite_error}\n\n"
                            f"This can happen when:\n"
                            f"• User profile is private or not searchable via API\n"
                            f"• LinkedIn has anti-scraping measures active\n"
                            f"• User changed their LinkedIn username recently\n"
                            f"• Unipile API rate limits or restrictions\n"
                            f"• LinkedIn account needs to be re-authenticated in Unipile\n\n"
                            f"WORKAROUND: Send invitation manually:\n"
                            f"1. Go to Unipile dashboard\n"
                            f"2. Navigate to LinkedIn account\n"
                            f"3. Send invitation to: {linkedin_url}\n"
                            f"4. Once accepted, messages will work automatically"
                        )
                        self.logger.warning(error_msg)
                        return SendResult(
                            success=False,
                            error_message=error_msg,
                            timestamp=datetime.now(),
                            service_used='unipile',
                            status='user_not_found'
                        )
            
        except Exception as e:
            self.logger.error(f"Unipile send error: {e}")
            return SendResult(
                success=False,
                error_message=str(e),
                timestamp=datetime.now(),
                service_used='unipile'
            )
    
    def _extract_linkedin_provider_id(self, linkedin_url: str) -> Optional[str]:
        """
        Extract LinkedIn username/public identifier from LinkedIn URL.
        
        Args:
            linkedin_url: LinkedIn profile URL (e.g., https://www.linkedin.com/in/dashaborysov/)
            
        Returns:
            Username/public identifier (e.g., "dashaborysov") or None if invalid
        """
        try:
            import re
            
            # Remove trailing slash and normalize
            url = linkedin_url.strip().rstrip('/')
            
            # Pattern to match LinkedIn profile URLs
            # Supports various formats:
            # - https://www.linkedin.com/in/username
            # - https://linkedin.com/in/username
            # - www.linkedin.com/in/username
            # - linkedin.com/in/username
            pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/([a-zA-Z0-9\-_]+)/?'
            
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                username = match.group(1)
                self.logger.debug(f"Extracted LinkedIn username: {username} from URL: {linkedin_url}")
                return username
            else:
                self.logger.warning(f"Could not extract username from LinkedIn URL: {linkedin_url}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting LinkedIn username from {linkedin_url}: {e}")
            return None
    
    def _get_linkedin_id_by_identifier(self, linkedin_url: str) -> Optional[str]:
        """
        Get full LinkedIn ID by retrieving user profile via Unipile API.
        Uses multiple approaches to find the LinkedIn ID.
        """
        try:
            # Extract username from URL
            username = self._extract_linkedin_provider_id(linkedin_url)
            if not username:
                self.logger.error(f"Could not extract username from LinkedIn URL: {linkedin_url}")
                return None
            
            # Method 1: Try direct user lookup by username
            provider_id = self._try_direct_user_lookup(username, linkedin_url)
            if provider_id:
                return provider_id
            
            # Method 2: Try search approach
            provider_id = self._try_search_user_lookup(username, linkedin_url)
            if provider_id:
                return provider_id
            
            # Method 3: Check if user is already in contacts/chats
            provider_id = self._try_contacts_lookup(linkedin_url)
            if provider_id:
                return provider_id
            
            self.logger.error(f"Could not find LinkedIn ID for URL: {linkedin_url}. User may not be searchable or may not exist.")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting LinkedIn ID for {linkedin_url}: {e}")
            return None
    
    def _try_direct_user_lookup(self, username: str, linkedin_url: str) -> Optional[str]:
        """Try direct user lookup by username."""
        try:
            url = f"{self.base_url}/users/{username}"
            params = {"account_id": self.account_id}
            
            self.logger.debug(f"Trying direct lookup for username: {username}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 404:
                self.logger.debug(f"Direct lookup: User not found: {username}")
                return None
            
            if response.status_code != 200:
                error_text = response.text[:200] if hasattr(response, 'text') else str(response.status_code)
                self.logger.warning(f"Direct lookup failed with status {response.status_code}: {error_text}")
                # If it's a 403 or 401, LinkedIn might be blocking access
                if response.status_code in [401, 403]:
                    self.logger.warning(f"LinkedIn may be blocking API access (status {response.status_code})")
                return None
            
            result = response.json()
            provider_id = result.get("provider_id")
            public_identifier = result.get("public_identifier", "")
            
            if provider_id:
                self.logger.info(f"Found LinkedIn ID via direct lookup: {provider_id} for {username}")
                return provider_id
            
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Direct lookup request failed for {username}: {e}")
            return None
        except Exception as e:
            self.logger.debug(f"Direct lookup failed for {username}: {e}")
            return None
    
    def _try_search_user_lookup(self, username: str, linkedin_url: str) -> Optional[str]:
        """Try to find user via search functionality."""
        try:
            # Try searching for the user by name or username
            url = f"{self.base_url}/users/search"
            params = {
                "account_id": self.account_id,
                "query": username,
                "limit": 10
            }
            
            self.logger.debug(f"Trying search lookup for username: {username}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code != 200:
                error_text = response.text[:200] if hasattr(response, 'text') else str(response.status_code)
                self.logger.warning(f"Search lookup failed with status {response.status_code}: {error_text}")
                # If it's a 403 or 401, LinkedIn might be blocking access
                if response.status_code in [401, 403]:
                    self.logger.warning(f"LinkedIn may be blocking search API access (status {response.status_code})")
                return None
            
            result = response.json()
            users = result.get("items", [])
            
            # Look for exact match by public_identifier
            for user in users:
                public_identifier = user.get("public_identifier", "")
                if public_identifier.lower() == username.lower():
                    provider_id = user.get("provider_id")
                    if provider_id:
                        self.logger.info(f"Found LinkedIn ID via search: {provider_id} for {username}")
                        return provider_id
            
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Search lookup request failed for {username}: {e}")
            return None
        except Exception as e:
            self.logger.debug(f"Search lookup failed for {username}: {e}")
            return None
    
    def _try_contacts_lookup(self, linkedin_url: str) -> Optional[str]:
        """Check if user is already in contacts/chats."""
        try:
            user_chat = self._find_unipile_user_in_chats(linkedin_url)
            if user_chat and user_chat.get("provider_id"):
                provider_id = user_chat["provider_id"]
                self.logger.info(f"Found LinkedIn ID in existing chats: {provider_id}")
                return provider_id
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Contacts lookup failed for {linkedin_url}: {e}")
            return None
    
    def _find_unipile_user_in_chats(self, linkedin_url: str) -> Optional[Dict]:
        """Search for user in existing chats by LinkedIn URL."""
        try:
            # Get all chats and check attendees
            url = f"{self.base_url}/chats"
            params = {
                "account_id": self.account_id,
                "limit": 100
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            chats = response.json().get("items", [])
            
            # Try to get LinkedIn ID from URL first (more reliable)
            linkedin_id = self._get_linkedin_id_by_identifier(linkedin_url)
            
            # Normalize LinkedIn URL for comparison
            linkedin_url_normalized = linkedin_url.lower().rstrip('/')
            username = self._extract_linkedin_provider_id(linkedin_url)
            
            # Search in chats for matching attendee
            # attendee_provider_id is usually full LinkedIn ID (e.g., ACoAAE7X2j4BhlsL3pPOcNuKUT6f5DQ5XhOvoHI)
            for chat in chats:
                attendee_provider_id = chat.get("attendee_provider_id", "")
                if not attendee_provider_id:
                    continue
                
                # Match by LinkedIn ID (most reliable)
                if linkedin_id and attendee_provider_id == linkedin_id:
                    self.logger.debug(f"Found user in chats by LinkedIn ID: {linkedin_id}")
                    return {
                        "id": chat.get("id"),
                        "provider_id": attendee_provider_id
                    }
                
                # Fallback: Check if LinkedIn URL contains the provider_id or vice versa
                # Also check if provider_id is part of the LinkedIn URL path
                if (attendee_provider_id.lower() in linkedin_url_normalized or 
                    linkedin_url_normalized.endswith(f"/{attendee_provider_id.lower()}/") or
                    linkedin_url_normalized.endswith(f"/{attendee_provider_id.lower()}") or
                    (username and username.lower() in attendee_provider_id.lower())):
                    self.logger.debug(f"Found user in chats by URL/username match: {linkedin_url}")
                    return {
                        "id": chat.get("id"),
                        "provider_id": attendee_provider_id
                    }
            
            self.logger.debug(f"User not found in existing chats for {linkedin_url}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Error finding user in chats: {e}")
            return None
    
    def _send_unipile_invitation(self, provider_id: str, message: str) -> SendResult:
        """
        Send LinkedIn invitation via Unipile using provider_id (full LinkedIn ID).
        
        Args:
            provider_id: Full LinkedIn ID (e.g., ACoAAE7X2j4BhlsL3pPOcNuKUT6f5DQ5XhOvoHI)
            message: Invitation message (will be truncated to 300 chars if longer)
        
        Returns:
            SendResult with status='invitation_sent' if successful
        """
        try:
            # Normalize message: replace newlines with spaces (LinkedIn may count them differently)
            # Also collapse multiple spaces
            import re
            message = re.sub(r'\s+', ' ', message.replace('\n', ' ').replace('\r', ' ')).strip()
            
            # Truncate message to 200 characters (very conservative limit)
            # Testing showed that messages up to 250 chars work via curl, but in practice
            # API may count characters differently (UTF-8 bytes, special chars, etc.)
            max_length = 200
            if len(message) > max_length:
                original_length = len(message)
                # Truncate to leave room for ellipsis, try to break at word boundary
                truncated = message[:max_length - 3]
                # Find last space to avoid breaking words
                last_space = truncated.rfind(' ')
                if last_space > max_length - 30:  # Only use word boundary if it's not too far back
                    truncated = truncated[:last_space]
                message = truncated.rstrip() + "..."
                final_length = len(message)
                self.logger.warning(
                    f"Invitation message truncated from {original_length} to {final_length} characters"
                )
            
            # Log what we're sending for debugging
            message_bytes = len(message.encode('utf-8'))
            self.logger.info(
                f"Sending invitation message: {len(message)} chars, {message_bytes} bytes. "
                f"Preview: {message[:80]}..."
            )
            
            url = f"{self.base_url}/users/invite"
            payload = {
                "account_id": self.account_id,
                "provider_id": provider_id,
                "message": message
            }
            
            self.logger.info(f"Attempting to send invitation to provider_id: {provider_id}")
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            
            # Handle different error status codes
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", str(error_data))
                    self.logger.warning(f"Invitation failed (400): {error_detail}")
                    
                    # Check if error is about message length
                    if "length" in error_detail.lower() or "300" in error_detail or "character" in error_detail.lower():
                        raise ValueError(
                            f"Cannot send invitation: message is too long. "
                            f"Error: {error_detail}"
                        )
                    
                    # Check if error is about provider_id format
                    if "format" in error_detail.lower() or "invalid" in error_detail.lower():
                        raise ValueError(
                            f"Cannot send invitation: provider_id format issue. "
                            f"Error: {error_detail}"
                        )
                    
                    raise ValueError(f"Cannot send invitation: {error_detail}")
                except ValueError:
                    raise
                except Exception as e:
                    raise ValueError(f"Cannot send invitation: {response.text}")
            
            elif response.status_code == 422:
                # 422 Unprocessable Entity - usually means invitation already sent recently
                try:
                    error_data = response.json()
                    error_type = error_data.get("type", "")
                    error_detail = error_data.get("detail", str(error_data))
                    error_title = error_data.get("title", "")
                    
                    self.logger.warning(f"Invitation failed (422): {error_title} - {error_detail}")
                    
                    # Check if it's "already invited recently" error
                    if "already" in error_type.lower() or "recently" in error_detail.lower():
                        # This is not really an error - invitation was already sent
                        # Return a special status to indicate this
                        self.logger.info(f"Invitation already sent recently (not an error): {error_detail}")
                        return SendResult(
                            success=False,  # Not a new send
                            message_id="already_sent",  # Placeholder ID
                            timestamp=datetime.now(),
                            service_used='unipile',
                            status='invitation_already_sent'
                        )
                    
                    raise ValueError(f"Cannot send invitation (422): {error_title} - {error_detail}")
                except ValueError:
                    raise
                except Exception as e:
                    raise ValueError(f"Cannot send invitation (422): {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            # Unipile API returns "invitation_id" field in successful response
            invite_id = result.get("invitation_id", result.get("id", result.get("invite_id", "")))
            
            if not invite_id:
                self.logger.warning(f"Invitation sent but no invitation_id in response: {result}")
                invite_id = "unknown"  # Fallback if API doesn't return ID
            
            self.logger.info(f"✓ Invitation sent via Unipile: {invite_id}")
            
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
    
    def _send_unipile_invitation_by_url(self, linkedin_url: str, message: str) -> SendResult:
        """
        Try to send LinkedIn invitation using LinkedIn URL directly (fallback method).
        Some Unipile API versions may support this when provider_id lookup fails.
        
        Args:
            linkedin_url: Full LinkedIn profile URL
            message: Invitation message
        
        Returns:
            SendResult with status='invitation_sent' if successful
        """
        try:
            # Normalize message
            import re
            message = re.sub(r'\s+', ' ', message.replace('\n', ' ').replace('\r', ' ')).strip()
            max_length = 200
            if len(message) > max_length:
                truncated = message[:max_length - 3]
                last_space = truncated.rfind(' ')
                if last_space > max_length - 30:
                    truncated = truncated[:last_space]
                message = truncated.rstrip() + "..."
            
            url = f"{self.base_url}/users/invite"
            # Try with linkedin_url parameter instead of provider_id
            payload = {
                "account_id": self.account_id,
                "linkedin_url": linkedin_url,
                "message": message
            }
            
            self.logger.info(f"Attempting to send invitation using LinkedIn URL directly: {linkedin_url}")
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            
            # Handle different error status codes
            if response.status_code == 400:
                error_data = response.json()
                error_detail = error_data.get("detail", str(error_data))
                self.logger.warning(f"Invitation by URL failed (400): {error_detail}")
                raise ValueError(f"Cannot send invitation by URL: {error_detail}")
            
            elif response.status_code == 422:
                error_data = response.json()
                error_type = error_data.get("type", "")
                error_detail = error_data.get("detail", str(error_data))
                
                if "already" in error_type.lower() or "recently" in error_detail.lower():
                    self.logger.info(f"Invitation already sent recently (not an error): {error_detail}")
                    return SendResult(
                        success=False,
                        message_id="already_sent",
                        timestamp=datetime.now(),
                        service_used='unipile',
                        status='invitation_already_sent'
                    )
                
                raise ValueError(f"Cannot send invitation by URL (422): {error_detail}")
            
            response.raise_for_status()
            
            result = response.json()
            invite_id = result.get("invitation_id", result.get("id", result.get("invite_id", "unknown")))
            
            self.logger.info(f"✓ Invitation sent via Unipile using URL: {invite_id}")
            
            return SendResult(
                success=False,
                message_id=invite_id,
                timestamp=datetime.now(),
                service_used='unipile',
                status='invitation_sent'
            )
            
        except Exception as e:
            self.logger.error(f"Error sending Unipile invitation by URL: {e}")
            raise
    
    def _get_or_create_chat_by_provider_id(self, provider_id: str) -> str:
        """Create new chat with user by LinkedIn provider_id."""
        try:
            url = f"{self.base_url}/chats"
            payload = {
                "account_id": self.account_id,
                "attendees_ids": [provider_id],
                "provider": "LINKEDIN"
            }
            
            self.logger.debug(f"Creating chat with provider_id: {provider_id}")
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            
            if response.status_code == 400:
                error_detail = response.json().get("detail", "")
                self.logger.warning(f"Chat creation failed: {error_detail}")
                # User not in contacts, need to send invitation first
                raise ValueError(f"Cannot create chat: user {provider_id} not in contacts")
            
            response.raise_for_status()
            
            result = response.json()
            chat_id = result.get("id")
            
            if not chat_id:
                raise ValueError("No chat_id returned from Unipile")
            
            self.logger.info(f"Created chat {chat_id} for provider_id {provider_id}")
            return chat_id
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                error_detail = e.response.json().get("detail", "")
                # User not in contacts, need to send invitation first
                self.logger.warning(f"User {provider_id} not in contacts: {error_detail}")
                raise ValueError(f"Cannot create chat: user {provider_id} not in contacts")
            raise
        except Exception as e:
            self.logger.error(f"Error creating Unipile chat: {e}")
            raise
    
    def _send_invitation_and_wait(self, provider_id: str) -> str:
        """Send invitation and return a placeholder chat_id (invitation needs to be accepted first)."""
        # For now, raise an error - invitation needs to be handled separately
        raise ValueError(f"User {provider_id} not in contacts. Please send LinkedIn invitation first through Unipile dashboard.")
    
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
            # API returns "message_id" field (not "id")
            message_id = result.get("message_id") or result.get("id")
            
            if not message_id:
                self.logger.warning(f"Unipile API response missing message_id: {result}")
            
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
        
        Strategy: If user is found in existing chats, invitation was accepted.
        
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
            # If user is found in chats, it means invitation was accepted
            user_chat = self._find_unipile_user_in_chats(linkedin_url)
            if user_chat:
                self.logger.info(f"User found in chats - invitation accepted: {linkedin_url}")
                return "accepted"
            
            # User not in chats yet - invitation still pending
            self.logger.debug(f"User not in chats yet - invitation pending: {linkedin_url}")
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
            self.logger.debug(f"Checking for responses since: {since_str}")
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
            
            self.logger.debug(f"Fetching chats from Unipile API...")
            chats_response = requests.get(chats_url, headers=self.headers, params=chats_params, timeout=30)
            
            if chats_response.status_code == 503:
                self.logger.warning("Unipile API temporarily unavailable (503) when fetching chats. Will retry on next check.")
                return []
            
            chats_response.raise_for_status()
            chats = chats_response.json().get("items", [])
            self.logger.info(f"Found {len(chats)} chats in Unipile")
            
            # Step 2: Get messages for each chat and filter for new incoming messages
            all_responses = []
            total_messages_checked = 0
            
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
                    total_messages_checked += len(messages)
                    
                    # Filter for incoming messages (is_sender=0) that are newer than last check
                    incoming_count = 0
                    new_incoming_count = 0
                    for msg in messages:
                        if msg.get("is_sender") == 0:  # Incoming message
                            incoming_count += 1
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
                                        new_incoming_count += 1
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
                    
                    if incoming_count > 0:
                        self.logger.debug(f"Chat {chat_id}: {incoming_count} incoming messages, {new_incoming_count} new since {since_dt}")
                
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
            
            self.logger.info(
                f"Response check completed: {len(chats)} chats checked, "
                f"{total_messages_checked} messages checked, "
                f"{len(all_responses)} new incoming responses found"
            )
            
            return all_responses
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code != 503:
                self.logger.error(f"HTTP error checking Unipile responses: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error checking Unipile responses: {e}")
            return []


