"""
Data validation utilities for InG AI Sales Department.
"""

import re
from typing import Optional
from urllib.parse import urlparse

def validate_linkedin_url(url: str) -> bool:
    """
    Validate LinkedIn profile URL format.
    
    Args:
        url: LinkedIn URL to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    # LinkedIn URL patterns
    patterns = [
        r'^https?://(www\.)?linkedin\.com/in/[\w-]+/?$',
        r'^https?://(www\.)?linkedin\.com/pub/[\w/-]+/?$',
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    
    return False

def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_contact_status(status: str) -> bool:
    """
    Validate contact status value.
    
    Args:
        status: Contact status to validate
    
    Returns:
        True if valid, False otherwise
    """
    valid_statuses = [
        "Not Contacted",
        "Allocated",
        "Message Sent",
        "Responded",
        "Closed"
    ]
    return status in valid_statuses

def validate_classification(classification: Optional[str]) -> bool:
    """
    Validate classification value.
    
    Args:
        classification: Classification to validate
    
    Returns:
        True if valid (including None), False otherwise
    """
    if classification is None:
        return True
    
    valid_classifications = ["Speaker", "Sponsor", "Other"]
    return classification in valid_classifications

def validate_sentiment(sentiment: Optional[str]) -> bool:
    """
    Validate sentiment value.
    
    Args:
        sentiment: Sentiment to validate
    
    Returns:
        True if valid (including None), False otherwise
    """
    if sentiment is None:
        return True
    
    valid_sentiments = ["positive", "negative", "neutral"]
    return sentiment in valid_sentiments

def validate_intent(intent: Optional[str]) -> bool:
    """
    Validate intent value.
    
    Args:
        intent: Intent to validate
    
    Returns:
        True if valid (including None), False otherwise
    """
    if intent is None:
        return True
    
    valid_intents = ["interested", "not_interested", "requesting_info"]
    return intent in valid_intents

def normalize_position(position: str) -> str:
    """
    Normalize position/title string.
    
    Args:
        position: Position string to normalize
    
    Returns:
        Normalized position string
    """
    if not position:
        return ""
    
    # Remove extra whitespace
    normalized = " ".join(position.split())
    
    # Convert to title case
    normalized = normalized.title()
    
    return normalized

