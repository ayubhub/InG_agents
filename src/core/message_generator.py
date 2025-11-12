"""
Message generation module for personalized LinkedIn messages.
"""

import os
from typing import Optional
from src.core.models import Lead
from src.utils.logger import setup_logger

class MessageGenerator:
    """Generates personalized LinkedIn messages."""
    
    def __init__(self, llm_client=None):
        """
        Initialize message generator.
        
        Args:
            llm_client: Optional LLM client for generation
        """
        self.llm_client = llm_client
        self.logger = setup_logger("MessageGenerator")
        
        # Get event info from config/env
        self.event_date = os.getenv("EVENT_DATE", "2025-11-20")
        self.event_name = os.getenv("EVENT_NAME", "Innovators Guild")
        
        # Base templates (Innovators Guild templates)
        self.speaker_template = """Hi [Name],

We're hosting an Innovators Guild event on [Date] - a curated gathering of the most ambitious engineers, founders, and innovators building the future.

Your work at [Company] leading [specific area] is exactly the kind of perspective our community needs to hear. I think you'd be a perfect fit.

Interested in speaking?

Best,

Ayub

Innovators Guild

https://innovators.london"""
        
        self.sponsor_template = """Hi [Name],

I've been following [Company]'s work in [one thing they're known for] - really impressed!

We run Innovators Guild events that bring together ambitious leaders and emerging companies. I think your team would find real value in being part of it.

Would you be open to a quick chat about sponsoring or collaborating on an event?

Best,

Ayub

Innovators Guild

https://innovators.london"""
    
    def generate(self, lead: Lead) -> str:
        """
        Generate personalized message for lead.
        
        Args:
            lead: Lead object
        
        Returns:
            Message text (Innovators Guild template with signature)
        """
        if self.llm_client:
            return self._generate_with_llm(lead)
        else:
            return self._generate_from_template(lead)
    
    def _generate_from_template(self, lead: Lead) -> str:
        """
        Generate message from template.
        
        Args:
            lead: Lead object
        
        Returns:
            Message text
        """
        # Select template based on classification
        if lead.classification == "Speaker":
            template = self.speaker_template
        elif lead.classification == "Sponsor":
            template = self.sponsor_template
        else:
            # Default to speaker template
            template = self.speaker_template
        
        # Replace variables
        first_name = lead.name.split()[0] if lead.name else "there"
        company = lead.company or "your company"
        position = lead.position or "your role"
        event_date = self.event_date
        
        # For Speaker: [specific area] - use position or company focus
        specific_area = position if position else "innovation"
        
        # For Sponsor: [one thing they're known for] - use company or position
        known_for = company if company else "innovation"
        
        message = template.replace("[Name]", first_name)
        message = message.replace("[Company]", company)
        message = message.replace("[Position]", position)
        message = message.replace("[Date]", event_date)
        message = message.replace("[specific area]", specific_area)
        message = message.replace("[one thing they're known for]", known_for)
        
        # Note: New templates are longer than 300 chars, but they include signature
        # LinkedIn allows longer messages, so we keep the full template
        # If needed, can truncate but keep signature
        
        return message
    
    def _generate_with_llm(self, lead: Lead) -> str:
        """
        Generate message using LLM.
        
        Args:
            lead: Lead object
        
        Returns:
            Message text
        """
        system_prompt = """You are a sales assistant writing personalised LinkedIn messages for Innovators Guild events. Messages must be:
- Personal and friendly
- Professional but conversational
- Match the lead's classification (Speaker or Sponsor)
- Include signature: "Best, Ayub\n\nInnovators Guild\n\nhttps://innovators.london"
- For Speakers: Mention their work at [Company] leading [specific area]
- For Sponsors: Mention following [Company]'s work in [one thing they're known for]

Template variables:
- [Name] - Lead's first name
- [Company] - Lead's company
- [Position] - Lead's position
- [Date] - Event date (from config)
- [specific area] - For Speakers: their area of expertise/position
- [one thing they're known for] - For Sponsors: what company is known for

Respond with ONLY the message text. No explanations."""
        
        user_prompt = f"""Generate a LinkedIn message for Innovators Guild event:
Name: {lead.name}
Position: {lead.position}
Company: {lead.company}
Classification: {lead.classification or 'Speaker'}
Event Date: {self.event_date}

Generate a personalized message following the Innovators Guild template style. Include the signature at the end."""
        
        try:
            response = self.llm_client.generate(user_prompt, system_prompt, temperature=0.7, max_tokens=200)
            message = response.strip()
            
            # LinkedIn allows longer messages, but keep reasonable length
            # Full template with signature is ~400-500 chars, which is acceptable
            if len(message) > 1000:
                self.logger.warning(f"Generated message too long ({len(message)} chars), truncating")
                message = message[:997] + "..."
            
            return message
        except Exception as e:
            self.logger.warning(f"LLM message generation failed: {e}, using template")
            return self._generate_from_template(lead)

