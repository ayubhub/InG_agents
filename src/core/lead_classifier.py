"""
Lead classification module (Speaker/Sponsor/Other).
"""

from typing import Optional
from src.core.models import Lead
from src.utils.logger import setup_logger

class LeadClassifier:
    """Classifies leads as Speaker, Sponsor, or Other."""
    
    def __init__(self, llm_client=None):
        """
        Initialize classifier.
        
        Args:
            llm_client: Optional LLM client for edge cases
        """
        self.llm_client = llm_client
        self.logger = setup_logger("LeadClassifier")
        
        # Speaker keywords
        self.speaker_keywords = [
            "CTO", "Chief Technology Officer",
            "Founder", "Co-Founder",
            "Engineer", "Engineering",
            "Technical Lead", "Tech Lead",
            "VP Engineering", "VP of Engineering",
            "Head of Engineering",
            "Software Architect",
            "Technical Director"
        ]
        
        # Sponsor keywords
        self.sponsor_keywords = [
            "CEO", "Chief Executive Officer",
            "CFO", "Chief Financial Officer",
            "CMO", "Chief Marketing Officer",
            "VP", "Vice President",
            "Director", "Managing Director",
            "Head of Business",
            "Business Development",
            "Sales Director",
            "Marketing Director"
        ]
    
    def classify(self, lead: Lead) -> str:
        """
        Classify lead using rule-based logic with LLM fallback for edge cases.
        
        Args:
            lead: Lead to classify
        
        Returns:
            Classification: "Speaker", "Sponsor", or "Other"
        """
        position = lead.position.upper()
        
        # Rule-based classification
        speaker_score = sum(1 for keyword in self.speaker_keywords if keyword.upper() in position)
        sponsor_score = sum(1 for keyword in self.sponsor_keywords if keyword.upper() in position)
        
        if speaker_score > 0 and speaker_score >= sponsor_score:
            return "Speaker"
        elif sponsor_score > 0:
            return "Sponsor"
        elif self.llm_client:
            # Use LLM for edge cases
            return self._classify_with_llm(lead)
        else:
            return "Other"
    
    def _classify_with_llm(self, lead: Lead) -> str:
        """
        Classify using LLM for edge cases.
        
        Args:
            lead: Lead to classify
        
        Returns:
            Classification
        """
        system_prompt = """You are a lead classification assistant for a tech event sales team. Your task is to classify leads as "Speaker" or "Sponsor" based on their position and company context.

Classification Rules:
- Speaker: Technical roles (CTO, Engineer, Founder, Technical Lead, VP Engineering)
- Sponsor: Business/executive roles (CEO, CFO, CMO, VP Business, Director, Head of Business Development)
- If position matches both categories, classify as "Speaker"

Respond with ONLY the classification: "Speaker", "Sponsor", or "Other". No explanation needed."""
        
        user_prompt = f"""Classify this lead:
Name: {lead.name}
Position: {lead.position}
Company: {lead.company}

Classification:"""
        
        try:
            response = self.llm_client.generate(user_prompt, system_prompt, temperature=0.3)
            classification = response.strip()
            
            if classification in ["Speaker", "Sponsor", "Other"]:
                return classification
            else:
                # Fallback to Other if response is unexpected
                return "Other"
        except Exception as e:
            self.logger.warning(f"LLM classification failed: {e}, using 'Other'")
            return "Other"

