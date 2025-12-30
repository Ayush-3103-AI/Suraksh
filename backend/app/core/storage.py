"""
MinIO Object Storage Client
MinIO client initialization and bucket management.
"""

import logging
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global MinIO client instance
_minio_client: Optional[Minio] = None


def get_minio_client() -> Minio:
    """
    Get or create MinIO client instance.
    
    Returns:
        MinIO client instance
        
    Raises:
        RuntimeError: If MinIO client cannot be initialized
    """
    global _minio_client
    
    if _minio_client is None:
        try:
            # Parse endpoint (host:port)
            endpoint_parts = settings.MINIO_ENDPOINT.split(":")
            host = endpoint_parts[0]
            port = int(endpoint_parts[1]) if len(endpoint_parts) > 1 else (443 if settings.MINIO_SECURE else 9000)
            
            _minio_client = Minio(
                endpoint=f"{host}:{port}",
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            logger.info(f"MinIO client initialized: {host}:{port}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize MinIO client: {e}") from e
    
    return _minio_client


def ensure_minio_bucket(bucket_name: Optional[str] = None) -> None:
    """
    Ensure MinIO bucket exists, create if it doesn't.
    Note: MinIO client is synchronous, so this function is not async.
    
    Args:
        bucket_name: Bucket name (defaults to settings.MINIO_BUCKET_NAME)
        
    Raises:
        RuntimeError: If bucket cannot be created or accessed
    """
    if bucket_name is None:
        bucket_name = settings.MINIO_BUCKET_NAME
    
    client = get_minio_client()
    
    try:
        # Check if bucket exists
        if not client.bucket_exists(bucket_name):
            # Create bucket if it doesn't exist
            client.make_bucket(bucket_name)
            logger.info(f"✅ Created MinIO bucket: {bucket_name}")
        else:
            logger.info(f"✅ MinIO bucket exists: {bucket_name}")
    except S3Error as e:
        error_msg = f"MinIO S3 error: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(f"Failed to ensure MinIO bucket exists: {error_msg}") from e
    except Exception as e:
        error_msg = f"MinIO connection error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(f"Failed to access MinIO: {error_msg}") from e


def verify_minio_connection() -> bool:
    """
    Verify MinIO connection is working.
    Note: MinIO client is synchronous, so this function is not async.
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        client = get_minio_client()
        # Try to list buckets to verify connection
        client.list_buckets()
        return True
    except Exception as e:
        logger.warning(f"MinIO connection verification failed: {e}")
        return False

