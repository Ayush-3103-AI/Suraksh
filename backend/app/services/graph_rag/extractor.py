"""
GraphRAG Extraction Service
Handles entity and relation extraction from text using LLM.

Implements strict type hints per Cursor Rule guidelines.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

# Fixed: Corrected import path for LLM
from llama_index.core.llms import LLM

from app.services.graph_rag.ontology import get_extraction_prompt
from app.services.graph_rag.llm_setup import get_extraction_llm

logger = logging.getLogger(__name__)


class GraphRAGExtractor:
    """
    GraphRAG extractor for extracting entities and relations from text.
    Uses LLM with strict ontology enforcement.
    """
    
    def __init__(self, llm: Optional[LLM] = None):
        """
        Initialize GraphRAG extractor.
        
        Args:
            llm: LLM instance (defaults to extraction LLM from config)
        """
        try:
            self.llm = llm or get_extraction_llm()
            # Fixed: Validate LLM was initialized successfully
            if self.llm is None:
                logger.error("[EXTRACT] Failed to initialize LLM - get_extraction_llm() returned None")
            else:
                logger.info(f"[EXTRACT] LLM initialized successfully: {type(self.llm).__name__}")
        except Exception as e:
            logger.error(f"[EXTRACT] Failed to initialize LLM: {type(e).__name__}: {e}", exc_info=True)
            self.llm = None
    
    async def extract_from_text(
        self,
        text: str,
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract entities and relations from text.
        
        Args:
            text: Input text to extract from
            document_id: Optional document ID to link entities
            
        Returns:
            Dictionary with 'entities' and 'relations' lists
        """
        # Fixed: Add logging to track extraction process
        text_preview = text[:200] + "..." if len(text) > 200 else text
        logger.info(f"[EXTRACT] Starting extraction: document_id={document_id}, text_length={len(text)}, preview={text_preview}")
        
        # Build extraction prompt
        prompt = get_extraction_prompt() + f"\n\nTEXT:\n{text}\n\n"
        
        if document_id:
            prompt += f"\nDOCUMENT_ID: {document_id}\n"
        
        # Call LLM for extraction
        response_text = None
        try:
            # Fixed: Check if LLM is available with detailed error
            if self.llm is None:
                error_msg = "[EXTRACT] LLM instance is None - cannot perform extraction. Check LLM_API_KEY configuration."
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            logger.debug(f"[EXTRACT] Calling LLM with prompt length: {len(prompt)}")
            
            # Try async first, fallback to sync
            if hasattr(self.llm, "acomplete"):
                logger.debug("[EXTRACT] Using async LLM call (acomplete)")
                response = await self.llm.acomplete(prompt)
            else:
                logger.debug("[EXTRACT] Using sync LLM call (complete) via asyncio")
                import asyncio
                response = await asyncio.to_thread(self.llm.complete, prompt)
            
            # Fixed: Extract text from response object properly (LlamaIndex CompletionResponse has .text attribute)
            if hasattr(response, "text"):
                response_text = response.text
            elif hasattr(response, "delta"):
                # Handle streaming response
                response_text = "".join([str(d) for d in response.delta])
            else:
                response_text = str(response)
            
            logger.debug(f"[EXTRACT] LLM response received, length: {len(response_text)}, preview: {response_text[:200]}")
            
            # Fixed: Handle empty or None response
            if not response_text or not response_text.strip():
                logger.warning("[EXTRACT] LLM returned empty response")
                return {"entities": [], "relations": []}
            
            # Parse JSON response
            # LLM might wrap JSON in markdown code blocks or add explanations
            original_response = response_text
            
            # Fixed: More robust JSON extraction
            # Try to find JSON object in response
            json_start = -1
            json_end = -1
            
            # Look for JSON object start
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end == -1:
                    json_end = len(response_text)
                response_text = response_text[json_start:json_end].strip()
                logger.debug(f"[EXTRACT] Extracted JSON from markdown code block")
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                if json_end == -1:
                    json_end = len(response_text)
                response_text = response_text[json_start:json_end].strip()
                logger.debug(f"[EXTRACT] Extracted JSON from code block")
            elif "{" in response_text:
                # Try to find JSON object directly
                json_start = response_text.find("{")
                # Find matching closing brace
                brace_count = 0
                for i, char in enumerate(response_text[json_start:], json_start):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                if json_end > json_start:
                    response_text = response_text[json_start:json_end].strip()
                    logger.debug(f"[EXTRACT] Extracted JSON object from response")
            
            # Fixed: Validate JSON before parsing
            if not response_text.strip():
                logger.warning(f"[EXTRACT] No JSON content found in response. Original response: {original_response[:500]}")
                return {"entities": [], "relations": []}
            
            # Parse JSON with error handling
            logger.debug(f"[EXTRACT] Parsing JSON, length: {len(response_text)}")
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError as parse_error:
                # Try to fix common JSON issues
                # Remove trailing commas
                fixed_json = re.sub(r',\s*}', '}', response_text)
                fixed_json = re.sub(r',\s*]', ']', fixed_json)
                try:
                    result = json.loads(fixed_json)
                    logger.debug(f"[EXTRACT] Fixed JSON parsing issues")
                except:
                    raise parse_error
            logger.debug(f"[EXTRACT] JSON parsed successfully")
            
            # Validate structure
            entities = result.get("entities", [])
            relations = result.get("relations", [])
            
            # Fixed: Log extraction results with more detail
            logger.info(f"[EXTRACT] Extraction successful: {len(entities)} entities, {len(relations)} relations extracted")
            if len(entities) == 0 and len(relations) == 0:
                logger.warning(f"[EXTRACT] WARNING: No entities or relations extracted from text. This may indicate:")
                logger.warning(f"[EXTRACT] 1. Text content is not suitable for extraction (too short, no named entities)")
                logger.warning(f"[EXTRACT] 2. LLM response format issue (check logs above for JSON parsing errors)")
                logger.warning(f"[EXTRACT] 3. Extraction prompt is too strict for this content")
                logger.warning(f"[EXTRACT] Full LLM response (first 2000 chars): {original_response[:2000]}")
            if len(entities) > 0:
                logger.info(f"[EXTRACT] Sample entities: {[e.get('id', e.get('properties', {}).get('name', 'unknown')) for e in entities[:3]]}")
            if len(relations) > 0:
                sample_relations = [
                    f"{r.get('source')} -> {r.get('target')} ({r.get('type')})"
                    for r in relations[:3]
                ]
                logger.info(f"[EXTRACT] Sample relations: {sample_relations}")
            
            # Add document_id to entities if provided
            if document_id:
                for entity in entities:
                    if "properties" not in entity:
                        entity["properties"] = {}
                    entity["properties"]["document_id"] = document_id
            
            return {
                "entities": entities,
                "relations": relations,
            }
        except json.JSONDecodeError as e:
            # Fixed: Enhanced JSON parsing error logging
            logger.error(f"[EXTRACT] Failed to parse LLM extraction response as JSON: {e}")
            logger.error(f"[EXTRACT] JSON error at position {e.pos if hasattr(e, 'pos') else 'unknown'}")
            logger.error(f"[EXTRACT] Response text (first 1000 chars): {response_text[:1000] if response_text else 'None'}")
            logger.error(f"[EXTRACT] Response text (last 500 chars): {response_text[-500:] if response_text and len(response_text) > 500 else response_text}")
            return {"entities": [], "relations": []}
        except Exception as e:
            # Fixed: Enhanced exception logging
            logger.error(f"[EXTRACT] Error during extraction: {type(e).__name__}: {e}", exc_info=True)
            if response_text:
                logger.error(f"[EXTRACT] Response text at error: {response_text[:500]}")
            return {"entities": [], "relations": []}

