"""
Rate limiter for LinkedIn message sending.
"""

import sqlite3
import random
from datetime import datetime, date, time
from typing import Optional, Dict
from pathlib import Path
from src.utils.logger import setup_logger

class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded."""
    pass

class RateLimiter:
    """Manages rate limiting for message sending."""

    def __init__(self, config: Dict, sqlite_db_path: str):
        """
        Initialize rate limiter.

        Args:
            config: Configuration dictionary
            sqlite_db_path: Path to SQLite database
        """
        self.config = config
        self.sqlite_db_path = sqlite_db_path
        self.logger = setup_logger("RateLimiter")

        outreach_config = config.get("outreach", {})
        self.daily_limit = outreach_config.get("rate_limit_daily", 45)
        self.interval_str = outreach_config.get("rate_limit_interval", "5-15 minutes")
        self.window_str = outreach_config.get("rate_limit_window", "09:00-17:00")

        # Parse interval (e.g., "5-15 minutes")
        self.min_interval, self.max_interval = self._parse_interval(self.interval_str)

        # Parse window (e.g., "09:00-17:00")
        self.window_start, self.window_end = self._parse_window(self.window_str)

        # Initialize database
        self._init_rate_limiter()

    def _parse_interval(self, interval_str: str) -> tuple:
        """Parse interval string to min/max seconds."""
        # Format: "5-15 minutes"
        parts = interval_str.replace("minutes", "").replace("minute", "").strip()
        if "-" in parts:
            min_val, max_val = parts.split("-")
            return int(min_val.strip()) * 60, int(max_val.strip()) * 60
        else:
            val = int(parts.strip()) * 60
            return val, val

    def _parse_window(self, window_str: str) -> tuple:
        """Parse time window string to time objects."""
        # Format: "09:00-17:00"
        start_str, end_str = window_str.split("-")
        start_hour, start_min = map(int, start_str.split(":"))
        end_hour, end_min = map(int, end_str.split(":"))
        return time(start_hour, start_min), time(end_hour, end_min)

    def _init_rate_limiter(self) -> None:
        """Initialize rate limiter in database."""
        conn = sqlite3.connect(str(self.sqlite_db_path))
        cursor = conn.cursor()

        # Check if record exists
        cursor.execute("SELECT COUNT(*) FROM rate_limiter")
        if cursor.fetchone()[0] == 0:
            # Create initial record
            cursor.execute("""
                INSERT INTO rate_limiter (daily_count, last_reset_date)
                VALUES (0, ?)
            """, (date.today().isoformat(),))

        conn.commit()
        conn.close()

    def can_send(self) -> bool:
        """
        Check if message can be sent (within rate limits).

        Returns:
            True if can send, False otherwise
        """
        # Check daily limit
        daily_count = self._get_daily_count()
        if daily_count >= self.daily_limit:
            self.logger.warning(f"Daily limit reached: {daily_count}/{self.daily_limit}")
            return False

        # Check time window
        current_time = datetime.now().time()
        # Handle time window (works for same-day windows like 09:00-23:59)
        in_window = self.window_start <= current_time <= self.window_end
        if not in_window:
            self.logger.warning(f"Outside time window: current={current_time}, window={self.window_start}-{self.window_end}")
            return False

        # Check minimum interval since last send
        last_send_time = self._get_last_send_time()
        if last_send_time:
            time_since_last = (datetime.now() - last_send_time).total_seconds()
            if time_since_last < self.min_interval:
                remaining = int(self.min_interval - time_since_last)
                self.logger.debug(f"Too soon since last send: {int(time_since_last)}s ago, need {self.min_interval}s (wait {remaining}s)")
                return False

        self.logger.debug(f"Rate limit OK: {daily_count}/{self.daily_limit}, time={current_time} in window {self.window_start}-{self.window_end}")
        return True

    def _get_last_send_time(self) -> Optional[datetime]:
        """Get last send time from database."""
        conn = sqlite3.connect(str(self.sqlite_db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT last_send_time FROM rate_limiter WHERE id = 1")
        result = cursor.fetchone()

        conn.close()

        if result and result[0]:
            try:
                return datetime.fromisoformat(result[0])
            except (ValueError, TypeError):
                return None
        return None

    def record_send(self) -> int:
        """
        Record a message send and return wait time until next send.

        Returns:
            Wait time in seconds until next send

        Raises:
            RateLimitExceededError: If rate limit exceeded
        """
        if not self.can_send():
            raise RateLimitExceededError("Rate limit exceeded")

        # Reset daily count if new day
        self._reset_if_new_day()

        # Update database
        conn = sqlite3.connect(str(self.sqlite_db_path))
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE rate_limiter
            SET daily_count = daily_count + 1,
                last_send_time = ?
            WHERE id = 1
        """, (datetime.now().isoformat(),))

        conn.commit()
        conn.close()

        # Calculate wait time
        wait_time = random.randint(self.min_interval, self.max_interval)

        return wait_time

    def _get_daily_count(self) -> int:
        """Get current daily count."""
        self._reset_if_new_day()

        conn = sqlite3.connect(str(self.sqlite_db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT daily_count FROM rate_limiter WHERE id = 1")
        result = cursor.fetchone()

        conn.close()

        return result[0] if result else 0

    def _reset_if_new_day(self) -> None:
        """Reset daily count if it's a new day."""
        conn = sqlite3.connect(str(self.sqlite_db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT last_reset_date FROM rate_limiter WHERE id = 1")
        result = cursor.fetchone()

        if result:
            last_reset = date.fromisoformat(result[0])
            if last_reset < date.today():
                # Reset for new day
                cursor.execute("""
                    UPDATE rate_limiter
                    SET daily_count = 0,
                        last_reset_date = ?
                    WHERE id = 1
                """, (date.today().isoformat(),))
                conn.commit()

        conn.close()
