"""
Ingest Endpoints
Data ingestion into GraphRAG pipeline (Text/PDF -> Chunk -> Extract -> Neo4j/Qdrant).
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.security import User, get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()
# #region agent log
import json
try:
    with open(r'd:\Hacakathons\Suraksh\.cursor\debug.log', 'a') as f:
        f.write(json.dumps({"location":"ingest.py:module_init","message":"Ingest module initialized","data":{"router_created":True},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + '\n')
except: pass
# #endregion

# Lazy-load dependencies to allow router registration even if dependencies fail
_ingestion_pipeline_available = None
_vault_service_available = None


def _get_ingestion_pipeline():
    """Lazy-load IngestionPipeline with error handling."""
    global _ingestion_pipeline_available
    
    if _ingestion_pipeline_available is False:
        return None
    
    try:
        from app.services.graph_rag.ingestion import IngestionPipeline
        pipeline = IngestionPipeline()
        _ingestion_pipeline_available = True
        return pipeline
    except ValueError as e:
        # Fixed: Catch ValueError (usually LLM API key missing) and provide helpful message
        error_msg = str(e)
        if "API key" in error_msg or "LLM_API_KEY" in error_msg:
            logger.error(f"LLM API key not configured: {e}")
            _ingestion_pipeline_available = False
            return None
        else:
            logger.error(f"Failed to initialize IngestionPipeline: {e}", exc_info=True)
            _ingestion_pipeline_available = False
            return None
    except Exception as e:
        # Fixed: Enhanced error logging with full traceback
        logger.error(f"Failed to import/initialize IngestionPipeline: {type(e).__name__}: {e}", exc_info=True)
        _ingestion_pipeline_available = False
        return None


def _get_vault_service():
    """Lazy-load VaultService with error handling."""
    global _vault_service_available
    
    if _vault_service_available is False:
        return None
    
    try:
        from app.services.vault_service import get_vault_service
        _vault_service_available = True
        return get_vault_service()
    except Exception as e:
        logger.error(f"Failed to import VaultService: {e}", exc_info=True)
        _vault_service_available = False
        return None


# Request/Response Models
class IngestRequest(BaseModel):
    """Ingest request model."""
    text: str
    source_id: str | None = None
    source_name: str | None = None
    clearance_level: str = "L3"
    extract_graph: bool = True


class IngestFileRequest(BaseModel):
    """Ingest file request model."""
    # Fixed: Accept Any type initially, validator will normalize to str
    file_id: str
    extract_graph: bool = True
    
    @field_validator('file_id', mode='before')
    @classmethod
    def validate_file_id(cls, v) -> str:
        """Validate and normalize file_id - accepts string or number, returns trimmed string."""
        # Fixed: Handle missing field (None) before other checks
        if v is None:
            raise ValueError("file_id is required and cannot be None or missing")
        
        # Handle empty strings, lists, dicts, etc.
        if isinstance(v, (list, dict)):
            raise ValueError("file_id must be a string or number, not a list or object")
        
        # Handle boolean False/True edge case
        if isinstance(v, bool):
            raise ValueError("file_id cannot be a boolean value")
        
        # Convert to string - be very permissive
        try:
            # Handle numeric types - convert to string without decimal for integers
            if isinstance(v, (int, float)):
                # For floats, convert to int if it's a whole number, otherwise keep as float string
                if isinstance(v, float) and v.is_integer():
                    str_value = str(int(v))
                else:
                    str_value = str(v)
            else:
                str_value = str(v)
            
            # Strip whitespace
            str_value = str_value.strip()
        except Exception as e:
            raise ValueError(f"file_id must be convertible to string: {e}")
        
        # Validate the string value
        if not str_value or str_value.lower() in ('undefined', 'null', 'none', ''):
            raise ValueError(f"file_id cannot be empty or invalid (received: {repr(v)})")
        
        return str_value
    
    @model_validator(mode='after')
    def validate_model(self):
        """Additional model-level validation after field validation."""
        # Fixed: Double-check file_id is valid after all validations
        if not self.file_id or not self.file_id.strip():
            raise ValueError("file_id cannot be empty after validation")
        return self
    
    # Fixed: Use ConfigDict for Pydantic v2 with proper validation
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": "123",
                "extract_graph": True
            }
        },
        # Make validation more lenient - strip whitespace automatically
        str_strip_whitespace=True,
        # Allow extra fields to be ignored (in case frontend sends additional data)
        extra="ignore",
    )


class IngestResponse(BaseModel):
    """Ingest response model."""
    source_id: str
    source_name: str | None
    entities_extracted: int
    relations_extracted: int
    chunks_created: int
    status: str


@router.post("/", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_data(
    request: IngestRequest,
    current_user: User = Depends(get_current_active_user),
) -> IngestResponse:
    """
    Ingest text data into the GraphRAG pipeline.
    
    Args:
        request: Ingest request with text data
        current_user: Current authenticated user
        
    Returns:
        Ingestion results
        
    Raises:
        HTTPException: If ingestion fails
    """
    # Simplified: Basic clearance check (can be removed if not needed)
    # Keeping minimal check for backward compatibility
    
    # Lazy-load ingestion pipeline
    pipeline = _get_ingestion_pipeline()
    if pipeline is None:
        # Fixed: Provide more helpful error message
        error_detail = "Ingestion service is not available. "
        
        # Check if it's an LLM configuration issue
        try:
            from app.core.config import settings
            if not settings.LLM_API_KEY:
                error_detail += "LLM_API_KEY is not set in environment variables. Please set it in backend/.env file. See COMPLETE_SETUP_GUIDE.md for instructions."
            else:
                error_detail += "GraphRAG dependencies may be missing or misconfigured. Check backend logs for details."
        except:
            error_detail += "GraphRAG dependencies may be missing or misconfigured. Check backend logs for details."
        
        logger.error(f"Ingestion failed: {error_detail}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_detail
        )
    
    try:
        # Ingest data
        result = await pipeline.ingest_text(
            text=request.text,
            source_id=request.source_id or f"source_{current_user.username}",
            source_name=request.source_name,
            clearance_level=request.clearance_level,
        )
        
        return IngestResponse(
            source_id=result["source_id"],
            source_name=result.get("source_name"),
            entities_extracted=result["entities_extracted"],
            relations_extracted=result["relations_extracted"],
            chunks_created=result["chunks_created"],
            status=result["status"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest data: {str(e)}"
        ) from e


@router.post("/file", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_file(
    request: IngestFileRequest,
    current_user: User = Depends(get_current_active_user),
) -> IngestResponse:
    """
    Ingest a file from the vault into the GraphRAG pipeline.
    
    Args:
        request: Ingest file request with file_id
        current_user: Current authenticated user
        
    Returns:
        Ingestion results
        
    Raises:
        HTTPException: If file not found or ingestion fails
    """
    # Fixed: Log received request for debugging with detailed info
    logger.info(
        f"File ingestion request received: file_id={request.file_id} "
        f"(type: {type(request.file_id).__name__}), "
        f"extract_graph={request.extract_graph}, "
        f"user={current_user.username}"
    )
    
    # Fixed: Additional validation with better error messages
    if not request.file_id or not request.file_id.strip():
        logger.warning(f"Empty or whitespace-only file_id received from user {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_id is required and cannot be empty or whitespace-only"
        )
    
    # Fixed: Validate file_id is provided (already validated by Pydantic, but double-check)
    file_id = request.file_id.strip() if isinstance(request.file_id, str) else str(request.file_id).strip()
    if not file_id:
        logger.warning(f"Empty file_id provided by user {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_id is required and cannot be empty"
        )
    
    logger.info(f"File ingestion requested: file_id={file_id}, user={current_user.username}")
    
    # Lazy-load vault service
    vault_service = _get_vault_service()
    if vault_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vault service is not available. Please check backend configuration."
        )
    
    # Get file from vault
    file_metadata = vault_service.get_file(file_id)
    if not file_metadata:
        logger.warning(f"File not found: file_id={file_id}, user={current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found in vault with id: {file_id}"
        )
    
    # Simplified: Removed complex clearance level checks
    # File can be ingested by any authenticated user
    
    # Get file content
    file_content = vault_service.get_file_content(file_id)
    if not file_content:
        logger.warning(f"File content not found: file_id={file_id}, filename={file_metadata.filename}, user={current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File content not found for file '{file_metadata.filename}'"
        )
    
    # Extract text from file based on content type
    content_type = file_metadata.content_type or ""
    filename = file_metadata.filename.lower()
    
    text_content = None
    
    # Handle PDF files
    if content_type == "application/pdf" or filename.endswith(".pdf"):
        try:
            from app.services.graph_rag.pdf_extractor import get_pdf_extractor
            
            pdf_extractor = get_pdf_extractor()
            text_content = await pdf_extractor.extract_text(
                pdf_bytes=file_content,
                filename=file_metadata.filename,
            )
            
            if not text_content or not text_content.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Could not extract text from PDF file '{file_metadata.filename}'. The PDF may be image-based or corrupted."
                )
        except ImportError:
            # Fallback to PyPDF2 if enhanced extractor not available
            try:
                import PyPDF2
                import io
                
                pdf_file = io.BytesIO(file_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                text_parts = []
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    except Exception as page_error:
                        logger.warning(f"Error extracting text from PDF page {page_num}: {str(page_error)}")
                        continue
                
                if text_parts:
                    text_content = "\n\n".join(text_parts)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Could not extract text from PDF file '{file_metadata.filename}'. The PDF may be image-based or corrupted."
                    )
            except ImportError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="PDF processing libraries are not installed. Please install them: pip install PyPDF2 pdfplumber"
                )
        except Exception as pdf_error:
            logger.error(f"PDF extraction error: file_id={file_id}, filename={file_metadata.filename}, error={str(pdf_error)}, user={current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract text from PDF file '{file_metadata.filename}': {str(pdf_error)}"
            )
    
    # Handle text files
    elif content_type.startswith("text/") or any(filename.endswith(ext) for ext in [".txt", ".csv", ".json", ".html", ".xml", ".md"]):
        try:
            text_content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            # Try other encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    text_content = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if text_content is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File '{file_metadata.filename}' could not be decoded as text. Unsupported encoding."
                )
    
    # Reject unsupported file types
    else:
        logger.warning(f"Unsupported file type: file_id={file_id}, filename={file_metadata.filename}, content_type={content_type}, user={current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File format not supported. File '{file_metadata.filename}' (type: {content_type}) is not supported. Supported formats: PDF (.pdf), Text files (.txt, .csv, .json, .html, .xml, .md)"
        )
    
    # Lazy-load ingestion pipeline
    pipeline = _get_ingestion_pipeline()
    if pipeline is None:
        # Fixed: Provide more helpful error message
        error_detail = "Ingestion service is not available. "
        
        # Check if it's an LLM configuration issue
        try:
            from app.core.config import settings
            if not settings.LLM_API_KEY:
                error_detail += "LLM_API_KEY is not set in environment variables. Please set it in backend/.env file. See COMPLETE_SETUP_GUIDE.md for instructions."
            else:
                error_detail += "GraphRAG dependencies may be missing or misconfigured. Check backend logs for details."
        except:
            error_detail += "GraphRAG dependencies may be missing or misconfigured. Check backend logs for details."
        
        logger.error(f"Ingestion failed: {error_detail}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_detail
        )
    
    try:
        logger.info(f"Starting ingestion: file_id={file_id}, filename={file_metadata.filename}, size={len(file_content)} bytes, user={current_user.username}")
        
        # Ingest file content
        result = await pipeline.ingest_text(
            text=text_content,
            source_id=f"file_{file_metadata.id}",
            source_name=file_metadata.filename,
            clearance_level=file_metadata.clearance_level,
            extract_graph=request.extract_graph,
        )
        
        logger.info(f"Ingestion successful: file_id={file_id}, filename={file_metadata.filename}, entities={result['entities_extracted']}, relations={result['relations_extracted']}, chunks={result['chunks_created']}, user={current_user.username}")
        
        return IngestResponse(
            source_id=result["source_id"],
            source_name=result.get("source_name"),
            entities_extracted=result["entities_extracted"],
            relations_extracted=result["relations_extracted"],
            chunks_created=result["chunks_created"],
            status=result["status"],
        )
    except Exception as e:
        logger.error(f"Ingestion failed: file_id={file_id}, filename={file_metadata.filename}, error={str(e)}, user={current_user.username}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest file '{file_metadata.filename}': {str(e)}"
        ) from e


@router.get("/diagnostics", status_code=status.HTTP_200_OK)
async def get_ingestion_diagnostics(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get diagnostics for ingestion service (LLM configuration, pipeline status).
    
    Returns:
        Dictionary with diagnostic information
    """
    diagnostics = {
        "pipeline_available": False,
        "llm_configured": False,
        "llm_error": None,
        "extractor_available": False,
        "extractor_error": None,
    }
    
    # Check pipeline availability
    pipeline = _get_ingestion_pipeline()
    diagnostics["pipeline_available"] = pipeline is not None
    
    # Check LLM configuration
    try:
        from app.services.graph_rag.llm_setup import get_extraction_llm
        llm = get_extraction_llm()
        diagnostics["llm_configured"] = llm is not None
        if llm:
            diagnostics["llm_type"] = type(llm).__name__
    except Exception as e:
        diagnostics["llm_error"] = str(e)
        diagnostics["llm_configured"] = False
    
    # Check extractor
    try:
        from app.services.graph_rag.extractor import GraphRAGExtractor
        extractor = GraphRAGExtractor()
        diagnostics["extractor_available"] = extractor.llm is not None
        if extractor.llm is None:
            diagnostics["extractor_error"] = "LLM instance is None"
    except Exception as e:
        diagnostics["extractor_error"] = str(e)
        diagnostics["extractor_available"] = False
    
    return diagnostics


@router.get("/export", status_code=status.HTTP_200_OK)
async def export_knowledge_graph(
    document_id: str | None = None,
    limit: int = 1000,
    include_isolated: bool = False,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Export knowledge graph as JSON-compliant structure.
    
    Args:
        document_id: Optional document ID to filter by
        limit: Maximum number of nodes to export
        include_isolated: Whether to include nodes without relationships
        current_user: Current authenticated user
        
    Returns:
        JSON object with "nodes" and "edges" arrays
    """
    try:
        from app.services.graph_rag.kg_export import get_kg_exporter
        
        exporter = get_kg_exporter()
        graph_data = await exporter.export_graph(
            document_id=document_id,
            limit=limit,
            include_isolated_nodes=include_isolated,
        )
        
        return graph_data
    except Exception as e:
        logger.error(f"Failed to export knowledge graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export knowledge graph: {str(e)}"
        ) from e

