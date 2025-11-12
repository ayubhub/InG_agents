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
        self.event_name = os.getenv("EVENT_NAME", "Tech Event 2025")
        
        # Base templates
        self.speaker_template = "Hi [Name]! We're organising a tech event on [Date]. Given your experience at [Company] as [Position], we think you'd be perfect as a speaker. Interested in sharing your insights?"
        self.sponsor_template = "Hello [Name]! We're hosting a tech event on [Date] and looking for corporate sponsors. [Company] would be a great fit. Would you like to learn more about sponsorship opportunities?"
    
    def generate(self, lead: Lead) -> str:
        """
        Generate personalized message for lead.
        
        Args:
            lead: Lead object
        
        Returns:
            Message text (max 300 characters)
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
        message = template.replace("[Name]", lead.name.split()[0] if lead.name else "there")
        message = message.replace("[Company]", lead.company or "your company")
        message = message.replace("[Position]", lead.position or "your role")
        message = message.replace("[Date]", self.event_date)
        
        # Ensure max length
        if len(message) > 300:
            message = message[:297] + "..."
        
        return message
    
    def _generate_with_llm(self, lead: Lead) -> str:
        """
        Generate message using LLM.
        
        Args:
            lead: Lead object
        
        Returns:
            Message text
        """
        system_prompt = """You are a sales assistant writing personalised LinkedIn messages for a tech event. Messages must be:
- Personal and friendly
- Under 300 characters
- Include: [Name], [Company], [Position], [Date]
- Match the lead's classification (Speaker or Sponsor)
- Professional but conversational
- Use British English spelling and terminology (e.g., "organising" not "organizing", "colour" not "color")

Template variables:
- [Name] - Lead's name
- [Company] - Lead's company
- [Position] - Lead's position
- [Date] - Event date (from config)

Respond with ONLY the message text. No explanations."""
        
        user_prompt = f"""Generate a LinkedIn message for:
Name: {lead.name}
Position: {lead.position}
Company: {lead.company}
Classification: {lead.classification or 'Speaker'}
Event Date: {self.event_date}

Message (max 300 characters):"""
        
        try:
            response = self.llm_client.generate(user_prompt, system_prompt, temperature=0.7, max_tokens=100)
            message = response.strip()
            
            # Ensure max length
            if len(message) > 300:
                message = message[:297] + "..."
            
            return message
        except Exception as e:
            self.logger.warning(f"LLM message generation failed: {e}, using template")
            return self._generate_from_template(lead)

