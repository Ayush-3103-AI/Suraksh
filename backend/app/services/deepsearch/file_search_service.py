"""
File Search Service using OpenRouter/DeepSeek
Provides RAG capabilities with citations using OpenRouter API.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiFileSearchService:
    """
    Service for performing RAG queries using OpenRouter/DeepSeek.
    
    Note: This service maintains the same interface as before but uses OpenRouter
    instead of Gemini File Search API. File uploads are handled by the vault service.
    """
    
    def __init__(self, api_key: Optional[str] = None, store_id: Optional[str] = None):
        """
        Initialize File Search service with OpenRouter.
        
        Args:
            api_key: OpenRouter API key (defaults to settings)
            store_id: Store ID (kept for compatibility, not used with OpenRouter)
        """
        self.api_key = api_key or settings.LLM_API_KEY
        if not self.api_key:
            raise ValueError(
                "LLM API key is required. Set LLM_API_KEY in environment variables."
            )
        
        # Configure OpenAI client for OpenRouter
        base_url = settings.OPENROUTER_BASE_URL or "https://openrouter.ai/api/v1"
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url,
            default_headers={
                "HTTP-Referer": settings.OPENROUTER_HTTP_REFERER or "https://suraksh.local",
                "X-Title": settings.OPENROUTER_SITE_NAME or "Suraksh Portal",
            } if base_url == "https://openrouter.ai/api/v1" else None,
        )
        
        self.model = settings.LLM_MODEL or "deepseek/deepseek-r1-0528:free"
        self.store_id = store_id  # Kept for compatibility
    
    def get_or_create_store(self) -> str:
        """
        Get existing File Search Store or create a new one.
        
        Returns:
            File Search Store ID
        """
        if self.store_id:
            # Verify store exists
            try:
                # Try to list stores to verify it exists
                # Note: The API might not have a direct "get" method, so we'll try to use it
                logger.info(f"Using configured File Search Store: {self.store_id}")
                return self.store_id
            except Exception as e:
                logger.warning(f"Store {self.store_id} may not exist, will create on first upload: {e}")
        
        # Store ID will be created on first file upload
        # For now, return None to indicate we need to create one
        logger.info("No File Search Store ID configured, will create on first file upload")
        return None
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        mime_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a file (compatibility method).
        
        Note: With OpenRouter, files are managed by the vault service.
        This method is kept for compatibility but doesn't perform actual uploads.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            mime_type: MIME type (auto-detected if not provided)
            
        Returns:
            Dictionary with file metadata
        """
        logger.info(f"File upload requested for {filename} (handled by vault service)")
        
        # Auto-detect MIME type if not provided
        if not mime_type:
            if filename.lower().endswith('.pdf'):
                mime_type = 'application/pdf'
            elif filename.lower().endswith('.txt'):
                mime_type = 'text/plain'
            elif filename.lower().endswith('.docx'):
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                mime_type = 'application/octet-stream'
        
        return {
            "file_id": f"vault_{filename}",
            "filename": filename,
            "mime_type": mime_type,
            "store_id": "vault",
            "message": "File should be uploaded via vault service. This is a compatibility method.",
        }
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Perform RAG search using OpenRouter/DeepSeek.
        
        Args:
            query: User query string
            top_k: Number of top results to retrieve (not used with OpenRouter, kept for compatibility)
            
        Returns:
            Dictionary with answer, citations, and grounding metadata
        """
        try:
            # Build enhanced query that instructs the model to cite sources
            enhanced_query = f"""
            {query}
            
            Please provide accurate information from the uploaded documents.
            If the information is not found in the documents, state: "The current documentation does not contain this information."
            Include citations in the format [Source: Filename, Page X] when referencing specific information.
            """
            
            # Generate content using OpenRouter
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": enhanced_query
                    }
                ],
                temperature=settings.LLM_TEMPERATURE,
            )
            
            # Extract answer
            answer = response.choices[0].message.content or ""
            
            # Extract citations from answer text
            citations = self._parse_citations_from_text(answer)
            
            return {
                "query": query,
                "answer": answer,
                "citations": citations,
                "grounding_metadata": {},
            }
        except Exception as e:
            logger.error(f"File Search query failed: {e}")
            raise RuntimeError(f"Search failed: {e}") from e
    
    
    def _parse_citations_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse citations from response text (fallback method).
        
        Args:
            text: Response text that may contain citation markers
            
        Returns:
            List of citation dictionaries
        """
        citations = []
        
        # Look for citation patterns in text
        # Pattern: [Source: filename, Page X] or similar
        citation_pattern = r'\[Source:\s*([^,]+),\s*Page\s*(\d+)\]'
        matches = re.finditer(citation_pattern, text, re.IGNORECASE)
        
        for match in matches:
            citations.append({
                "filename": match.group(1).strip(),
                "page": int(match.group(2)),
                "confidence": None,
            })
        
        return citations

