"""
Embedding provider wrapper for generating text embeddings.

Supports OpenAI embeddings by default. Can be extended for other providers.
"""

import os
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available. Embeddings will use fallback method.")


class EmbeddingProvider:
    """Wrapper for embedding generation."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                openai.api_key = self.api_key
                self.client = openai
                logger.info(f"Initialized OpenAI embeddings with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("OpenAI API key not found. Using fallback embedding method.")
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if self.client and self.api_key:
            try:
                # Use OpenAI embeddings
                response = self.client.embeddings.create(
                    model=self.model,
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"OpenAI embedding failed: {e}. Using fallback.")
                return self._fallback_embed(text)
        else:
            return self._fallback_embed(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if self.client and self.api_key:
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                logger.error(f"OpenAI batch embedding failed: {e}. Using fallback.")
                return [self._fallback_embed(text) for text in texts]
        else:
            return [self._fallback_embed(text) for text in texts]
    
    def _fallback_embed(self, text: str) -> List[float]:
        """
        Fallback embedding method using simple TF-IDF-like approach.
        This is a naive implementation for local development without API keys.
        
        Args:
            text: Input text
            
        Returns:
            Simple hash-based embedding vector (dimension 1536 to match OpenAI)
        """
        import hashlib
        import numpy as np
        
        # Create a deterministic vector based on text hash
        # This is NOT a real embedding but allows the system to work offline
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Generate a 1536-dimensional vector (matching OpenAI embedding size)
        # by repeating and transforming the hash
        vector = []
        for i in range(1536):
            byte_idx = i % len(hash_bytes)
            vector.append((hash_bytes[byte_idx] / 255.0 - 0.5) * 2)
        
        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = [v / norm for v in vector]
        
        return vector


# Global instance
_embedding_provider: Optional[EmbeddingProvider] = None


def get_embedding_provider() -> EmbeddingProvider:
    """Get or create the global embedding provider instance."""
    global _embedding_provider
    if _embedding_provider is None:
        _embedding_provider = EmbeddingProvider()
    return _embedding_provider


def embed_text(text: str) -> List[float]:
    """Convenience function to embed a single text."""
    provider = get_embedding_provider()
    return provider.embed(text)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Convenience function to embed multiple texts."""
    provider = get_embedding_provider()
    return provider.embed_batch(texts)

