"""
LLM client for Google Gemini API integration.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from src.utils.logger import setup_logger

class LLMClient:
    """Client for Google Gemini LLM API."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM client.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = setup_logger("LLMClient")
        
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        
        # Get model from config
        llm_config = config.get("llm", {})
        model_name = llm_config.get("model", "gemini-pro")
        self.model = genai.GenerativeModel(model_name)
        
        # Cache settings
        self.cache_enabled = llm_config.get("cache_enabled", True)
        storage = config.get("storage", {})
        cache_dir = storage.get("cache_directory", "data/cache")
        self.cache_dir = Path(cache_dir) / "llm_responses"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Default parameters
        self.temperature = llm_config.get("temperature", 0.7)
        self.max_tokens = llm_config.get("max_tokens", 500)
        self.context_max_tokens = llm_config.get("context_max_tokens", 200000)
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True
    ) -> str:
        """
        Generate text using LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Temperature (overrides config)
            max_tokens: Max tokens (overrides config)
            use_cache: Whether to use cache
        
        Returns:
            Generated text
        """
        # Check cache
        if use_cache and self.cache_enabled:
            cached = self._get_cached_response(prompt, system_prompt)
            if cached:
                return cached
        
        # Build full prompt
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        try:
            # Generate response
            temp = temperature if temperature is not None else self.temperature
            max_toks = max_tokens if max_tokens is not None else self.max_tokens
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temp,
                    max_output_tokens=max_toks,
                )
            )
            result = self._extract_response_text(response)
            if not result:
                finish_info = self._build_finish_info(response)
                usage_info = getattr(response, "usage_metadata", None)
                self.logger.error(
                    "LLM returned empty content",
                    extra={
                        "finish_info": finish_info,
                        "usage": {
                            "prompt_tokens": getattr(usage_info, "prompt_token_count", None),
                            "candidates_tokens": getattr(usage_info, "candidates_token_count", None),
                            "total_tokens": getattr(usage_info, "total_token_count", None),
                        } if usage_info else None,
                    }
                )
                raise ValueError("LLM response did not contain any text parts")
            
            # Cache response
            if use_cache and self.cache_enabled:
                self._cache_response(prompt, system_prompt, result)
            
            return result
            
        except Exception as e:
            prompt_preview = full_prompt[:200] + ("..." if len(full_prompt) > 200 else "")
            self.logger.error(
                f"LLM API error: {e}",
                extra={
                    "prompt_preview": prompt_preview,
                    "system_prompt_provided": bool(system_prompt),
                    "temperature": temp,
                    "max_tokens": max_toks,
                }
            )
            raise
    
    def generate_with_context(
        self,
        prompt: str,
        context: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text with context injection.
        
        Args:
            prompt: User prompt
            context: Context dictionary
            system_prompt: Optional system prompt
        
        Returns:
            Generated text
        """
        # Convert context to text
        context_text = json.dumps(context, indent=2)
        
        # Estimate tokens (rough: 1 token ≈ 4 characters)
        estimated_tokens = len(context_text) // 4
        
        # Summarize if too large
        if estimated_tokens > self.context_max_tokens:
            context_text = self._summarize_context(context)
        
        # Build prompt with context
        full_prompt = f"Context: {context_text}\n\nPrompt: {prompt}"
        
        return self.generate(full_prompt, system_prompt)
    
    def _get_cached_response(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Get cached response if available."""
        cache_key = self._get_cache_key(prompt, system_prompt)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    return data.get("response")
            except Exception as e:
                self.logger.warning(f"Error reading cache: {e}")
        
        return None
    
    def _cache_response(self, prompt: str, system_prompt: Optional[str], response: str) -> None:
        """Cache response."""
        cache_key = self._get_cache_key(prompt, system_prompt)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    "prompt": prompt,
                    "system_prompt": system_prompt,
                    "response": response
                }, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Error caching response: {e}")
    
    def _get_cache_key(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate cache key from prompt."""
        text = f"{system_prompt or ''}{prompt}"
        return hashlib.md5(text.encode()).hexdigest()
    
    def _extract_response_text(self, response: Any) -> str:
        """Safely extract text from response candidates."""
        if not response:
            return ""
        
        texts: List[str] = []
        candidates = getattr(response, "candidates", []) or []
        for idx, candidate in enumerate(candidates):
            finish_reason = getattr(candidate, "finish_reason", None)
            if finish_reason and str(finish_reason).upper() not in {"STOP", "FINISH_REASON_STOP"}:
                self.logger.warning(
                    f"LLM candidate {idx} finished with reason {finish_reason}",
                    extra={"safety": getattr(candidate, "safety_ratings", None)}
                )
            
            content = getattr(candidate, "content", None)
            if not content:
                continue
            
            parts = getattr(content, "parts", []) or []
            for part in parts:
                text = getattr(part, "text", None)
                if text:
                    texts.append(text.strip())
        
        return "\n".join(filter(None, texts)).strip()
    
    def _build_finish_info(self, response: Any) -> str:
        """Collect finish reason diagnostics for logging."""
        info_segments = []
        
        candidates = getattr(response, "candidates", []) or []
        for idx, candidate in enumerate(candidates):
            finish_reason = getattr(candidate, "finish_reason", None)
            info_segments.append(f"candidate_{idx}:{finish_reason}")
        
        prompt_feedback = getattr(response, "prompt_feedback", None)
        if prompt_feedback:
            info_segments.append(f"prompt_feedback={prompt_feedback}")
        
        return "; ".join(info_segments) if info_segments else "no candidates"
    
    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """
        Summarize context if too large.
        Simple implementation - can be enhanced.
        
        Args:
            context: Context dictionary
        
        Returns:
            Summarized context text
        """
        # Simple summarization - keep only essential keys
        essential_keys = ["leads_processed", "messages_sent", "responses_received", "key_metrics"]
        summarized = {k: v for k, v in context.items() if k in essential_keys}
        
        return json.dumps(summarized, indent=2)

