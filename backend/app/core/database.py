"""
Database Connection Clients
Neo4j and Qdrant client initialization and management.
"""

from typing import Optional, TYPE_CHECKING

from neo4j import AsyncGraphDatabase
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import settings

if TYPE_CHECKING:
    from neo4j import AsyncDriver

# Global client instances
_neo4j_driver: Optional["AsyncDriver"] = None
_qdrant_client: Optional[AsyncQdrantClient] = None


def get_neo4j_driver() -> "AsyncDriver":
    """
    Get or create Neo4j async driver instance.
    
    Returns:
        Neo4j async driver instance
        
    Raises:
        RuntimeError: If Neo4j driver cannot be initialized
    """
    global _neo4j_driver
    
    if _neo4j_driver is None:
        try:
            _neo4j_driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Neo4j driver: {e}") from e
    
    return _neo4j_driver


async def close_neo4j_driver() -> None:
    """Close Neo4j driver connection."""
    global _neo4j_driver
    
    if _neo4j_driver is not None:
        await _neo4j_driver.close()
        _neo4j_driver = None


def get_qdrant_client() -> AsyncQdrantClient:
    """
    Get or create Qdrant async client instance.
    
    Returns:
        Qdrant async client instance
        
    Raises:
        RuntimeError: If Qdrant client cannot be initialized
    """
    global _qdrant_client
    
    if _qdrant_client is None:
        try:
            _qdrant_client = AsyncQdrantClient(
                url=settings.QDRANT_URL,
                check_compatibility=False,  # Suppress version warning for Docker image compatibility
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Qdrant client: {e}") from e
    
    return _qdrant_client


async def ensure_qdrant_collection(collection_name: Optional[str] = None) -> None:
    """
    Ensure Qdrant collection exists, create if it doesn't.
    
    Args:
        collection_name: Collection name (defaults to settings.QDRANT_COLLECTION_NAME)
        
    Raises:
        RuntimeError: If collection cannot be created or accessed
    """
    if collection_name is None:
        collection_name = settings.QDRANT_COLLECTION_NAME
    
    client = get_qdrant_client()
    
    try:
        # Check if collection exists
        collections = await client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if collection_name not in collection_names:
            # Create collection if it doesn't exist
            # Using 1536 dimensions (OpenAI text-embedding-3-small default)
            from app.core.embeddings import get_embedding_service
            embedding_service = get_embedding_service()
            dimension = embedding_service.get_embedding_dimension()
            
            await client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE,
                ),
            )
            print(f"[OK] Created Qdrant collection: {collection_name}")
        else:
            print(f"[OK] Qdrant collection exists: {collection_name}")
    except Exception as e:
        raise RuntimeError(f"Failed to ensure Qdrant collection exists: {e}") from e


async def verify_neo4j_connection() -> bool:
    """
    Verify Neo4j connection is working.
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        driver = get_neo4j_driver()
        async with driver.session() as session:
            result = await session.run("RETURN 1 as test")
            await result.single()
        return True
    except Exception:
        return False


async def verify_qdrant_connection() -> bool:
    """
    Verify Qdrant connection is working.
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        client = get_qdrant_client()
        await client.get_collections()
        return True
    except Exception:
        return False

