"""
Data models for InG AI Sales Department.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Lead:
    """Lead data model."""
    id: str
    name: str
    position: str
    company: str
    linkedin_url: str
    classification: Optional[str] = None  # "Speaker", "Sponsor", "Other"
    quality_score: Optional[float] = None  # 1-10
    contact_status: str = "Not Contacted"  # "Not Contacted", "Allocated", "Message Sent", "Responded", "Closed"
    allocated_to: Optional[str] = None
    allocated_at: Optional[datetime] = None
    message_sent: Optional[str] = None
    message_sent_at: Optional[datetime] = None
    response: Optional[str] = None
    response_received_at: Optional[datetime] = None
    response_sentiment: Optional[str] = None  # "positive", "negative", "neutral"
    response_intent: Optional[str] = None  # "interested", "not_interested", "requesting_info"
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None
    quality_score_placeholder: bool = False

@dataclass
class SendResult:
    """Result of sending a LinkedIn message."""
    success: bool
    message_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    service_used: Optional[str] = None  # "dripify" or "gojiberry"

@dataclass
class ResponseAnalysis:
    """Analysis of a lead's response."""
    sentiment: str  # "positive", "negative", "neutral"
    intent: str  # "interested", "not_interested", "requesting_info"
    key_info: str
    confidence: float  # 0.0-1.0

