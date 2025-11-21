"""
Base agent class for all AI agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Optional
from src.communication.message_queue import MessageQueue
from src.communication.state_manager import StateManager
from src.integrations.llm_client import LLMClient
from src.utils.logger import setup_logger

class BaseAgent(ABC):
    """Base class for all AI agents."""
    
    def __init__(
        self,
        agent_name: str,
        config: Dict,
        state_manager: StateManager,
        message_queue: MessageQueue,
        llm_client: LLMClient
    ):
        """
        Initialize base agent.
        
        Args:
            agent_name: Agent name
            config: Configuration dictionary
            state_manager: State manager instance
            message_queue: Message queue instance
            llm_client: LLM client instance
        """
        self.agent_name = agent_name
        self.config = config
        self.state_manager = state_manager
        self.message_queue = message_queue
        self.llm_client = llm_client
        self.logger = setup_logger(agent_name)
        self.running = False
    
    def start(self) -> None:
        """Start the agent."""
        self.running = True
        self.logger.info(f"{self.agent_name} started")
    
    def stop(self) -> None:
        """Stop the agent."""
        self.running = False
        self.logger.info(f"{self.agent_name} stopped")
    
    def process_message(self, message: Dict) -> None:
        """
        Process a message from the queue.
        
        Args:
            message: Message dictionary
        """
        self.logger.debug(f"Processing message: {message.get('type')}")
        # Override in subclasses for specific message handling
    
    def health_check(self) -> Dict:
        """
        Perform health check.
        
        Returns:
            Health status dictionary
        """
        return {
            "agent": self.agent_name,
            "running": self.running,
            "status": "healthy" if self.running else "stopped"
        }
    
    def publish_event(self, event_type: str, data: Dict) -> None:
        """
        Publish an event (deprecated, now no-op for backward compatibility).
        Events are no longer used - agents coordinate through Google Sheets.
        
        Args:
            event_type: Event type
            data: Event data
        """
        # Just log, don't create files
        self.logger.debug(f"Event (deprecated): {event_type}")
    
    def subscribe_to_events(self, event_types: List[str], callback: Callable) -> None:
        """
        Subscribe to event types.
        
        Args:
            event_types: List of event types
            callback: Callback function
        """
        # For now, agents poll using process_messages
        # Future: async event handling
        pass
    
    @abstractmethod
    def run(self) -> None:
        """
        Main agent loop (blocking).
        Must be implemented by subclasses.
        """
        pass

