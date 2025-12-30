"""
Suraksh Backend Configuration
Pydantic v2 Settings with environment variable loading.
"""

from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with strict validation."""
    
    model_config = SettingsConfigDict(
        # Fixed: Use absolute path to .env file to ensure it's found regardless of working directory
        env_file=str(Path(__file__).parent.parent / ".env") if (Path(__file__).parent.parent / ".env").exists() else ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    APP_NAME: str = "Suraksh Backend API"
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    
    # CORS
    # Fixed: Added localhost:3002 to support frontend running on different port
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3002", "http://localhost:8000"],
        description="Allowed CORS origins",
    )
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://suraksh:suraksh_pass@localhost:5432/suraksh_db",
        description="PostgreSQL connection string",
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    
    # Neo4j
    NEO4J_URI: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j Bolt connection URI",
    )
    NEO4J_USER: str = Field(default="neo4j", description="Neo4j username")
    NEO4J_PASSWORD: str = Field(default="", description="Neo4j password")
    
    # Qdrant
    QDRANT_URL: str = Field(
        default="http://localhost:6333",
        description="Qdrant vector database URL",
    )
    QDRANT_COLLECTION_NAME: str = Field(
        default="suraksh_documents",
        description="Default Qdrant collection name",
    )
    
    # MinIO Object Storage
    MINIO_ENDPOINT: str = Field(
        default="localhost:9000",
        description="MinIO endpoint (host:port)",
    )
    MINIO_ACCESS_KEY: str = Field(
        default="minioadmin",
        description="MinIO access key",
    )
    MINIO_SECRET_KEY: str = Field(
        default="minioadmin123",
        description="MinIO secret key",
    )
    MINIO_BUCKET_NAME: str = Field(
        default="suraksh-vault",
        description="MinIO bucket name for file storage",
    )
    MINIO_SECURE: bool = Field(
        default=False,
        description="Use HTTPS for MinIO (set to True in production)",
    )
    
    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production-use-strong-random-key",
        description="JWT secret key (MUST be changed in production)",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT access token expiration in minutes",
    )
    
    # LLM Configuration (for GraphRAG)
    LLM_PROVIDER: str = Field(
        default="openrouter",
        description="LLM provider: 'openrouter', 'openai', or 'deepseek'",
    )
    LLM_MODEL: str = Field(
        default="deepseek/deepseek-r1-0528:free",
        description="LLM model name (e.g., 'deepseek/deepseek-r1-0528:free', 'gpt-4')",
    )
    LLM_API_KEY: str = Field(
        default="",
        description="LLM API key (OpenRouter/OpenAI/etc.)",
    )
    LLM_TEMPERATURE: float = Field(
        default=0.1,
        description="LLM temperature for deterministic extraction",
    )
    
    # OpenRouter Configuration
    OPENROUTER_BASE_URL: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL",
    )
    OPENROUTER_HTTP_REFERER: str = Field(
        default="https://suraksh.local",
        description="HTTP Referer for OpenRouter rankings",
    )
    OPENROUTER_SITE_NAME: str = Field(
        default="Suraksh Portal",
        description="Site name for OpenRouter rankings",
    )


# Global settings instance
settings = Settings()

