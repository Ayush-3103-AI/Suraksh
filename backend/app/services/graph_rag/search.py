"""
GraphRAG Search Service
Hybrid search combining vector search (Qdrant) and graph traversal (Neo4j).

Implements hybrid retrieval with configurable weights per Cursor Rule guidelines:
- vector_weight: Weight for semantic vector search (default: 0.5)
- graph_weight: Weight for graph traversal (default: 0.5)
"""

import logging
from typing import Any, Dict, List, Optional

# Fixed: Corrected import path for LLM (changed from .types to direct import)
from llama_index.core.llms import LLM

from app.core.config import settings
from app.core.database import get_neo4j_driver, get_qdrant_client
from app.services.graph_rag.llm_setup import get_synthesis_llm
from app.services.graph_rag.ontology import get_synthesis_prompt

logger = logging.getLogger(__name__)


class HybridSearchService:
    """
    Hybrid search service combining vector and graph search.
    
    Implements hybrid retrieval with configurable weights per Cursor Rule:
    - Balances semantic finding (vector) with structural reasoning (graph)
    """
    
    def __init__(
        self,
        synthesis_llm: Optional[LLM] = None,
        vector_weight: float = 0.5,
        graph_weight: float = 0.5,
    ):
        """
        Initialize hybrid search service.
        
        Args:
            synthesis_llm: LLM for answer synthesis (optional)
            vector_weight: Weight for vector search results (default: 0.5)
            graph_weight: Weight for graph traversal results (default: 0.5)
        """
        self.synthesis_llm = synthesis_llm or get_synthesis_llm()
        # Normalize weights to sum to 1.0
        total_weight = vector_weight + graph_weight
        if total_weight > 0:
            self.vector_weight = vector_weight / total_weight
            self.graph_weight = graph_weight / total_weight
        else:
            self.vector_weight = 0.5
            self.graph_weight = 0.5
    
    async def search(
        self,
        query: str,
        user_clearance: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Perform hybrid search: vector search + graph traversal.
        
        Implements hybrid retrieval per Cursor Rule guidelines:
        - Combines semantic finding (vector) with structural reasoning (graph)
        - Uses configurable weights to balance results
        
        Args:
            query: User query string
            user_clearance: User clearance level for filtering
            top_k: Number of top results to retrieve
            
        Returns:
            Dictionary with search results, graph path, and synthesized answer
        """
        # Step 1: Vector search in Qdrant (semantic similarity)
        vector_results = await self._vector_search(query, top_k, user_clearance)
        
        # Step 2: Extract entities from query using LLM (enhanced extraction)
        entities = await self._extract_entities_from_query_llm(query)
        # Also extract from vector results
        entities.extend(self._extract_entities_from_results(vector_results))
        
        # Step 3: Graph traversal in Neo4j (structural reasoning)
        graph_path = await self._graph_traversal(entities, user_clearance)
        
        # Step 4: Combine results with weights
        combined_context = self._combine_results(
            vector_results,
            graph_path,
            vector_weight=self.vector_weight,
            graph_weight=self.graph_weight,
        )
        
        # Step 5: Synthesize answer
        answer = await self._synthesize_answer(query, combined_context, graph_path)
        
        return {
            "query": query,
            "answer": answer,
            "vector_results": vector_results,
            "graph_path": graph_path,
            "entities_found": entities,
            "weights": {
                "vector": self.vector_weight,
                "graph": self.graph_weight,
            },
        }
    
    async def _vector_search(
        self,
        query: str,
        top_k: int,
        user_clearance: str,
    ) -> List[Dict[str, Any]]:
        """
        Perform vector search in Qdrant.
        
        Args:
            query: Search query
            top_k: Number of results
            user_clearance: User clearance level
            
        Returns:
            List of relevant document chunks
        """
        try:
            # Get Qdrant client
            client = get_qdrant_client()
            
            # Generate query embedding
            from app.core.embeddings import get_embedding_service
            embedding_service = get_embedding_service()
            query_embedding = await embedding_service.get_embedding(query)
            
            # Perform vector search
            from app.core.config import settings
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Build clearance filter
            clearance_order = {"L1": 1, "L2": 2, "L3": 3}
            user_level = clearance_order.get(user_clearance, 3)
            
            # Filter: user can access files at their level or lower
            # L1 can access L1, L2, L3; L2 can access L2, L3; L3 can only access L3
            allowed_levels = [level for level, order in clearance_order.items() if order >= user_level]
            
            # Search with filter (simplified - Qdrant filter syntax may vary)
            # For now, search without filter and filter results in Python
            search_result = await client.search(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query_vector=query_embedding,
                limit=top_k * 2,  # Get more results to filter
            )
            
            # Filter by clearance level in Python
            filtered_results = []
            for hit in search_result:
                payload = hit.payload or {}
                hit_clearance = payload.get("clearance_level", "L3")
                hit_level = clearance_order.get(hit_clearance, 3)
                
                if hit_level >= user_level:
                    filtered_results.append(hit)
                    if len(filtered_results) >= top_k:
                        break
            
            search_result = filtered_results
            
            # Format results
            results = []
            for hit in search_result:
                payload = hit.payload or {}
                results.append({
                    "text": payload.get("text", ""),
                    "document_id": payload.get("document_id", ""),
                    "clearance_level": payload.get("clearance_level", ""),
                    "metadata": payload.get("metadata", {}),
                    "score": hit.score,
                })
            
            return results
        except Exception as e:
            logger.error(f"Error in vector search: {e}", exc_info=True)
            return []
    
    async def _extract_entities_from_query_llm(self, query: str) -> List[str]:
        """
        Extract entity names from query using LLM (enhanced extraction per Cursor Rule).
        
        Args:
            query: User query
            
        Returns:
            List of potential entity names
        """
        try:
            # Use LLM to extract entities from query
            from app.services.graph_rag.llm_setup import get_extraction_llm
            extraction_llm = get_extraction_llm()
            
            prompt = f"""Extract all entity names (people, organizations, locations, events) from the following query.
Return only a JSON array of entity names, nothing else.

Query: {query}

Return format: ["entity1", "entity2", ...]"""
            
            if hasattr(extraction_llm, "acomplete"):
                response = await extraction_llm.acomplete(prompt)
            else:
                import asyncio
                response = await asyncio.to_thread(extraction_llm.complete, prompt)
            
            response_text = str(response).strip()
            # Parse JSON array
            import json
            if response_text.startswith("["):
                entities = json.loads(response_text)
                return entities[:10]  # Limit to top 10
        except Exception as e:
            logger.warning(f"LLM entity extraction failed, falling back to simple extraction: {e}")
        
        # Fallback to simple extraction
        return self._extract_entities_from_query_simple(query)
    
    def _extract_entities_from_query_simple(self, query: str) -> List[str]:
        """
        Extract entity names from query (simple keyword extraction - fallback).
        
        Args:
            query: User query
            
        Returns:
            List of potential entity names
        """
        words = query.split()
        # Filter out common words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "how", "what", "where", "when", "who", "why"}
        entities = [w for w in words if w.lower() not in stop_words and len(w) > 2]
        return entities[:5]  # Limit to top 5
    
    def _extract_entities_from_results(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Extract entities from vector search results.
        
        Args:
            results: Vector search results
            
        Returns:
            List of entity names
        """
        entities = []
        for result in results:
            # Extract entities from result text/metadata
            # Placeholder implementation
            pass
        return entities
    
    async def _graph_traversal(
        self,
        entities: List[str],
        user_clearance: str,
    ) -> Dict[str, Any]:
        """
        Perform graph traversal in Neo4j to find connections.
        
        Args:
            entities: List of entity names to search for
            user_clearance: User clearance level
            
        Returns:
            Graph traversal path information
        """
        try:
            driver = get_neo4j_driver()
            
            # Build Cypher query to find paths between entities
            if len(entities) >= 2:
                # Find shortest path between first two entities
                query = """
                MATCH (a), (b)
                WHERE a.name = $entity1 OR a.id = $entity1
                  AND b.name = $entity2 OR b.id = $entity2
                MATCH p = shortestPath((a)-[*..10]-(b))
                RETURN p
                LIMIT 1
                """
                
                async with driver.session() as session:
                    result = await session.run(
                        query,
                        entity1=entities[0],
                        entity2=entities[1] if len(entities) > 1 else entities[0],
                    )
                    record = await result.single()
                    
                    if record:
                        path = record["p"]
                        return {
                            "path_found": True,
                            "path_length": len(path.relationships) if path else 0,
                            "entities": [n.get("name", n.get("id", "")) for n in path.nodes] if path else [],
                        }
            
            return {
                "path_found": False,
                "path_length": 0,
                "entities": [],
            }
        except Exception as e:
            print(f"Error in graph traversal: {e}")
            return {
                "path_found": False,
                "path_length": 0,
                "entities": [],
                "error": str(e),
            }
    
    def _combine_results(
        self,
        vector_results: List[Dict[str, Any]],
        graph_path: Dict[str, Any],
        vector_weight: float,
        graph_weight: float,
    ) -> str:
        """
        Combine vector and graph results with weights.
        
        Args:
            vector_results: Vector search results
            graph_path: Graph traversal path
            vector_weight: Weight for vector results
            graph_weight: Weight for graph results
            
        Returns:
            Combined context string
        """
        context_parts = []
        
        # Add vector results (weighted)
        if vector_results and vector_weight > 0:
            vector_context = self._format_vector_results(vector_results)
            context_parts.append(f"=== VECTOR SEARCH RESULTS (weight: {vector_weight:.2f}) ===\n{vector_context}")
        
        # Add graph path (weighted)
        if graph_path.get("path_found") and graph_weight > 0:
            graph_desc = f"Graph path found: {graph_path.get('path_length', 0)} relationships connecting: {', '.join(graph_path.get('entities', []))}"
            context_parts.append(f"=== GRAPH TRAVERSAL (weight: {graph_weight:.2f}) ===\n{graph_desc}")
        
        return "\n\n".join(context_parts) if context_parts else "No relevant context found."
    
    def _format_vector_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format vector search results as context string.
        
        Args:
            results: Vector search results
            
        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant documents found."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            text = result.get("text", result.get("content", ""))
            metadata = result.get("metadata", {})
            filename = metadata.get("filename", "Unknown")
            
            context_parts.append(f"Document {i} ({filename}):\n{text}\n")
        
        return "\n".join(context_parts)
    
    async def _synthesize_answer(
        self,
        query: str,
        combined_context: str,
        graph_path: Dict[str, Any],
    ) -> str:
        """
        Synthesize answer from combined context (vector + graph) using LLM.
        
        Args:
            query: Original user query
            combined_context: Combined context from vector search and graph traversal
            graph_path: Graph traversal path information
            
        Returns:
            Synthesized answer
        """
        # Format graph path description
        if graph_path.get("path_found"):
            path_desc = f"Found path with {graph_path['path_length']} relationships connecting: {', '.join(graph_path.get('entities', []))}"
        else:
            path_desc = "No direct path found in knowledge graph."
        
        # Build synthesis prompt with combined context
        prompt = get_synthesis_prompt(query, combined_context, path_desc)
        
        try:
            # Try async first, fallback to sync
            if hasattr(self.synthesis_llm, "acomplete"):
                response = await self.synthesis_llm.acomplete(prompt)
            else:
                import asyncio
                response = await asyncio.to_thread(self.synthesis_llm.complete, prompt)
            return str(response).strip()
        except Exception as e:
            logger.error(f"Error generating answer: {e}", exc_info=True)
            return f"Error generating answer: {str(e)}"

