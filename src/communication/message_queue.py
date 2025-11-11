"""
File-based message queue for inter-agent communication.
"""

import json
import uuid
import sqlite3
from pathlib import Path
from typing import Dict, List, Callable, Optional
from datetime import datetime
from src.utils.logger import setup_logger

class MessageQueue:
    """File-based message queue with SQLite index."""
    
    def __init__(self, config: Dict):
        """
        Initialize MessageQueue.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = setup_logger("MessageQueue")
        
        storage = config.get("storage", {})
        self.queue_dir = Path(storage.get("queue_directory", "data/queue"))
        self.sqlite_db = storage.get("sqlite_db", "data/state/agents.db")
        
        # Create queue directories
        (self.queue_dir / "pending").mkdir(parents=True, exist_ok=True)
        (self.queue_dir / "processed").mkdir(parents=True, exist_ok=True)
        (self.queue_dir / "failed").mkdir(parents=True, exist_ok=True)
    
    def publish(self, event: Dict) -> None:
        """
        Publish an event to the queue.
        
        Args:
            event: Event dictionary with 'type', 'agent_from', 'agent_to', 'data'
        """
        event_id = str(uuid.uuid4())
        event["event_id"] = event_id
        event["created_at"] = datetime.now().isoformat()
        
        # Save to file
        file_path = self._save_event_to_file(event)
        
        # Index in SQLite
        conn = sqlite3.connect(str(self.sqlite_db))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO message_queue_index 
            (event_id, event_type, agent_from, agent_to, status, file_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            event.get("type"),
            event.get("agent_from"),
            event.get("agent_to"),
            "pending",
            str(file_path),
            event["created_at"]
        ))
        
        conn.commit()
        conn.close()
        
        self.logger.debug(f"Published event: {event.get('type')} from {event.get('agent_from')}")
    
    def subscribe(self, event_types: List[str], callback: Callable, agent_name: str) -> None:
        """
        Subscribe to event types (for future use with polling).
        
        Args:
            event_types: List of event types to subscribe to
            callback: Callback function
            agent_name: Agent name
        """
        # Store subscription info (for future async implementation)
        # For now, agents will poll using process_messages
        pass
    
    def process_messages(self, agent_name: str) -> List[Dict]:
        """
        Process pending messages for an agent.
        
        Args:
            agent_name: Agent name
        
        Returns:
            List of event dictionaries
        """
        conn = sqlite3.connect(str(self.sqlite_db))
        cursor = conn.cursor()
        
        # Get pending events for this agent
        cursor.execute("""
            SELECT event_id, file_path FROM message_queue_index
            WHERE agent_to = ? AND status = 'pending'
            ORDER BY created_at ASC
        """, (agent_name,))
        
        events = []
        for event_id, file_path in cursor.fetchall():
            try:
                event = self._load_event_from_file(Path(file_path))
                events.append(event)
                
                # Mark as processed
                cursor.execute("""
                    UPDATE message_queue_index
                    SET status = 'processed'
                    WHERE event_id = ?
                """, (event_id,))
                
                # Move file to processed
                processed_path = self.queue_dir / "processed" / f"{event_id}.json"
                Path(file_path).rename(processed_path)
                
            except Exception as e:
                self.logger.error(f"Error processing event {event_id}: {e}")
                # Mark as failed
                cursor.execute("""
                    UPDATE message_queue_index
                    SET status = 'failed'
                    WHERE event_id = ?
                """, (event_id,))
                
                # Move file to failed
                failed_path = self.queue_dir / "failed" / f"{event_id}.json"
                try:
                    Path(file_path).rename(failed_path)
                except:
                    pass
        
        conn.commit()
        conn.close()
        
        return events
    
    def _save_event_to_file(self, event: Dict) -> Path:
        """
        Save event to JSON file.
        
        Args:
            event: Event dictionary
        
        Returns:
            Path to saved file
        """
        event_id = event.get("event_id", str(uuid.uuid4()))
        file_path = self.queue_dir / "pending" / f"{event_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(event, f, indent=2)
        
        return file_path
    
    def _load_event_from_file(self, file_path: Path) -> Dict:
        """
        Load event from JSON file.
        
        Args:
            file_path: Path to event file
        
        Returns:
            Event dictionary
        """
        with open(file_path, 'r') as f:
            return json.load(f)

