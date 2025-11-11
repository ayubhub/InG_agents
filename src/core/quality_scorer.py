"""
Quality scoring module for leads (1-10 scale).
"""

from src.core.models import Lead
from src.utils.logger import setup_logger

class QualityScorer:
    """Calculates quality scores for leads."""
    
    def __init__(self):
        """Initialize quality scorer."""
        self.logger = setup_logger("QualityScorer")
    
    def calculate_score(self, lead: Lead) -> float:
        """
        Calculate quality score (1-10 scale).
        
        Factors:
        - Position match: 0-4 (exact match = 4, partial = 2-3)
        - Company relevance: 0-3 (based on company size/type)
        - Profile completeness: 0-3 (based on available data)
        
        Args:
            lead: Lead to score
        
        Returns:
            Quality score (1.0-10.0)
        """
        position_score = self._calculate_position_match(lead.position)
        company_score = self._calculate_company_relevance(lead.company)
        completeness_score = self._calculate_completeness(lead)
        
        total = position_score + company_score + completeness_score
        return min(10.0, max(1.0, total))
    
    def _calculate_position_match(self, position: str) -> float:
        """
        Calculate position match score (0-4).
        
        Args:
            position: Position string
        
        Returns:
            Score 0-4
        """
        if not position:
            return 0.0
        
        position_upper = position.upper()
        
        # High-value positions (4 points)
        high_value = ["CTO", "CEO", "FOUNDER", "VP", "DIRECTOR"]
        if any(keyword in position_upper for keyword in high_value):
            return 4.0
        
        # Medium-value positions (2-3 points)
        medium_value = ["HEAD", "LEAD", "MANAGER", "ENGINEER"]
        if any(keyword in position_upper for keyword in medium_value):
            return 2.5
        
        # Low-value or unclear (1 point)
        return 1.0
    
    def _calculate_company_relevance(self, company: str) -> float:
        """
        Calculate company relevance score (0-3).
        
        Args:
            company: Company name
        
        Returns:
            Score 0-3
        """
        if not company:
            return 0.0
        
        company_upper = company.upper()
        
        # Tech-related keywords (higher score)
        tech_keywords = ["TECH", "SOFTWARE", "SYSTEMS", "SOLUTIONS", "DIGITAL", "DATA"]
        if any(keyword in company_upper for keyword in tech_keywords):
            return 3.0
        
        # General business (medium score)
        return 2.0
    
    def _calculate_completeness(self, lead: Lead) -> float:
        """
        Calculate profile completeness score (0-3).
        
        Args:
            lead: Lead object
        
        Returns:
            Score 0-3
        """
        score = 0.0
        
        # Name (0.5)
        if lead.name:
            score += 0.5
        
        # Position (0.5)
        if lead.position:
            score += 0.5
        
        # Company (0.5)
        if lead.company:
            score += 0.5
        
        # LinkedIn URL (1.0)
        if lead.linkedin_url:
            score += 1.0
        
        # Additional data (0.5)
        if lead.notes:
            score += 0.5
        
        return min(3.0, score)

