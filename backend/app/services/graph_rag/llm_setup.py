"""
LLM Setup for GraphRAG Services
Initializes LLM instances for graph extraction and query synthesis.
"""

# Fixed: Corrected import path for LLM
from llama_index.core.llms import LLM

from app.core.llm_factory import get_llm


def get_extraction_llm() -> LLM:
    """
    Get LLM instance for graph extraction (entity/relation extraction).
    
    Returns:
        LLM instance configured for extraction tasks
    """
    return get_llm()


def get_synthesis_llm() -> LLM:
    """
    Get LLM instance for query synthesis (generating answers from graph + context).
    
    Returns:
        LLM instance configured for synthesis tasks
    """
    # For Phase 1, use the same LLM for both extraction and synthesis
    # In future phases, can configure different models/temperatures
    return get_llm()

