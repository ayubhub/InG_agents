"""
State manager for InG AI Sales Department.
Manages Google Sheets (primary database) and SQLite (local state).
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.core.models import Lead
from src.integrations.google_sheets_io import GoogleSheetsIO
from src.utils.logger import setup_logger

class StateManager:
    """Manages shared state across agents."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize StateManager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = setup_logger("StateManager")
        
        # Initialize storage paths
        storage = config.get("storage", {})
        self.data_dir = Path(storage.get("data_directory", "data"))
        self.sqlite_db_path = storage.get("sqlite_db", "data/state/agents.db")
        
        # Create directories
        self._create_directories()
        
        # Initialize SQLite database
        self._init_database()
        
        # Initialize Google Sheets client
        self.google_sheets = GoogleSheetsIO(config)
    
    def _create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.data_dir / "state",
            self.data_dir / "queue" / "pending",
            self.data_dir / "queue" / "processed",
            self.data_dir / "queue" / "failed",
            self.data_dir / "cache" / "knowledge",
            self.data_dir / "cache" / "agent_context",
            self.data_dir / "cache" / "llm_responses",
            self.data_dir / "events" / "sales_manager",
            self.data_dir / "events" / "lead_finder",
            self.data_dir / "events" / "outreach",
            self.data_dir / "logs",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self) -> None:
        """Initialize SQLite database with required tables."""
        db_path = Path(self.sqlite_db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create agent_state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_state (
                agent_name TEXT PRIMARY KEY,
                state_data TEXT,
                last_updated TIMESTAMP
            )
        """)
        
        # Create rate_limiter table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rate_limiter (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                daily_count INTEGER DEFAULT 0,
                last_send_time TIMESTAMP,
                last_reset_date DATE
            )
        """)
        
        # Create message_queue_index table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_queue_index (
                event_id TEXT PRIMARY KEY,
                event_type TEXT,
                agent_from TEXT,
                agent_to TEXT,
                status TEXT,
                file_path TEXT,
                created_at TIMESTAMP
            )
        """)
        
        # Create locks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locks (
                resource_id TEXT PRIMARY KEY,
                agent_name TEXT,
                acquired_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        
        # Create agent_context table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                context_type TEXT,
                context_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"SQLite database initialized: {db_path}")
    
    def read_leads(self, filters: Optional[Dict[str, Any]] = None) -> List[Lead]:
        """
        Read leads from Google Sheets.
        
        Args:
            filters: Optional filters (e.g., {"contact_status": "Not Contacted"})
        
        Returns:
            List of Lead objects
        """
        return self.google_sheets.read_leads(filters)
    
    def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update lead in Google Sheets.
        
        Args:
            lead_id: Lead ID
            updates: Dictionary of fields to update
        
        Returns:
            True if successful, False otherwise
        """
        return self.google_sheets.update_lead(lead_id, updates)
    
    def allocate_leads(self, lead_ids: List[str], agent: str) -> bool:
        """
        Allocate leads to an agent.
        
        Args:
            lead_ids: List of lead IDs to allocate
            agent: Agent name
        
        Returns:
            True if successful, False otherwise
        """
        updates = {
            "contact_status": "Allocated",
            "allocated_to": agent,
            "allocated_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        success = True
        for lead_id in lead_ids:
            if not self.update_lead(lead_id, updates):
                success = False
        
        return success
    
    def save_agent_context(self, agent_name: str, context: Dict[str, Any]) -> None:
        """
        Save agent context to SQLite and file cache.
        
        Args:
            agent_name: Agent name
            context: Context data dictionary
        """
        # Save to SQLite
        conn = sqlite3.connect(str(self.sqlite_db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO agent_context (agent_name, context_type, context_data)
            VALUES (?, ?, ?)
        """, (
            agent_name,
            context.get("type", "operational"),
            json.dumps(context)
        ))
        
        conn.commit()
        conn.close()
        
        # Save to file cache
        cache_file = self.data_dir / "cache" / "agent_context" / f"{agent_name}.json"
        with open(cache_file, 'w') as f:
            json.dump(context, f, indent=2)
    
    def get_agent_context(self, agent_name: str, context_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get agent context from cache.
        
        Args:
            agent_name: Agent name
            context_type: Optional context type filter
        
        Returns:
            Context dictionary
        """
        cache_file = self.data_dir / "cache" / "agent_context" / f"{agent_name}.json"
        
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        return {}
    
    def acquire_lock(self, resource_id: str, agent_name: str, timeout_seconds: int = 300) -> bool:
        """
        Acquire a lock on a resource.
        
        Args:
            resource_id: Resource identifier
            agent_name: Agent name acquiring the lock
            timeout_seconds: Lock timeout in seconds
        
        Returns:
            True if lock acquired, False otherwise
        """
        conn = sqlite3.connect(str(self.sqlite_db_path))
        cursor = conn.cursor()
        
        # Check for existing lock
        cursor.execute("""
            SELECT agent_name, expires_at FROM locks
            WHERE resource_id = ?
        """, (resource_id,))
        
        result = cursor.fetchone()
        
        if result:
            existing_agent, expires_at_str = result
            expires_at = datetime.fromisoformat(expires_at_str)
            
            if datetime.now() < expires_at:
                # Lock still valid
                conn.close()
                return False
            
            # Lock expired, remove it
            cursor.execute("DELETE FROM locks WHERE resource_id = ?", (resource_id,))
        
        # Acquire new lock
        expires_at = datetime.now().timestamp() + timeout_seconds
        expires_at_dt = datetime.fromtimestamp(expires_at)
        
        cursor.execute("""
            INSERT INTO locks (resource_id, agent_name, acquired_at, expires_at)
            VALUES (?, ?, ?, ?)
        """, (
            resource_id,
            agent_name,
            datetime.now().isoformat(),
            expires_at_dt.isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return True
    
    def release_lock(self, resource_id: str) -> None:
        """
        Release a lock on a resource.
        
        Args:
            resource_id: Resource identifier
        """
        conn = sqlite3.connect(str(self.sqlite_db_path))
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM locks WHERE resource_id = ?", (resource_id,))
        
        conn.commit()
        conn.close()

