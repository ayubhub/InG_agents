"""
Response analysis module for sentiment and intent detection.
"""

import json
from src.core.models import ResponseAnalysis
from src.utils.logger import setup_logger

class ResponseAnalyser:
    """Analyses lead responses for sentiment and intent."""
    
    def __init__(self, llm_client=None):
        """
        Initialize response analyser.
        
        Args:
            llm_client: Optional LLM client for analysis
        """
        self.llm_client = llm_client
        self.logger = setup_logger("ResponseAnalyser")
    
    def analyse(self, response_text: str, original_message: Optional[str] = None) -> ResponseAnalysis:
        """
        Analyse response for sentiment and intent.
        
        Args:
            response_text: Response text from lead
            original_message: Optional original message sent
        
        Returns:
            ResponseAnalysis object
        """
        if self.llm_client:
            return self._analyse_with_llm(response_text, original_message)
        else:
            return self._analyse_rule_based(response_text)
    
    def _analyse_with_llm(self, response_text: str, original_message: Optional[str] = None) -> ResponseAnalysis:
        """
        Analyse using LLM.
        
        Args:
            response_text: Response text
            original_message: Optional original message
        
        Returns:
            ResponseAnalysis
        """
        system_prompt = """You are analyzing a LinkedIn message response to determine sentiment and intent.

Sentiment options: "positive", "negative", "neutral"
Intent options: "interested", "not_interested", "requesting_info"

Respond in JSON format:
{
  "sentiment": "positive|negative|neutral",
  "intent": "interested|not_interested|requesting_info",
  "key_info": "brief summary of key information",
  "confidence": 0.0-1.0
}

Be aware: 10% error rate is acceptable. When uncertain, choose neutral sentiment."""
        
        user_prompt = f"""Analyze this response from a lead:

Original message sent: {original_message or 'N/A'}
Lead's response: {response_text}

Analysis:"""
        
        try:
            response = self.llm_client.generate(user_prompt, system_prompt, temperature=0.3, max_tokens=200)
            
            # Try to parse JSON response
            try:
                analysis_data = json.loads(response)
            except:
                # If not JSON, try to extract from text
                analysis_data = self._parse_text_response(response)
            
            return ResponseAnalysis(
                sentiment=analysis_data.get("sentiment", "neutral"),
                intent=analysis_data.get("intent", "requesting_info"),
                key_info=analysis_data.get("key_info", ""),
                confidence=float(analysis_data.get("confidence", 0.7))
            )
        except Exception as e:
            self.logger.warning(f"LLM analysis failed: {e}, using rule-based")
            return self._analyse_rule_based(response_text)
    
    def _analyse_rule_based(self, response_text: str) -> ResponseAnalysis:
        """
        Analyse using rule-based logic.
        
        Args:
            response_text: Response text
        
        Returns:
            ResponseAnalysis
        """
        text_lower = response_text.lower()
        
        # Sentiment keywords
        positive_keywords = ["interested", "yes", "sure", "great", "sounds good", "let's", "would love"]
        negative_keywords = ["no", "not interested", "not now", "busy", "sorry"]
        
        positive_count = sum(1 for kw in positive_keywords if kw in text_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Intent keywords
        interested_keywords = ["interested", "yes", "tell me more", "details", "when"]
        not_interested_keywords = ["no", "not interested", "not now"]
        
        if any(kw in text_lower for kw in interested_keywords):
            intent = "interested"
        elif any(kw in text_lower for kw in not_interested_keywords):
            intent = "not_interested"
        else:
            intent = "requesting_info"
        
        return ResponseAnalysis(
            sentiment=sentiment,
            intent=intent,
            key_info=response_text[:100],  # First 100 chars
            confidence=0.6  # Lower confidence for rule-based
        )
    
    def _parse_text_response(self, text: str) -> Dict:
        """Parse text response to extract analysis data."""
        text_lower = text.lower()
        
        # Try to extract JSON-like structure
        sentiment = "neutral"
        intent = "requesting_info"
        
        if '"sentiment"' in text_lower or "sentiment" in text_lower:
            if "positive" in text_lower:
                sentiment = "positive"
            elif "negative" in text_lower:
                sentiment = "negative"
        
        if '"intent"' in text_lower or "intent" in text_lower:
            if "interested" in text_lower:
                intent = "interested"
            elif "not_interested" in text_lower or "not interested" in text_lower:
                intent = "not_interested"
        
        return {
            "sentiment": sentiment,
            "intent": intent,
            "key_info": text[:100],
            "confidence": 0.5
        }

