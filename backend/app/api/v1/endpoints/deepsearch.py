"""
DeepSearch-RAG-Sentinel API Endpoints
Hyper-accurate, cited answers using OpenRouter/DeepSeek API.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security import User, get_current_active_user
from app.services.deepsearch.sentinel_agent import DeepSearchRAGSentinel

router = APIRouter()


# Request/Response Models
class DeepSearchRequest(BaseModel):
    """DeepSearch query request model."""
    query: str
    top_k: int = 5


class Citation(BaseModel):
    """Citation model."""
    filename: str
    page: int | None = None
    confidence: float | None = None


class SourceSummary(BaseModel):
    """Source summary model."""
    filename: str
    pages: list[int] = []
    confidence: float | None = None


class DeepSearchResponse(BaseModel):
    """DeepSearch response model."""
    query: str
    answer: str
    citations: list[Citation] = []
    source_summary: list[SourceSummary] = []
    error: str | None = None


@router.post("/", response_model=DeepSearchResponse, status_code=status.HTTP_200_OK)
async def deepsearch_query(
    request: DeepSearchRequest,
    current_user: User = Depends(get_current_active_user),
) -> DeepSearchResponse:
    """
    Perform DeepSearch-RAG-Sentinel query using OpenRouter/DeepSeek API.
    
    This endpoint provides hyper-accurate, cited answers by:
        - Using OpenRouter/DeepSeek API for document retrieval
    - Applying Layout-Aware Parsing for tables, charts, and diagrams
    - Including citations in format [Source: Filename, Page X]
    - Never speculating if information is not in the PDFs
    
    Args:
        request: DeepSearch request with query
        current_user: Current authenticated user
        
    Returns:
        DeepSearch response with answer and citations
        
    Raises:
        HTTPException: If query fails
    """
    # Validate query
    if not request.query or len(request.query.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must be at least 3 characters long"
        )
    
    # Validate top_k
    if request.top_k < 1 or request.top_k > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="top_k must be between 1 and 50"
        )
    
    # Initialize DeepSearch-RAG-Sentinel agent
    agent = DeepSearchRAGSentinel()
    
    try:
        # Perform DeepSearch query
        result = await agent.query(
            user_query=request.query,
            top_k=request.top_k,
        )
        
        # Format citations
        citations = [
            Citation(
                filename=c.get("filename", "Unknown"),
                page=c.get("page"),
                confidence=c.get("confidence"),
            )
            for c in result.get("citations", [])
        ]
        
        # Format source summary
        source_summary = [
            SourceSummary(
                filename=s.get("filename", "Unknown"),
                pages=s.get("pages", []),
                confidence=s.get("confidence"),
            )
            for s in result.get("source_summary", [])
        ]
        
        return DeepSearchResponse(
            query=result["query"],
            answer=result["answer"],
            citations=citations,
            source_summary=source_summary,
            error=result.get("error"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DeepSearch query failed: {str(e)}"
        ) from e

