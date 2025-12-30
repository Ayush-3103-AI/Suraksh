"""
Vault Endpoints
Secure file vault operations (upload, list, download, delete).
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.core.security import User, get_current_active_user
from app.services.vault_service import get_vault_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class FileMetadataResponse(BaseModel):
    """File metadata response model."""
    id: str
    filename: str
    size: int
    clearance_level: str
    uploaded_at: str
    uploaded_by: str
    content_type: str | None = None


class ListFilesResponse(BaseModel):
    """List files response model."""
    files: list[FileMetadataResponse]
    total: int


class UploadFileResponse(BaseModel):
    """Upload file response model."""
    file_id: str
    filename: str
    size: int
    uploaded_at: str


@router.get("/files", response_model=ListFilesResponse, status_code=status.HTTP_200_OK)
async def list_files(
    current_user: User = Depends(get_current_active_user),
) -> ListFilesResponse:
    """
    List all files in the vault accessible to the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of files with metadata
    """
    vault_service = get_vault_service()
    
    # Get all files (in Phase 2, filter by user clearance level)
    all_files = vault_service.list_files()
    
    # Filter files based on user clearance level
    clearance_order = {"L1": 1, "L2": 2, "L3": 3}
    user_level = clearance_order.get(current_user.clearance_level, 0)
    
    accessible_files = [
        f for f in all_files
        if clearance_order.get(f.clearance_level, 3) <= user_level
    ]
    
    # Convert to response format
    files_data = [
        FileMetadataResponse(
            id=str(f.id),
            filename=f.filename,
            size=f.size,
            clearance_level=f.clearance_level,
            uploaded_at=f.uploaded_at,
            uploaded_by=f.uploaded_by,
            content_type=f.content_type,
        )
        for f in accessible_files
    ]
    
    return ListFilesResponse(
        files=files_data,
        total=len(files_data),
    )


@router.post("/upload", response_model=UploadFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
) -> UploadFileResponse:
    """
    Upload a file to the vault.
    
    Args:
        file: Uploaded file
        current_user: Current authenticated user
        
    Returns:
        Upload response with file metadata
        
    Raises:
        HTTPException: If upload fails
    """
    vault_service = get_vault_service()
    
    filename = None
    try:
        # Read file content
        filename = file.filename or "unnamed"
        logger.info(f"Upload request received: filename={filename}, user={current_user.username}, content_type={file.content_type}")
        
        # Validate file
        if not filename or filename.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        logger.info(f"File read: filename={filename}, size={file_size} bytes")
        
        # Determine clearance level (default to user's level)
        clearance_level = current_user.clearance_level
        
        # Upload file
        metadata = vault_service.upload_file(
            file_content=file_content,
            filename=filename,
            clearance_level=clearance_level,
            uploaded_by=current_user.username,
            content_type=file.content_type,
        )
        
        logger.info(f"File uploaded successfully: file_id={metadata.id}, filename={filename}, user={current_user.username}")
        
        return UploadFileResponse(
            file_id=metadata.id,
            filename=metadata.filename,
            size=metadata.size,
            uploaded_at=metadata.uploaded_at,
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except RuntimeError as e:
        # Storage-related errors (MinIO or local filesystem)
        error_msg = str(e)
        logger.error(f"Storage error during upload: filename={filename}, user={current_user.username}, error={error_msg}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to storage: {error_msg}"
        ) from e
    except Exception as e:
        # Generic errors - log full traceback for debugging
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Unexpected error during upload: filename={filename}, user={current_user.username}, error_type={error_type}, error={error_msg}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {error_msg}"
        ) from e


@router.get("/files/{file_id}", status_code=status.HTTP_200_OK)
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Download a file from the vault.
    
    Args:
        file_id: File ID
        current_user: Current authenticated user
        
    Returns:
        File content
        
    Raises:
        HTTPException: If file not found or access denied
    """
    vault_service = get_vault_service()
    
    # Get file metadata
    metadata = vault_service.get_file(file_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check clearance level
    clearance_order = {"L1": 1, "L2": 2, "L3": 3}
    user_level = clearance_order.get(current_user.clearance_level, 0)
    file_level = clearance_order.get(metadata.clearance_level, 3)
    
    if file_level > user_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient clearance level to access this file"
        )
    
    # Get file content
    file_content = vault_service.get_file_content(file_id)
    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File content not found"
        )
    
    from fastapi.responses import Response
    
    return Response(
        content=file_content,
        media_type=metadata.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{metadata.filename}"'
        }
    )


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a file from the vault.
    
    Args:
        file_id: File ID
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If file not found or access denied
    """
    vault_service = get_vault_service()
    
    # Get file metadata
    metadata = vault_service.get_file(file_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check if user owns the file or has L1 clearance
    if metadata.uploaded_by != current_user.username and current_user.clearance_level != "L1":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only file owner or L1 users can delete files"
        )
    
    # Delete file
    deleted = vault_service.delete_file(file_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )
    
    return None

