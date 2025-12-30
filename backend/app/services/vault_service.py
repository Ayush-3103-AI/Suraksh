"""
Vault Service
Handles secure file storage and retrieval using MinIO object storage.
"""

import io
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import settings
from app.core.storage import ensure_minio_bucket, get_minio_client

logger = logging.getLogger(__name__)

# Fixed: Metadata file path for persistence across restarts
METADATA_FILE = Path("vault_storage") / "_metadata.json"


class FileMetadata:
    """File metadata model."""
    
    def __init__(
        self,
        id: str,
        filename: str,
        size: int,
        clearance_level: str,
        uploaded_at: str,
        uploaded_by: str,
        content_type: Optional[str] = None,
        file_path: Optional[str] = None,
    ):
        self.id = id
        self.filename = filename
        self.size = size
        self.clearance_level = clearance_level
        self.uploaded_at = uploaded_at
        self.uploaded_by = uploaded_by
        self.content_type = content_type
        self.file_path = file_path
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "size": self.size,
            "clearance_level": self.clearance_level,
            "uploaded_at": self.uploaded_at,
            "uploaded_by": self.uploaded_by,
            "content_type": self.content_type,
        }


class VaultService:
    """Vault service for file storage using MinIO with local filesystem fallback."""
    
    def __init__(self):
        """Initialize vault service."""
        # MinIO bucket name
        self.bucket_name = settings.MINIO_BUCKET_NAME
        
        # Local filesystem fallback directory
        self.local_storage_dir = Path("vault_storage")
        self.local_storage_dir.mkdir(exist_ok=True)
        
        # Track if MinIO is available
        self._minio_available = None
        
        # Fixed: Load file metadata from disk for persistence across restarts
        self._files: Dict[str, FileMetadata] = {}
        self._load_metadata()
    
    def _check_minio_available(self) -> bool:
        """Check if MinIO is available."""
        if self._minio_available is None:
            try:
                from app.core.storage import verify_minio_connection
                self._minio_available = verify_minio_connection()
            except Exception as e:
                logger.warning(f"MinIO availability check failed: {e}")
                self._minio_available = False
        return self._minio_available
    
    def _load_metadata(self) -> None:
        """
        Fixed: Load file metadata from disk to persist across server restarts.
        """
        try:
            if METADATA_FILE.exists():
                with open(METADATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for file_id, meta in data.items():
                        self._files[file_id] = FileMetadata(
                            id=meta["id"],
                            filename=meta["filename"],
                            size=meta["size"],
                            clearance_level=meta["clearance_level"],
                            uploaded_at=meta["uploaded_at"],
                            uploaded_by=meta["uploaded_by"],
                            content_type=meta.get("content_type"),
                            file_path=meta.get("file_path"),
                        )
                logger.info(f"Loaded {len(self._files)} files from metadata cache")
        except Exception as e:
            logger.warning(f"Failed to load metadata from disk: {e}")
            self._files = {}
    
    def _save_metadata(self) -> None:
        """
        Fixed: Save file metadata to disk for persistence across server restarts.
        """
        try:
            # Ensure directory exists
            self.local_storage_dir.mkdir(exist_ok=True)
            
            data = {}
            for file_id, meta in self._files.items():
                data[file_id] = {
                    "id": meta.id,
                    "filename": meta.filename,
                    "size": meta.size,
                    "clearance_level": meta.clearance_level,
                    "uploaded_at": meta.uploaded_at,
                    "uploaded_by": meta.uploaded_by,
                    "content_type": meta.content_type,
                    "file_path": meta.file_path,
                }
            
            with open(METADATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved metadata for {len(self._files)} files")
        except Exception as e:
            logger.error(f"Failed to save metadata to disk: {e}")
    
    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        clearance_level: str,
        uploaded_by: str,
        content_type: Optional[str] = None,
    ) -> FileMetadata:
        """
        Upload a file to the vault (MinIO with local filesystem fallback).
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            clearance_level: Clearance level (L1, L2, L3)
            uploaded_by: Username of uploader
            content_type: MIME type of the file
            
        Returns:
            FileMetadata object
            
        Raises:
            RuntimeError: If both MinIO and local storage fail
        """
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        object_name = file_id
        storage_path = None
        
        # Try MinIO first if available
        if self._check_minio_available():
            try:
                # Ensure bucket exists before upload
                ensure_minio_bucket(self.bucket_name)
                
                # Upload file to MinIO
                minio_client = get_minio_client()
                file_stream = io.BytesIO(file_content)
                # Fixed: Ensure stream position is at the beginning
                file_stream.seek(0)
                
                minio_client.put_object(
                    bucket_name=self.bucket_name,
                    object_name=object_name,
                    data=file_stream,
                    length=len(file_content),
                    content_type=content_type or "application/octet-stream",
                )
                
                logger.info(f"File uploaded to MinIO: {file_id} ({filename})")
                storage_path = f"minio://{self.bucket_name}/{object_name}"
            except Exception as e:
                logger.warning(f"MinIO upload failed, falling back to local storage: {e}")
                self._minio_available = False  # Mark as unavailable for next time
        
        # Fallback to local filesystem if MinIO failed or unavailable
        if not storage_path:
            try:
                local_file_path = self.local_storage_dir / file_id
                with open(local_file_path, "wb") as f:
                    f.write(file_content)
                storage_path = str(local_file_path)
                logger.info(f"File uploaded to local storage: {file_id} ({filename})")
            except Exception as e:
                logger.error(f"Both MinIO and local storage failed: {e}", exc_info=True)
                raise RuntimeError(f"Failed to upload file: {e}") from e
        
        # Create metadata
        metadata = FileMetadata(
            id=file_id,
            filename=filename,
            size=len(file_content),
            clearance_level=clearance_level,
            uploaded_at=datetime.utcnow().isoformat(),
            uploaded_by=uploaded_by,
            content_type=content_type,
            file_path=storage_path,  # Store storage path (MinIO or local)
        )
        
        # Store metadata
        self._files[file_id] = metadata
        
        # Fixed: Persist metadata to disk
        self._save_metadata()
        
        return metadata
    
    def get_file(self, file_id: str) -> Optional[FileMetadata]:
        """
        Get file metadata by ID.
        
        Args:
            file_id: File ID
            
        Returns:
            FileMetadata if found, None otherwise
        """
        return self._files.get(file_id)
    
    def get_file_content(self, file_id: str) -> Optional[bytes]:
        """
        Get file content by ID from storage (MinIO or local filesystem).
        
        Args:
            file_id: File ID
            
        Returns:
            File content as bytes if found, None otherwise
        """
        metadata = self._files.get(file_id)
        if not metadata:
            return None
        
        storage_path = metadata.file_path or file_id
        
        # Check if it's a MinIO path or local path
        if storage_path.startswith("minio://"):
            # Extract bucket and object from minio://bucket/object format
            try:
                parts = storage_path.replace("minio://", "").split("/", 1)
                bucket = parts[0]
                object_name = parts[1] if len(parts) > 1 else file_id
                
                minio_client = get_minio_client()
                response = minio_client.get_object(
                    bucket_name=bucket,
                    object_name=object_name,
                )
                
                file_content = response.read()
                response.close()
                response.release_conn()
                
                return file_content
            except Exception as e:
                logger.error(f"Failed to retrieve file from MinIO: {file_id}, error: {e}")
                return None
        else:
            # Local filesystem path
            try:
                local_path = Path(storage_path)
                if local_path.exists():
                    with open(local_path, "rb") as f:
                        return f.read()
                else:
                    logger.error(f"Local file not found: {storage_path}")
                    return None
            except Exception as e:
                logger.error(f"Failed to retrieve file from local storage: {file_id}, error: {e}")
                return None
    
    def list_files(self, uploaded_by: Optional[str] = None) -> List[FileMetadata]:
        """
        List all files in the vault.
        
        Args:
            uploaded_by: Optional filter by uploader username
            
        Returns:
            List of FileMetadata objects
        """
        files = list(self._files.values())
        
        if uploaded_by:
            files = [f for f in files if f.uploaded_by == uploaded_by]
        
        # Sort by upload date (newest first)
        files.sort(key=lambda f: f.uploaded_at, reverse=True)
        
        return files
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from the vault (MinIO or local filesystem).
        
        Args:
            file_id: File ID
            
        Returns:
            True if deleted, False if not found
        """
        metadata = self._files.get(file_id)
        if not metadata:
            return False
        
        storage_path = metadata.file_path or file_id
        
        # Check if it's a MinIO path or local path
        if storage_path.startswith("minio://"):
            # Extract bucket and object from minio://bucket/object format
            try:
                parts = storage_path.replace("minio://", "").split("/", 1)
                bucket = parts[0]
                object_name = parts[1] if len(parts) > 1 else file_id
                
                minio_client = get_minio_client()
                minio_client.remove_object(
                    bucket_name=bucket,
                    object_name=object_name,
                )
                
                logger.info(f"File deleted from MinIO: {file_id}")
            except Exception as e:
                logger.warning(f"Failed to delete file from MinIO: {file_id}, error: {e}")
                # Continue to remove metadata even if MinIO deletion fails
        else:
            # Local filesystem path
            try:
                local_path = Path(storage_path)
                if local_path.exists():
                    local_path.unlink()
                    logger.info(f"File deleted from local storage: {file_id}")
            except Exception as e:
                logger.warning(f"Failed to delete file from local storage: {file_id}, error: {e}")
        
        # Remove from metadata store
        del self._files[file_id]
        
        # Fixed: Persist metadata to disk
        self._save_metadata()
        
        return True


# Global vault service instance
_vault_service: Optional[VaultService] = None


def get_vault_service() -> VaultService:
    """Get or create vault service instance."""
    global _vault_service
    if _vault_service is None:
        _vault_service = VaultService()
    return _vault_service

