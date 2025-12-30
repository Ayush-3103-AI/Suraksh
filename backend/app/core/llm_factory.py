"""
LLM Factory for GraphRAG
Supports OpenRouter (DeepSeek) and OpenAI with LlamaIndex integration.
"""

from typing import Optional

# Fixed: Corrected import path for LLM
from llama_index.core.llms import LLM
from llama_index.llms.openai import OpenAI
from openai import OpenAI as OpenAIClient

from app.core.config import settings


def get_llm() -> LLM:
    """
    Factory function to create LLM instance based on configuration.
    Uses OpenRouter API with DeepSeek model by default.
    
    Returns:
        LLM instance (OpenAI-compatible via OpenRouter)
        
    Raises:
        ValueError: If provider is not supported or API key is missing
    """
    provider = settings.LLM_PROVIDER.lower()
    
    # Get API key
    api_key = settings.LLM_API_KEY
    if not api_key:
        raise ValueError(
            "LLM API key is required. Set LLM_API_KEY in environment variables."
        )
    
    # Get model name (default to DeepSeek R1)
    model_name = settings.LLM_MODEL or "deepseek/deepseek-r1-0528:free"
    
    # OpenRouter uses OpenAI-compatible API
    if provider in ["openai", "openrouter", "deepseek"]:
        # Configure OpenAI client to use OpenRouter base URL
        base_url = settings.OPENROUTER_BASE_URL or "https://openrouter.ai/api/v1"
        
        # Create OpenAI client with OpenRouter configuration
        client_kwargs = {
            "api_key": api_key,
            "base_url": base_url,
        }
        
        # Add OpenRouter-specific headers if using OpenRouter
        if base_url == "https://openrouter.ai/api/v1":
            client_kwargs["default_headers"] = {
                "HTTP-Referer": settings.OPENROUTER_HTTP_REFERER or "https://suraksh.local",
                "X-Title": settings.OPENROUTER_SITE_NAME or "Suraksh Portal",
            }
        
        # Create OpenAI client instance
        openai_client = OpenAIClient(**client_kwargs)
        
        # Pass client to LlamaIndex OpenAI wrapper
        return OpenAI(
            client=openai_client,
            model=model_name,
            temperature=settings.LLM_TEMPERATURE,
        )
    
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. Supported providers: 'openai', 'openrouter', 'deepseek'"
        )


def get_llm_for_embedding() -> Optional[LLM]:
    """
    Get LLM instance for embedding generation (if needed).
    For most cases, this will be the same as the main LLM.
    
    Returns:
        LLM instance or None if not needed
    """
    return get_llm()

