"""
Multi-Account LinkedIn Sender with Automatic Failover
Manages multiple LinkedIn accounts and switches when limits are reached.
"""

import os
import json
import time
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta, timedelta
from dotenv import load_dotenv
from src.core.models import SendResult
from src.utils.logger import setup_logger
from src.integrations.linkedin_sender import LinkedInSender, LinkedInAPIError

class AccountLimitError(Exception):
    """Raised when an account reaches its sending limit."""
    pass

class MultiAccountLinkedInSender:
    """
    Multi-account LinkedIn sender with automatic failover.
    Manages multiple Unipile accounts and switches when limits are reached.
    """
    
    def __init__(self, config: Dict):
        """Initialize multi-account LinkedIn sender."""
        self.config = config
        self.logger = setup_logger("MultiAccountLinkedIn")
        
        # Set service attribute for compatibility
        self.service = "unipile"
        
        # Load account configurations
        self.accounts = self._load_accounts()
        self.current_account_index = 0
        self.account_stats = {}
        
        # Rate limiting settings
        self.daily_limit_per_account = int(os.getenv("LINKEDIN_DAILY_LIMIT", "50"))
        self.hourly_limit_per_account = int(os.getenv("LINKEDIN_HOURLY_LIMIT", "10"))
        
        # State file for tracking usage
        storage_config = config.get("storage", {})
        data_dir = storage_config.get("data_directory", "data")
        self.state_file = os.path.join(data_dir, "state", "multi_account_state.json")
        
        # Global cooldown for when all accounts hit the same API limit
        self.global_cooldown_until = None
        
        # Load existing state
        self._load_state()
        
        # Ensure we start with Account_1 (index 0)
        self.current_account_index = 0
        self.logger.info(f"Initialized multi-account LinkedIn sender with {len(self.accounts)} accounts")
        self.logger.info(f"Starting with account index {self.current_account_index}: {self.accounts[self.current_account_index]['name']}")
        
        # Log all accounts
        for i, account in enumerate(self.accounts):
            self.logger.info(f"  Account {i}: {account['name']} - {account['account_id']}")
    
    def _load_accounts(self) -> List[Dict]:
        """Load all configured LinkedIn accounts."""
        # Force reload environment variables
        load_dotenv(override=True)
        
        accounts = []
        
        # Debug: Log environment variables
        self.logger.info(f"Loading accounts - Primary DSN: {os.getenv('UNIPILE_DSN')}")
        self.logger.info(f"Loading accounts - Primary Account ID: {os.getenv('UNIPILE_ACCOUNT_ID')}")
        self.logger.info(f"Loading accounts - Secondary DSN: {os.getenv('UNIPILE_DSN_2')}")
        self.logger.info(f"Loading accounts - Secondary Account ID: {os.getenv('UNIPILE_ACCOUNT_ID_2')}")
        
        # Load primary account
        # NOTE: These are fallback credentials. Update with actual account IDs from API
        primary_account = {
            "name": "Account_1",
            "dsn": "api22.unipile.com:15229",  # Current DSN
            "api_key": "pmrqNERD.I2FFFtqp3BGdkagj8cbKp3Z/f8hR7T48XG0+y1+cnuM=",  # Current API KEY
            "account_id": os.getenv("UNIPILE_ACCOUNT_ID") or ""  # Will be set from .env or API
        }
        
        # Try to load from environment first
        if os.getenv("UNIPILE_DSN") and os.getenv("UNIPILE_API_KEY") and os.getenv("UNIPILE_ACCOUNT_ID"):
            primary_account["dsn"] = os.getenv("UNIPILE_DSN")
            primary_account["api_key"] = os.getenv("UNIPILE_API_KEY")
            primary_account["account_id"] = os.getenv("UNIPILE_ACCOUNT_ID")
            self.logger.info("Using primary account from environment variables")
        else:
            self.logger.warning("Primary account not in environment - using fallback (update .env file)")
        
        if primary_account["account_id"]:
            accounts.append(primary_account)
            self.logger.info(f"Added primary account: {primary_account['account_id']}")
        else:
            self.logger.warning("Primary account ID missing - skipping Account_1")
        
        # Load secondary account
        secondary_account = {
            "name": "Account_2",
            "dsn": "api22.unipile.com:15229",  # Current DSN
            "api_key": "pmrqNERD.I2FFFtqp3BGdkagj8cbKp3Z/f8hR7T48XG0+y1+cnuM=",  # Current API KEY
            "account_id": os.getenv("UNIPILE_ACCOUNT_ID_2") or ""  # Will be set from .env or API
        }
        
        # Try to load from environment first
        if os.getenv("UNIPILE_DSN_2") and os.getenv("UNIPILE_API_KEY_2") and os.getenv("UNIPILE_ACCOUNT_ID_2"):
            secondary_account["dsn"] = os.getenv("UNIPILE_DSN_2")
            secondary_account["api_key"] = os.getenv("UNIPILE_API_KEY_2")
            secondary_account["account_id"] = os.getenv("UNIPILE_ACCOUNT_ID_2")
            self.logger.info("Using secondary account from environment variables")
        else:
            self.logger.warning("Secondary account not in environment - using fallback (update .env file)")
        
        self.logger.info(f"Checking Account_2: DSN={secondary_account['dsn']}, Account_ID={secondary_account['account_id']}")
        
        if secondary_account["account_id"]:
            accounts.append(secondary_account)
            self.logger.info(f"Added Account_2: {secondary_account['account_id']}")
        else:
            self.logger.warning("Account_2 ID missing - skipping Account_2")
        
        # Load additional secondary accounts from env vars
        account_num = 3
        while True:
            account = {
                "name": f"Account_{account_num}",
                "dsn": os.getenv(f"UNIPILE_DSN_{account_num}"),
                "api_key": os.getenv(f"UNIPILE_API_KEY_{account_num}"),
                "account_id": os.getenv(f"UNIPILE_ACCOUNT_ID_{account_num}")
            }
            
            self.logger.info(f"Checking Account_{account_num}: DSN={account['dsn']}, Account_ID={account['account_id']}")
            
            if all([account["dsn"], account["api_key"], account["account_id"]]):
                accounts.append(account)
                self.logger.info(f"Added Account_{account_num}: {account['account_id']}")
                account_num += 1
            else:
                self.logger.info(f"Account_{account_num} missing credentials - stopping")
                break
        
        if not accounts:
            raise ValueError("No LinkedIn accounts configured. Please set UNIPILE_DSN, UNIPILE_API_KEY, and UNIPILE_ACCOUNT_ID")
        
        return accounts
    
    def _load_state(self):
        """Load account usage state from file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    loaded_stats = data.get("account_stats", {})
                    self.current_account_index = data.get("current_account_index", 0)
                    self.global_cooldown_until = data.get("global_cooldown_until", None)
                    
                    # Only keep stats for accounts that are actually configured
                    configured_account_names = {acc["name"] for acc in self.accounts}
                    self.account_stats = {
                        name: stats for name, stats in loaded_stats.items()
                        if name in configured_account_names
                    }
                    
                    # Remove stats for accounts that are no longer configured
                    removed_accounts = set(loaded_stats.keys()) - configured_account_names
                    if removed_accounts:
                        self.logger.info(f"Removed stats for unconfigured accounts: {removed_accounts}")
                    
                    # Ensure current_account_index is valid
                    if self.current_account_index >= len(self.accounts):
                        self.current_account_index = 0
                        self.logger.info(f"Reset current_account_index to 0 (was out of range)")
                    
                    # Initialize stats for new accounts
                    for account in self.accounts:
                        if account["name"] not in self.account_stats:
                            self.account_stats[account["name"]] = {
                                "daily_sent": 0,
                                "hourly_sent": 0,
                                "last_reset_date": datetime.now().date().isoformat(),
                                "last_reset_hour": datetime.now().hour,
                                "total_sent": 0,
                                "error_count": 0,
                                "last_used": None,
                                "cooldown_until": None
                            }
                            self.logger.info(f"Initialized stats for {account['name']}")
        except Exception as e:
            self.logger.warning(f"Error loading account state: {e}")
            self.account_stats = {}
            self.global_cooldown_until = None
    
    def _save_state(self):
        """Save account usage state to file."""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            data = {
                "account_stats": self.account_stats,
                "current_account_index": self.current_account_index,
                "global_cooldown_until": self.global_cooldown_until,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Error saving account state: {e}")
    
    def _get_account_stats(self, account_name: str) -> Dict:
        """Get usage stats for an account."""
        if account_name not in self.account_stats:
            self.account_stats[account_name] = {
                "daily_sent": 0,
                "hourly_sent": 0,
                "last_reset_date": datetime.now().date().isoformat(),
                "last_reset_hour": datetime.now().hour,
                "total_sent": 0,
                "last_error": None,
                "error_count": 0,
                "last_used": None,
                "cooldown_until": None  # Add cooldown timestamp
            }
        return self.account_stats[account_name]
    
    def _reset_counters_if_needed(self, account_name: str):
        """Reset daily/hourly counters if time period has passed."""
        stats = self._get_account_stats(account_name)
        now = datetime.now()
        
        # Reset daily counter
        if stats["last_reset_date"] != now.date().isoformat():
            stats["daily_sent"] = 0
            stats["error_count"] = 0  # Reset error count daily
            stats["last_reset_date"] = now.date().isoformat()
            self.logger.info(f"Reset daily counter and error count for {account_name}")
        
        # Also reset error count every hour to prevent permanent blocking
        if stats["last_reset_hour"] != now.hour:
            stats["error_count"] = max(0, stats["error_count"] - 5)  # Reduce error count hourly
            if stats["error_count"] == 0:
                self.logger.info(f"Reset error count for {account_name} (hourly reset)")
        
        # Reset hourly counter
        if stats["last_reset_hour"] != now.hour:
            stats["hourly_sent"] = 0
            stats["last_reset_hour"] = now.hour
            self.logger.debug(f"Reset hourly counter for {account_name}")
    
    def _is_account_available(self, account_name: str) -> Tuple[bool, str]:
        """Check if account is available for sending."""
        stats = self._get_account_stats(account_name)
        self._reset_counters_if_needed(account_name)
        
        now = datetime.now()
        
        # Check cooldown period first (most important)
        if stats.get("cooldown_until"):
            try:
                cooldown_until = datetime.fromisoformat(stats["cooldown_until"])
                if now < cooldown_until:
                    remaining = int((cooldown_until - now).total_seconds() / 60)
                    return False, f"In cooldown for {remaining} more minutes"
                else:
                    # Cooldown expired, clear it and reset error count
                    stats["cooldown_until"] = None
                    stats["error_count"] = 0
                    self.logger.info(f"Cooldown expired for {account_name}, account available again")
            except (ValueError, TypeError):
                # Invalid cooldown timestamp, clear it
                stats["cooldown_until"] = None
        
        self.logger.info(f"Checking availability for {account_name}: daily_sent={stats['daily_sent']}, hourly_sent={stats['hourly_sent']}, error_count={stats['error_count']}")
        
        # Check daily limit
        if stats["daily_sent"] >= self.daily_limit_per_account:
            return False, f"Daily limit reached ({stats['daily_sent']}/{self.daily_limit_per_account})"
        
        # Check hourly limit
        if stats["hourly_sent"] >= self.hourly_limit_per_account:
            return False, f"Hourly limit reached ({stats['hourly_sent']}/{self.hourly_limit_per_account})"
        
        return True, f"Available (daily: {stats['daily_sent']}/{self.daily_limit_per_account}, hourly: {stats['hourly_sent']}/{self.hourly_limit_per_account}, errors: {stats['error_count']})"
    
    def _get_linkedin_sender(self, account: Dict) -> LinkedInSender:
        """Create LinkedInSender instance for specific account."""
        # Temporarily override environment variables
        original_dsn = os.environ.get("UNIPILE_DSN")
        original_api_key = os.environ.get("UNIPILE_API_KEY")
        original_account_id = os.environ.get("UNIPILE_ACCOUNT_ID")
        
        try:
            os.environ["UNIPILE_DSN"] = account["dsn"]
            os.environ["UNIPILE_API_KEY"] = account["api_key"]
            os.environ["UNIPILE_ACCOUNT_ID"] = account["account_id"]
            os.environ["LINKEDIN_SERVICE"] = "unipile"
            
            return LinkedInSender(self.config)
        finally:
            # Restore original environment variables
            if original_dsn:
                os.environ["UNIPILE_DSN"] = original_dsn
            if original_api_key:
                os.environ["UNIPILE_API_KEY"] = original_api_key
            if original_account_id:
                os.environ["UNIPILE_ACCOUNT_ID"] = original_account_id
    
    def _find_available_account(self) -> Optional[Tuple[int, Dict]]:
        """Find the next available account for sending."""
        self.logger.info(f"Finding available account. Current index: {self.current_account_index}")
        
        # Check global cooldown first
        if self.global_cooldown_until:
            try:
                cooldown_until = datetime.fromisoformat(self.global_cooldown_until)
                if datetime.now() < cooldown_until:
                    remaining = int((cooldown_until - datetime.now()).total_seconds() / 60)
                    self.logger.info(f"Global cooldown active for {remaining} more minutes")
                    return None
                else:
                    # Global cooldown expired
                    self.global_cooldown_until = None
                    self.logger.info("Global cooldown expired")
            except (ValueError, TypeError):
                self.global_cooldown_until = None
        
        # Try current account first
        current_account = self.accounts[self.current_account_index]
        self.logger.info(f"Checking current account: {current_account['name']} ({current_account['account_id']})")
        available, reason = self._is_account_available(current_account["name"])
        
        if available:
            self.logger.info(f"Using current account: {current_account['name']}")
            return self.current_account_index, current_account
        
        self.logger.info(f"Current account {current_account['name']} not available: {reason}")
        
        # Try other accounts
        for i, account in enumerate(self.accounts):
            if i == self.current_account_index:
                continue  # Already checked
            
            self.logger.info(f"Checking alternative account {i}: {account['name']} ({account['account_id']})")
            available, reason = self._is_account_available(account["name"])
            if available:
                self.logger.info(f"Switching to {account['name']} (index {i})")
                self.current_account_index = i
                self._save_state()
                return i, account
            else:
                self.logger.info(f"Account {account['name']} not available: {reason}")
        
        self.logger.error("No available accounts found!")
        return None
    
    def send_message(self, linkedin_url: str, message: str) -> SendResult:
        """
        Send LinkedIn message using available account with automatic failover.
        
        Args:
            linkedin_url: LinkedIn profile URL
            message: Message text
        
        Returns:
            SendResult object
        """
        # Find available account
        account_info = self._find_available_account()
        if not account_info:
            error_msg = "All LinkedIn accounts have reached their limits or are unavailable"
            self.logger.error(error_msg)
            return SendResult(
                success=False,
                error_message=error_msg,
                timestamp=datetime.now(),
                service_used="multi_account_unipile",
                status="all_accounts_limited"
            )
        
        account_index, account = account_info
        account_name = account["name"]
        
        try:
            # Create sender for this account
            sender = self._get_linkedin_sender(account)
            
            # Attempt to send message
            self.logger.info(f"Sending message via {account_name} to {linkedin_url}")
            result = sender.send_message(linkedin_url, message)
            
            # Update stats
            stats = self._get_account_stats(account_name)
            
            if result.success or result.status in ['invitation_sent', 'invitation_already_sent']:
                # Count as successful send
                stats["daily_sent"] += 1
                stats["hourly_sent"] += 1
                stats["total_sent"] += 1
                stats["last_used"] = datetime.now().isoformat()
                stats["error_count"] = 0  # Reset error count on success
                
                # Update result to show which account was used
                result.service_used = f"unipile_{account_name.lower()}"
                
                self.logger.info(f"Message sent via {account_name} - Daily: {stats['daily_sent']}/{self.daily_limit_per_account}, Hourly: {stats['hourly_sent']}/{self.hourly_limit_per_account}")
            else:
                # Handle errors - only increment for actual rate limits
                stats["last_error"] = result.error_message
                
                # Check if this looks like a rate limit error
                if any(keyword in (result.error_message or "").lower() for keyword in ["limit", "rate", "quota", "too many", "temporary"]):
                    # Check if this is a "temporary provider limit" which affects all accounts
                    if "temporary provider limit" in (result.error_message or "").lower():
                        # Set global cooldown - affects all accounts
                        cooldown_minutes = 20  # 20 minute global cooldown
                        self.global_cooldown_until = (datetime.now() + timedelta(minutes=cooldown_minutes)).isoformat()
                        self.logger.warning(f"Temporary provider limit detected - setting {cooldown_minutes} minute GLOBAL cooldown for all accounts")
                    else:
                        # Set individual account cooldown
                        cooldown_minutes = 10  # 10 minute individual cooldown
                        cooldown_until = datetime.now() + timedelta(minutes=cooldown_minutes)
                        stats["cooldown_until"] = cooldown_until.isoformat()
                        self.logger.warning(f"Rate limit detected for {account_name}, setting {cooldown_minutes} minute cooldown until {cooldown_until.strftime('%H:%M')}")
                    
                    stats["error_count"] += 1  # Still track for logging
                else:
                    # For non-rate-limit errors, just increment error count
                    stats["error_count"] += 1
                    self.logger.warning(f"Non-rate-limit error for {account_name}: {result.error_message}")
            
            self._save_state()
            return result
            
        except Exception as e:
            # Handle unexpected errors - don't always count against account
            stats = self._get_account_stats(account_name)
            error_str = str(e).lower()
            
            # Only count network/API errors against the account
            if any(keyword in error_str for keyword in ["connection", "timeout", "network", "api", "unipile"]):
                stats["error_count"] += 1
                self.logger.warning(f"Network/API error for {account_name}: {e}")
            else:
                self.logger.error(f"System error (not counted against account) for {account_name}: {e}")
                
            stats["last_error"] = str(e)
            self._save_state()
            
            return SendResult(
                success=False,
                error_message=f"Error with {account_name}: {str(e)}",
                timestamp=datetime.now(),
                service_used=f"unipile_{account_name.lower()}"
            )
    
    def check_responses(self) -> List[Dict]:
        """Check for responses across all accounts."""
        all_responses = []
        
        for account in self.accounts:
            try:
                sender = self._get_linkedin_sender(account)
                responses = sender.check_responses()
                
                # Add account info to each response
                for response in responses:
                    response["account_used"] = account["name"]
                
                all_responses.extend(responses)
                
            except Exception as e:
                self.logger.warning(f"Error checking responses for {account['name']}: {e}")
        
        return all_responses
    
    def check_invitation_status(self, invite_id: str, linkedin_url: str) -> str:
        """Check invitation status across all accounts."""
        for account in self.accounts:
            try:
                sender = self._get_linkedin_sender(account)
                status = sender.check_invitation_status(invite_id, linkedin_url)
                
                if status != "pending":
                    return status
                    
            except Exception as e:
                self.logger.warning(f"Error checking invitation status for {account['name']}: {e}")
        
        return "pending"
    
    def get_account_status(self) -> Dict:
        """Get status of all accounts."""
        status = {
            "current_account": self.accounts[self.current_account_index]["name"],
            "total_accounts": len(self.accounts),
            "accounts": []
        }
        
        for account in self.accounts:
            stats = self._get_account_stats(account["name"])
            self._reset_counters_if_needed(account["name"])
            available, reason = self._is_account_available(account["name"])
            
            status["accounts"].append({
                "name": account["name"],
                "available": available,
                "reason": reason,
                "daily_sent": stats["daily_sent"],
                "daily_limit": self.daily_limit_per_account,
                "hourly_sent": stats["hourly_sent"],
                "hourly_limit": self.hourly_limit_per_account,
                "total_sent": stats["total_sent"],
                "error_count": stats["error_count"],
                "last_used": stats["last_used"]
            })
        
        return status
