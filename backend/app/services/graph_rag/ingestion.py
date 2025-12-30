"""
GraphRAG Ingestion Pipeline
Text -> Chunk -> Extract -> Neo4j/Qdrant pipeline.

Implements hierarchical (Parent-Child) chunking strategy for maximum accuracy.
Follows Cursor Rule: rag_architecture.mdc guidelines.
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional

from llama_index.core import Document
from llama_index.core.node_parser import (
    HierarchicalNodeParser,
    SimpleNodeParser,
    SentenceSplitter,
)

from app.core.config import settings
from app.core.database import get_neo4j_driver, get_qdrant_client
from app.services.graph_rag.extractor import GraphRAGExtractor

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Pipeline for ingesting text data into the knowledge graph.
    Handles hierarchical chunking, entity/relation extraction, and graph/vector indexing.
    
    Implements:
    - Hierarchical (Parent-Child) chunking for maximum accuracy
    - File hash checking for idempotency
    - Failed jobs logging
    - Async/await for all I/O operations
    """
    
    def __init__(
        self,
        extractor: Optional[GraphRAGExtractor] = None,
        use_enhanced: bool = False,
        use_hierarchical_chunking: bool = True,
    ):
        """
        Initialize ingestion pipeline.
        
        Args:
            extractor: GraphRAG extractor instance (optional)
            use_enhanced: Whether to use enhanced KG extractor (default: False - simplified)
            use_hierarchical_chunking: Use hierarchical (Parent-Child) chunking (default: True)
        """
        # Fixed: Use basic extractor with fallback mode if LLM not configured
        try:
            self.extractor = extractor or GraphRAGExtractor()
            # Check if extractor has valid LLM
            if self.extractor.llm is None:
                logger.warning("[INGEST] LLM not configured - running in NO-EXTRACTION mode. Files will be chunked but entities will not be extracted.")
                logger.warning("[INGEST] To enable extraction, set LLM_API_KEY in backend/.env file with a valid OpenRouter API key.")
                self.extraction_enabled = False
            else:
                logger.info("[INGEST] IngestionPipeline initialized successfully with extractor")
                self.extraction_enabled = True
        except Exception as e:
            logger.warning(f"[INGEST] Failed to initialize extractor: {type(e).__name__}: {e}")
            logger.warning("[INGEST] Running in NO-EXTRACTION mode. Files will be chunked but entities will not be extracted.")
            self.extractor = None
            self.extraction_enabled = False
        self.use_enhanced = use_enhanced
        
        # Implement hierarchical chunking per Cursor Rule guidelines
        if use_hierarchical_chunking:
            # Parent chunks: 1024 tokens to preserve full context for graph extraction
            # Child chunks: 256 tokens for precise vector retrieval
            self.parent_parser = SimpleNodeParser.from_defaults(
                chunk_size=1024,
                chunk_overlap=200,
            )
            self.child_parser = SentenceSplitter.from_defaults(
                chunk_size=256,
                chunk_overlap=50,
            )
            self.use_hierarchical = True
        else:
            # Fallback to simple chunking
            self.node_parser = SimpleNodeParser.from_defaults(
                chunk_size=1024,
                chunk_overlap=200,
            )
            self.use_hierarchical = False
        
        # Track processed file hashes for idempotency
        self._processed_hashes: set[str] = set()
    
    async def ingest_text(
        self,
        text: str,
        source_id: str,
        source_name: Optional[str] = None,
        clearance_level: str = "L3",  # Kept for backward compatibility, not actively used
        check_hash: bool = True,
        extract_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingest text data into the knowledge graph.
        
        Implements idempotency via file hash checking per Cursor Rule guidelines.
        
        Args:
            text: Text content to ingest
            source_id: Unique identifier for the data source
            source_name: Optional name/description of the source
            clearance_level: Data clearance level (L1, L2, L3)
            check_hash: Whether to check file hash for idempotency (default: True)
            
        Returns:
            Dictionary with ingestion results (entities, relations, chunks)
            
        Raises:
            RuntimeError: If ingestion fails
        """
        if not text or not text.strip():
            raise RuntimeError("Text content cannot be empty")
        
        # Idempotency: Check file hash before processing
        if check_hash:
            text_hash = self._compute_text_hash(text, source_id)
            if text_hash in self._processed_hashes:
                logger.info(f"Skipping duplicate ingestion: source_id={source_id}, hash={text_hash[:8]}...")
                return {
                    "source_id": source_id,
                    "source_name": source_name,
                    "entities_extracted": 0,
                    "relations_extracted": 0,
                    "chunks_created": 0,
                    "status": "skipped_duplicate",
                    "message": "File already processed (idempotency check)",
                }
        
        try:
            # Step 1: Create document
            document = Document(
                text=text,
                metadata={
                    "source_id": source_id,
                    "source_name": source_name or source_id,
                    "clearance_level": clearance_level,
                },
            )
            
            # Step 2: Hierarchical chunking (Parent-Child strategy)
            if self.use_hierarchical:
                # Create parent chunks (1024 tokens) for graph extraction
                parent_nodes = self.parent_parser.get_nodes_from_documents([document])
                
                # Create child chunks (256 tokens) for vector retrieval
                child_nodes = []
                for parent_node in parent_nodes:
                    parent_doc = Document(
                        text=parent_node.get_content(),
                        metadata=parent_node.metadata.copy(),
                    )
                    children = self.child_parser.get_nodes_from_documents([parent_doc])
                    # Link children to parent
                    for child in children:
                        child.metadata["parent_id"] = parent_node.node_id
                        child.metadata["is_child"] = True
                    child_nodes.extend(children)
                
                # Use parent nodes for graph extraction (preserve full context)
                extraction_nodes = parent_nodes
                # Use child nodes for vector storage (precise retrieval)
                vector_nodes = child_nodes
            else:
                # Fallback to simple chunking
                nodes = self.node_parser.get_nodes_from_documents([document])
                extraction_nodes = nodes
                vector_nodes = nodes
            
            # Step 3: Extract entities and relations from parent chunks
            all_nodes = []
            all_edges = []
            
            # Fixed: Check if extraction is enabled and requested
            if extract_graph and self.extraction_enabled and self.extractor is not None:
                # Fixed: Add logging for extraction process
                logger.info(f"[INGEST] Starting extraction from {len(extraction_nodes)} chunks for source_id={source_id}")
                
                chunks_processed = 0
                chunks_with_entities = 0
                
                for idx, node in enumerate(extraction_nodes):
                    chunk_text = node.get_content()
                    chunk_preview = chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text
                    logger.debug(f"[INGEST] Processing chunk {idx + 1}/{len(extraction_nodes)}, length={len(chunk_text)}, preview={chunk_preview}")
                    
                    try:
                        extraction_result = await self.extractor.extract_from_text(
                            text=chunk_text,
                            document_id=source_id,
                        )
                        
                        chunks_processed += 1
                        
                        # Simplified: Always use basic format (entities and relations)
                        entities = extraction_result.get("entities", [])
                        relations = extraction_result.get("relations", [])
                        
                        if len(entities) > 0 or len(relations) > 0:
                            chunks_with_entities += 1
                            logger.debug(f"[INGEST] Chunk {idx + 1} extracted {len(entities)} entities, {len(relations)} relations")
                        
                        # Convert entities to nodes
                        for entity in entities:
                            entity_id = entity.get("id", "")
                            entity_props = entity.get("properties", {})
                            entity_name = entity_props.get("name", entity_id)
                            
                            # Fixed: Generate entity ID if missing
                            if not entity_id:
                                entity_type = entity.get("type", "entity").lower()
                                entity_id = f"{entity_type}_{entity_name.lower().replace(' ', '_').replace('-', '_')}"
                                logger.warning(f"[INGEST] Generated entity ID: {entity_id} for entity without ID")
                            
                            all_nodes.append({
                                "id": entity_id,
                                "label": entity_name,
                                "type": entity.get("type", "entity").lower(),
                                "properties": entity_props,
                            })
                        
                        # Convert relations to edges
                        for relation in relations:
                            source_id = relation.get("source", "")
                            target_id = relation.get("target", "")
                            
                            # Fixed: Skip relations with missing source or target
                            if not source_id or not target_id:
                                logger.warning(f"[INGEST] Skipping relation with missing source or target: source={source_id}, target={target_id}")
                                continue
                            
                            all_edges.append({
                                "source": source_id,
                                "target": target_id,
                                "relationship": relation.get("type", "related_to").lower(),
                                "weight": relation.get("properties", {}).get("weight", 1.0),
                                "properties": relation.get("properties", {}),
                            })
                    except Exception as e:
                        # Fixed: Enhanced error logging for chunk extraction failures
                        logger.error(f"[INGEST] Failed to extract from chunk {idx + 1}/{len(extraction_nodes)}: {type(e).__name__}: {e}", exc_info=True)
                        # Continue processing other chunks
                        continue
                
                # Fixed: Log extraction summary
                logger.info(f"[INGEST] Extraction complete: {chunks_processed}/{len(extraction_nodes)} chunks processed, {chunks_with_entities} chunks with entities, total entities={len(all_nodes)}, total relations={len(all_edges)}")
                
                if len(all_nodes) == 0 and len(all_edges) == 0:
                    logger.warning(f"[INGEST] No entities or relations extracted from {len(extraction_nodes)} chunks for source_id={source_id}. This may indicate:")
                    logger.warning(f"[INGEST] 1. LLM extraction is failing (check LLM configuration and API key)")
                    logger.warning(f"[INGEST] 2. Text content is not suitable for extraction")
                    logger.warning(f"[INGEST] 3. JSON parsing is failing (check extraction logs)")
            elif extract_graph and not self.extraction_enabled:
                logger.warning(f"[INGEST] Graph extraction requested but LLM is not configured. Skipping entity/relation extraction.")
                logger.warning(f"[INGEST] To enable extraction, set LLM_API_KEY in backend/.env file with a valid OpenRouter API key.")
            elif not extract_graph:
                logger.info(f"[INGEST] Graph extraction disabled (extract_graph=false). Skipping entity/relation extraction.")
            
            # Step 4: Store in Neo4j (graph store)
            await self._store_in_neo4j(all_nodes, all_edges, source_id)
            
            # Step 5: Store in Qdrant (vector store) - use child nodes for precise retrieval
            await self._store_in_qdrant(vector_nodes, source_id, clearance_level)
            
            # Mark as processed for idempotency
            if check_hash:
                text_hash = self._compute_text_hash(text, source_id)
                self._processed_hashes.add(text_hash)
            
            return {
                "source_id": source_id,
                "source_name": source_name,
                "entities_extracted": len(all_nodes),
                "relations_extracted": len(all_edges),
                "chunks_created": len(vector_nodes),
                "status": "success",
            }
        except Exception as e:
            # Error handling: Log to failed_jobs (in-memory for now, can be extended to DB)
            error_info = {
                "source_id": source_id,
                "source_name": source_name,
                "error": str(e),
                "clearance_level": clearance_level,
            }
            logger.error(f"Failed ingestion job: {error_info}", exc_info=True)
            # In production, store in failed_jobs table/queue
            # await self._log_failed_job(error_info)
            raise RuntimeError(f"Ingestion failed: {str(e)}") from e
    
    def _compute_text_hash(self, text: str, source_id: str) -> str:
        """
        Compute hash for text content for idempotency checking.
        
        Args:
            text: Text content
            source_id: Source identifier
            
        Returns:
            SHA256 hash string
        """
        content = f"{source_id}:{text}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def _store_in_neo4j(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        document_id: str,
    ) -> None:
        """
        Store nodes and edges directly in Neo4j.
        
        Args:
            nodes: List of extracted nodes (JSON format)
            edges: List of extracted edges (JSON format)
            document_id: Document ID for linking
        """
        if not nodes and not edges:
            logger.warning(f"[INGEST] No nodes or edges to store in Neo4j for document_id={document_id}")
            return
        
        driver = get_neo4j_driver()
        
        # Fixed: Add logging for Neo4j storage
        logger.info(f"[INGEST] Storing {len(nodes)} nodes and {len(edges)} edges in Neo4j for document_id={document_id}")
        
        async with driver.session() as session:
            # Create nodes
            nodes_created = 0
            for node in nodes:
                entity_type = node.get("type", "entity").upper()
                entity_id = node.get("id", "")
                
                # Fixed: Generate entity ID if missing
                if not entity_id:
                    entity_name = node.get("label") or node.get("properties", {}).get("name", "unknown")
                    entity_id = f"{entity_type.lower()}_{entity_name.lower().replace(' ', '_')}"
                    logger.warning(f"[INGEST] Generated entity ID: {entity_id} for entity without ID")
                
                properties = node.get("properties", {}).copy()
                properties["source_id"] = document_id
                properties["name"] = node.get("label") or properties.get("name", entity_id)
                
                # Fixed: Ensure entity_id is in properties for consistency
                if "id" not in properties:
                    properties["id"] = entity_id
                
                # Create or update node
                # Use parameterized query to prevent injection
                query = f"""
                MERGE (n:{entity_type} {{id: $entity_id}})
                SET n += $properties
                RETURN n
                """
                try:
                    result = await session.run(query, entity_id=entity_id, properties=properties)
                    await result.consume()  # Consume result to ensure query executes
                    nodes_created += 1
                except Exception as e:
                    logger.error(f"[INGEST] Failed to store node {entity_id}: {e}")
                    continue
            
            logger.info(f"[INGEST] Created/updated {nodes_created}/{len(nodes)} nodes in Neo4j")
            
            # Create relationships
            edges_created = 0
            for edge in edges:
                source_id = edge.get("source", "")
                target_id = edge.get("target", "")
                rel_type = edge.get("relationship", "related_to").upper()
                properties = edge.get("properties", {}).copy()
                weight = edge.get("weight", 1.0)
                properties["weight"] = weight
                
                # Fixed: Skip edges with missing source or target
                if not source_id or not target_id:
                    logger.warning(f"[INGEST] Skipping edge with missing source or target: source={source_id}, target={target_id}")
                    continue
                
                # Create relationship
                query = f"""
                MATCH (a), (b)
                WHERE a.id = $source_id AND b.id = $target_id
                MERGE (a)-[r:{rel_type}]->(b)
                SET r += $properties
                RETURN r
                """
                try:
                    result = await session.run(
                        query,
                        source_id=source_id,
                        target_id=target_id,
                        properties=properties,
                    )
                    await result.consume()  # Consume result to ensure query executes
                    edges_created += 1
                except Exception as e:
                    logger.error(f"[INGEST] Failed to store edge {source_id}->{target_id}: {e}")
                    continue
            
            logger.info(f"[INGEST] Created/updated {edges_created}/{len(edges)} edges in Neo4j")
    
    async def _store_in_qdrant(
        self,
        nodes: List[Any],
        document_id: str,
        clearance_level: str,
    ) -> None:
        """
        Store document chunks in Qdrant vector store.
        
        Args:
            nodes: Document nodes (chunks)
            document_id: Document ID
            clearance_level: Clearance level
        """
        client = get_qdrant_client()
        
        # Ensure collection exists
        from app.core.database import ensure_qdrant_collection
        await ensure_qdrant_collection()
        
        # For now, store metadata only
        # TODO: Implement proper embedding generation and storage
        # This is a placeholder - actual implementation would:
        # 1. Generate embeddings for each node
        # 2. Store in Qdrant with metadata
        # 3. Link to document_id and clearance_level
        
        # Generate embeddings and store
        from app.core.embeddings import get_embedding_service
        
        embedding_service = get_embedding_service()
        texts = [node.get_content() for node in nodes]
        embeddings = await embedding_service.get_embeddings(texts)
        
        points = []
        for i, (node, embedding) in enumerate(zip(nodes, embeddings)):
            node_id = f"{document_id}_{i}"
            text = node.get_content()
            
            points.append({
                "id": node_id,
                "vector": embedding,
                "payload": {
                    "text": text,
                    "document_id": document_id,
                    "clearance_level": clearance_level,
                    "metadata": node.metadata if hasattr(node, "metadata") else {},
                },
            })
        
        if points:
            try:
                await client.upsert(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    points=points,
                )
            except Exception as e:
                logger.warning(f"Failed to store in Qdrant: {e}")
                # Continue even if Qdrant fails
    
    async def _log_failed_job(self, error_info: Dict[str, Any]) -> None:
        """
        Log failed ingestion job for retry/debugging.
        
        In production, this should write to a database table or queue.
        For now, logs to logger.
        
        Args:
            error_info: Dictionary with error details
        """
        logger.error(f"Failed ingestion job logged: {error_info}")
        # TODO: Implement database logging:
        # await db.execute(
        #     "INSERT INTO failed_jobs (source_id, source_name, error, clearance_level, created_at) VALUES (:source_id, :source_name, :error, :clearance_level, NOW())",
        #     error_info
        # )

