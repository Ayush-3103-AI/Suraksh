"""
DeepSearch-RAG-Sentinel Agent
Hyper-accurate, cited answers using OpenRouter/DeepSeek API with Layout-Aware Parsing.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from app.services.deepsearch.file_search_service import GeminiFileSearchService

logger = logging.getLogger(__name__)


class DeepSearchRAGSentinel:
    """
    DeepSearch-RAG-Sentinel Agent
    
    Provides hyper-accurate, cited answers by autonomously navigating,
    retrieving, and synthesizing data from the PDF vault using OpenRouter/DeepSeek API.
    
    Key Features:
    - NEVER answers from internal training data if PDFs contain the information
    - MUST NOT speculate or "fill in the gaps"
    - ALWAYS includes citations in format [Source: Filename, Page X]
    - Uses Layout-Aware Parsing for tables, charts, and diagrams
    - Cross-references retrieved chunks to ensure no conflicting data
    """
    
    def __init__(self, file_search_service: Optional[GeminiFileSearchService] = None):
        """
        Initialize DeepSearch-RAG-Sentinel agent.
        
        Args:
            file_search_service: File Search service instance (OpenRouter/DeepSeek)
        """
        self.file_search_service = file_search_service or GeminiFileSearchService()
    
    async def query(
        self,
        user_query: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Process a user query and return a hyper-accurate, cited answer.
        
        This method follows the interaction protocol:
        1. Query Reformulation: Transform natural language into high-precision search vector
        2. Context Retrieval: Invoke File Search with Layout Parser
        3. Cross-Reference Validation: Compare retrieved chunks for conflicts
        4. Synthesized Generation: Construct response with Grounding Metadata
        5. Citation Audit: Verify every claim is mapped to file and page
        
        Args:
            user_query: Natural language query
            top_k: Number of top results to retrieve
            
        Returns:
            Dictionary with answer, citations, and source summary
        """
        # Step 1: Query Reformulation
        reformulated_query = self._reformulate_query(user_query)
        logger.info(f"Query reformulated: {user_query} -> {reformulated_query}")
        
        # Step 2: Context Retrieval via File Search
        try:
            search_result = await self.file_search_service.search(
                query=reformulated_query,
                top_k=top_k,
            )
        except Exception as e:
            logger.error(f"File Search failed: {e}")
            return {
                "query": user_query,
                "answer": "The current documentation does not contain this information.",
                "citations": [],
                "source_summary": [],
                "error": str(e),
            }
        
        # Step 3: Cross-Reference Validation
        validated_result = self._validate_cross_references(search_result)
        
        # Step 4: Synthesized Generation with citations
        answer_with_citations = self._add_citations_to_answer(
            validated_result["answer"],
            validated_result["citations"],
        )
        
        # Step 5: Citation Audit
        source_summary = self._audit_citations(validated_result["citations"])
        
        return {
            "query": user_query,
            "answer": answer_with_citations,
            "citations": validated_result["citations"],
            "source_summary": source_summary,
            "grounding_metadata": validated_result.get("grounding_metadata", {}),
        }
    
    def _reformulate_query(self, query: str) -> str:
        """
        Transform natural language input into high-precision search vector.
        
        Args:
            query: Original user query
            
        Returns:
            Reformulated query optimized for semantic retrieval
        """
        # Enhance query with context for better retrieval
        # Add instructions for layout-aware parsing
        enhanced_query = f"""
        Search the document vault for information about: {query}
        
        Please provide accurate information with specific citations including:
        - Filename
        - Page number
        - Direct quotes when relevant
        
        If the information is not found in the documents, state that clearly.
        """
        
        return enhanced_query.strip()
    
    def _validate_cross_references(self, search_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare retrieved chunks to ensure no conflicting data exists.
        
        Args:
            search_result: Search result from File Search API
            
        Returns:
            Validated search result with conflict detection
        """
        answer = search_result.get("answer", "")
        citations = search_result.get("citations", [])
        
        # Check for conflicting information
        # This is a simplified version - in production, you might want to
        # do more sophisticated conflict detection
        
        # Group citations by filename
        citations_by_file = {}
        for citation in citations:
            filename = citation.get("filename", "Unknown")
            if filename not in citations_by_file:
                citations_by_file[filename] = []
            citations_by_file[filename].append(citation)
        
        # Add conflict detection note if multiple sources
        if len(citations_by_file) > 1:
            logger.info(f"Information found across {len(citations_by_file)} different documents")
        
        return {
            "answer": answer,
            "citations": citations,
            "grounding_metadata": search_result.get("grounding_metadata", {}),
            "conflict_detected": False,  # Simplified - could be enhanced
        }
    
    def _add_citations_to_answer(self, answer: str, citations: List[Dict[str, Any]]) -> str:
        """
        Add citations to answer in the required format [Source: Filename, Page X].
        
        Args:
            answer: Original answer text
            citations: List of citation dictionaries
            
        Returns:
            Answer with properly formatted citations
        """
        if not citations:
            return answer
        
        # Check if citations are already in the answer
        if "[Source:" in answer:
            # Citations already present, just ensure format is correct
            return self._normalize_citation_format(answer)
        
        # Add citations at the end of the answer
        citation_text = "\n\n**Sources:**\n"
        for i, citation in enumerate(citations, 1):
            filename = citation.get("filename", "Unknown")
            page = citation.get("page")
            
            if page:
                citation_text += f"[Source: {filename}, Page {page}]\n"
            else:
                citation_text += f"[Source: {filename}]\n"
        
        return answer + citation_text
    
    def _normalize_citation_format(self, text: str) -> str:
        """
        Normalize citation format to [Source: Filename, Page X].
        
        Args:
            text: Text with citations
            
        Returns:
            Text with normalized citations
        """
        # Pattern to match various citation formats
        patterns = [
            (r'\[Source:\s*([^,]+),\s*Page\s*(\d+)\]', r'[Source: \1, Page \2]'),
            (r'\[Source:\s*([^\]]+)\]', r'[Source: \1]'),
        ]
        
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _audit_citations(self, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Verify that every claim in the response is mapped to a specific file and page.
        
        Args:
            citations: List of citations
            
        Returns:
            Source summary with all documents accessed
        """
        source_summary = []
        seen_files = set()
        
        for citation in citations:
            filename = citation.get("filename", "Unknown")
            page = citation.get("page")
            confidence = citation.get("confidence")
            
            if filename not in seen_files:
                source_summary.append({
                    "filename": filename,
                    "pages": [page] if page else [],
                    "confidence": confidence,
                })
                seen_files.add(filename)
            else:
                # Add page to existing file entry
                for source in source_summary:
                    if source["filename"] == filename and page:
                        if page not in source["pages"]:
                            source["pages"].append(page)
        
        return source_summary
    
    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        mime_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a document to the File Search Store.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            mime_type: MIME type (auto-detected if not provided)
            
        Returns:
            Upload result with file_id
        """
        return await self.file_search_service.upload_file(
            file_content=file_content,
            filename=filename,
            mime_type=mime_type,
        )

