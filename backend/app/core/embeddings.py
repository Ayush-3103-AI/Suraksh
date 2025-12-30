"""
Embedding Service
Generates text embeddings for vector search using OpenAI or local models.
"""

from typing import List, Optional

from llama_index.core.embeddings import BaseEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding

from app.core.config import settings


class EmbeddingService:
    """
    Service for generating text embeddings.
    Supports OpenAI embeddings and can be extended for local models.
    """
    
    def __init__(self, embedding_model: Optional[BaseEmbedding] = None):
        """
        Initialize embedding service.
        
        Args:
            embedding_model: Embedding model instance (optional)
        """
        if embedding_model is None:
            self.embedding_model = self._get_default_embedding_model()
        else:
            self.embedding_model = embedding_model
    
    def _get_default_embedding_model(self) -> BaseEmbedding:
        """
        Get default embedding model based on configuration.
        
        Returns:
            Embedding model instance
            
        Raises:
            ValueError: If embedding model cannot be initialized
        """
        # For now, use OpenAI embeddings (can be extended for other providers)
        api_key = settings.LLM_API_KEY
        
        if not api_key:
            # Fallback: try to use a local model or return None
            # For Phase 2, we'll use OpenAI text-embedding-3-small
            raise ValueError(
                "Embedding API key is required. Set LLM_API_KEY in environment variables."
            )
        
        # Use OpenAI text-embedding-3-small (1536 dimensions, fast and cheap)
        return OpenAIEmbedding(
            api_key=api_key,
            model="text-embedding-3-small",
        )
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            # Get embedding
            embedding = await self.embedding_model.aget_query_embedding(text)
            return embedding
        except Exception as e:
            # Fallback: return zero vector if embedding fails
            print(f"Warning: Failed to generate embedding: {e}")
            # Return zero vector with default dimension (1536 for text-embedding-3-small)
            return [0.0] * 1536
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts (batch).
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        try:
            # Get embeddings in batch
            embeddings = await self.embedding_model.aget_text_embedding_batch(texts)
            return embeddings
        except Exception as e:
            # Fallback: return zero vectors if embedding fails
            print(f"Warning: Failed to generate embeddings: {e}")
            return [[0.0] * 1536 for _ in texts]
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings.
        
        Returns:
            Embedding dimension
        """
        # OpenAI text-embedding-3-small has 1536 dimensions
        return 1536


# Global embedding service instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get or create global embedding service instance.
    
    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    
    if _embedding_service is None:
        try:
            _embedding_service = EmbeddingService()
        except ValueError:
            # If embedding service can't be initialized, create a fallback
            # that returns zero vectors (for development/testing)
            class FallbackEmbedding:
                async def aget_query_embedding(self, text: str):
                    return [0.0] * 1536
                
                async def aget_text_embedding_batch(self, texts: List[str]):
                    return [[0.0] * 1536 for _ in texts]
            
            from llama_index.core.embeddings import BaseEmbedding
            fallback = FallbackEmbedding()
            _embedding_service = EmbeddingService(embedding_model=fallback)  # type: ignore
    
    return _embedding_service

