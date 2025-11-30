"""
LLM client wrapper for generating text completions.

Supports OpenAI by default. Includes fallback for local development.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available. LLM will use fallback method.")


class LLMClient:
    """Wrapper for LLM API calls."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                openai.api_key = self.api_key
                self.client = openai
                logger.info(f"Initialized OpenAI LLM with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("OpenAI API key not found. Using fallback LLM method.")
    
    def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate text completion from a prompt.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            response_format: Optional response format specification
            
        Returns:
            Generated text response
        """
        if self.client and self.api_key:
            try:
                messages = [{"role": "user", "content": prompt}]
                params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                if response_format:
                    params["response_format"] = response_format
                
                response = self.client.chat.completions.create(**params)
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"OpenAI completion failed: {e}. Using fallback.")
                return self._fallback_complete(prompt)
        else:
            return self._fallback_complete(prompt)
    
    def complete_json(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Generate JSON response from a prompt.
        
        Args:
            prompt: Input prompt (should request JSON output)
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            Parsed JSON dictionary
        """
        # Check if API key is available
        if not self.api_key or not self.client:
            raise ValueError(
                "OpenAI API key is required. Please set OPENAI_API_KEY in your .env file."
            )
        
        try:
            response = self.complete(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response[:500]}")
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
        except ValueError:
            raise  # Re-raise ValueError (like missing API key)
        except Exception as e:
            logger.error(f"JSON completion failed: {e}")
            raise ValueError(f"Failed to generate response from OpenAI API: {str(e)}")
    
    def _fallback_complete(self, prompt: str) -> str:
        """
        Fallback completion for local development.
        Provides basic keyword-based responses.
        """
        logger.warning("Using fallback LLM (keyword matching). Install OpenAI for full functionality.")
        
        # Very basic keyword-based response
        prompt_lower = prompt.lower()
        
        if "question" in prompt_lower and "generate" in prompt_lower:
            # Interview question generation fallback
            return json.dumps([
                {"id": "q1", "question": "Tell me about your experience with the technologies mentioned in the job description.", "difficulty": "medium", "category": "technical"},
                {"id": "q2", "question": "Describe a challenging project you worked on and how you solved it.", "difficulty": "medium", "category": "problem-solving"},
                {"id": "q3", "question": "How do you stay updated with industry trends?", "difficulty": "easy", "category": "behavioral"},
                {"id": "q4", "question": "Explain a time when you had to learn a new technology quickly.", "difficulty": "medium", "category": "behavioral"},
                {"id": "q5", "question": "What is your approach to debugging complex issues?", "difficulty": "hard", "category": "technical"}
            ])
        
        elif "score" in prompt_lower and "answer" in prompt_lower:
            # Answer scoring fallback
            return json.dumps({
                "score": 70.0,
                "feedback": "The answer addresses the question. Consider providing more specific examples and technical details.",
                "tags": ["clarity", "needs_examples"]
            })
        
        elif "match" in prompt_lower and "job" in prompt_lower:
            # Job matching fallback
            return json.dumps({
                "score": 75.0,
                "rationale": "The candidate profile shows relevant experience and skills that align with the job requirements.",
                "matched_skills": ["Python", "Software Development", "Problem Solving"]
            })
        
        elif "summary" in prompt_lower and "interview" in prompt_lower:
            # Interview summary fallback
            return json.dumps({
                "avg_score": 72.5,
                "summary": "The candidate demonstrated good technical knowledge and communication skills. Areas for improvement include providing more concrete examples.",
                "strengths": ["Technical knowledge", "Communication", "Problem-solving approach"],
                "weaknesses": ["Needs more examples", "Could expand on system design", "More detail on past projects"]
            })
        
        else:
            return '{"result": "Fallback response - OpenAI API key required for full functionality"}'
    
    def _fallback_json(self, prompt: str) -> Dict[str, Any]:
        """Fallback JSON response."""
        response = self._fallback_complete(prompt)
        try:
            return json.loads(response)
        except:
            return {"error": "Failed to generate response"}


# Global instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create the global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def complete(prompt: str, **kwargs) -> str:
    """Convenience function for text completion."""
    client = get_llm_client()
    return client.complete(prompt, **kwargs)


def complete_json(prompt: str, **kwargs) -> Dict[str, Any]:
    """Convenience function for JSON completion."""
    client = get_llm_client()
    return client.complete_json(prompt, **kwargs)

