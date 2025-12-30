"""
Search Endpoints
Hybrid search (Vector + Graph) for intelligence queries.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.core.security import User, get_current_active_user
from app.services.graph_rag.search import HybridSearchService

router = APIRouter()


# Request/Response Models
class SearchRequest(BaseModel):
    """Search request model."""
    query: str
    top_k: int = 5
    vector_weight: float = 0.5
    graph_weight: float = 0.5


class Node(BaseModel):
    """Graph node model."""
    id: str
    label: str
    properties: dict


class Edge(BaseModel):
    """Graph edge model."""
    source: str
    target: str
    relation: str
    properties: dict = {}


class GraphPath(BaseModel):
    """Graph path model."""
    path_found: bool
    path_length: int
    entities: list[str]
    error: str | None = None


class SearchResponse(BaseModel):
    """Search response model."""
    query: str
    answer: str
    graph_path: GraphPath
    entities_found: list[str]
    reasoning: str = ""


@router.post("/", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def hybrid_search(
    request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
) -> SearchResponse:
    """
    Perform hybrid search combining vector search and graph traversal.
    
    Args:
        request: Search request with query
        current_user: Current authenticated user
        
    Returns:
        Search results with synthesized answer
        
    Raises:
        HTTPException: If search fails
    """
    # Validate query
    if not request.query or len(request.query.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must be at least 3 characters long"
        )
    
    # Validate top_k
    if request.top_k < 1 or request.top_k > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="top_k must be between 1 and 50"
        )
    
    # Initialize search service with configurable weights
    search_service = HybridSearchService(
        vector_weight=request.vector_weight,
        graph_weight=request.graph_weight,
    )
    
    try:
        # Perform hybrid search
        result = await search_service.search(
            query=request.query,
            user_clearance=current_user.clearance_level,
            top_k=request.top_k,
        )
        
        # Format graph path
        graph_path = GraphPath(
            path_found=result["graph_path"].get("path_found", False),
            path_length=result["graph_path"].get("path_length", 0),
            entities=result["graph_path"].get("entities", []),
            error=result["graph_path"].get("error"),
        )
        
        return SearchResponse(
            query=result["query"],
            answer=result["answer"],
            graph_path=graph_path,
            entities_found=result.get("entities_found", []),
            reasoning=f"Found {len(result.get('vector_results', []))} relevant documents and {graph_path.path_length} graph relationships.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        ) from e


@router.get("/graph/all", status_code=status.HTTP_200_OK)
async def get_all_graph_data(
    limit: int = Query(200, ge=1, le=1000, description="Maximum number of nodes to return"),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get all graph data for visualization (all entities and relationships).
    
    Args:
        limit: Maximum number of nodes to return
        current_user: Current authenticated user
        
    Returns:
        Graph data with nodes and edges
    """
    try:
        from app.core.database import get_neo4j_driver
        
        # Fixed: Check if Neo4j driver can be initialized
        try:
            driver = get_neo4j_driver()
        except RuntimeError as e:
            # Neo4j not available - return empty graph gracefully
            return {
                "nodes": [],
                "edges": [],
            }
        
        # Query Neo4j for all nodes and relationships
        # Fixed: First get all nodes (even without relationships), then get relationships
        # This ensures we return nodes even if no relationships exist
        nodes_query = """
        MATCH (n)
        RETURN n
        LIMIT $node_limit
        """
        
        relationships_query = """
        MATCH (n)-[r]->(connected)
        RETURN n, r, connected
        LIMIT $rel_limit
        """
        
        nodes = []
        edges = []
        node_ids = set()
        node_id_map = {}  # Map Neo4j internal ID to our node ID
        edge_ids = set()
        
        # Fixed: Handle connection errors gracefully
        try:
            async with driver.session() as session:
                # Step 1: Get all nodes (even without relationships)
                nodes_result = await session.run(nodes_query, node_limit=limit)
                
                async for record in nodes_result:
                    if "n" in record:
                        node = record["n"]
                        # Use the node's 'id' property if it exists, otherwise use Neo4j internal ID
                        node_props = dict(node)
                        node_id = node_props.get("id", str(node.id))
                        neo4j_id = node.id
                        
                        if node_id not in node_ids:
                            # Get label (entity type)
                            labels = list(node.labels)
                            label = labels[0] if labels else "ENTITY"
                            
                            # Use 'name' property for label if available, otherwise use ID
                            display_label = node_props.get("name", node_id)
                            
                            nodes.append({
                                "id": node_id,
                                "label": display_label,
                                "type": label,
                                "properties": node_props,
                            })
                            node_ids.add(node_id)
                            node_id_map[neo4j_id] = node_id
                            
                            # Stop if we've reached the node limit
                            if len(nodes) >= limit:
                                break
                
                # Step 2: Get relationships and filter by nodes we found
                if len(node_id_map) > 0:
                    rel_result = await session.run(relationships_query, rel_limit=limit * 3)
                    
                    async for record in rel_result:
                        if "r" in record and "n" in record and "connected" in record:
                            rel = record["r"]
                            source_node = record["n"]
                            target_node = record["connected"]
                            
                            source_neo4j_id = source_node.id
                            target_neo4j_id = target_node.id
                            
                            # Only include if both nodes are in our node set
                            source_id = node_id_map.get(source_neo4j_id)
                            target_id = node_id_map.get(target_neo4j_id)
                            
                            if source_id and target_id:
                                edge_key = f"{source_id}-{rel.type}-{target_id}"
                                if edge_key not in edge_ids:
                                    edges.append({
                                        "source": source_id,
                                        "target": target_id,
                                        "relationship": rel.type,
                                        "properties": dict(rel),
                                    })
                                    edge_ids.add(edge_key)
        except Exception as conn_error:
            # Fixed: Handle connection errors (Neo4j not running) gracefully
            # Check if it's a connection error
            error_msg = str(conn_error).lower()
            if "resolve" in error_msg or "connection" in error_msg or "refused" in error_msg:
                # Neo4j is not available - return empty graph
                return {
                    "nodes": [],
                    "edges": [],
                }
            # Re-raise if it's a different error
            raise
        
        return {
            "nodes": nodes,
            "edges": edges,
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Fixed: Provide more specific error message
        error_detail = str(e)
        if "resolve" in error_detail.lower() or "connection" in error_detail.lower():
            # Return empty graph if Neo4j is not available
            return {
                "nodes": [],
                "edges": [],
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve graph data: {error_detail}"
        ) from e


@router.get("/graph", status_code=status.HTTP_200_OK)
async def get_graph_data(
    entity_name: str = Query(..., description="Entity name to find connections for"),
    depth: int = Query(2, ge=1, le=5, description="Graph traversal depth"),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get graph data for visualization.
    
    Args:
        entity_name: Entity name to find connections for
        depth: Graph traversal depth
        current_user: Current authenticated user
        
    Returns:
        Graph data with nodes and edges
    """
    try:
        from app.core.database import get_neo4j_driver
        
        # Fixed: Check if Neo4j driver can be initialized
        try:
            driver = get_neo4j_driver()
        except RuntimeError as e:
            # Neo4j not available - return empty graph gracefully
            return {
                "nodes": [],
                "edges": [],
            }
        
        # Query Neo4j for entity and its connections
        query = """
        MATCH (n)-[r*1..$depth]-(connected)
        WHERE n.name = $entity_name OR n.id = $entity_name
        RETURN n, r, connected
        LIMIT 100
        """
        
        nodes = []
        edges = []
        node_ids = set()
        
        # Fixed: Handle connection errors gracefully
        try:
            async with driver.session() as session:
                result = await session.run(query, entity_name=entity_name, depth=depth)
                
                async for record in result:
                    # Extract nodes
                    for node_key in ["n", "connected"]:
                        if node_key in record:
                            node = record[node_key]
                            node_id = str(node.id)
                            if node_id not in node_ids:
                                nodes.append({
                                    "id": node_id,
                                    "label": list(node.labels)[0] if node.labels else "ENTITY",
                                    "properties": dict(node),
                                })
                                node_ids.add(node_id)
                    
                    # Extract relationships
                    if "r" in record:
                        rels = record["r"]
                        if isinstance(rels, list):
                            for rel in rels:
                                edges.append({
                                    "source": str(rel.start_node.id),
                                    "target": str(rel.end_node.id),
                                    "relation": rel.type,
                                    "properties": dict(rel),
                                })
                        else:
                            edges.append({
                                "source": str(rels.start_node.id),
                                "target": str(rels.end_node.id),
                                "relation": rels.type,
                                "properties": dict(rels),
                            })
        except Exception as conn_error:
            # Fixed: Handle connection errors (Neo4j not running) gracefully
            error_msg = str(conn_error).lower()
            if "resolve" in error_msg or "connection" in error_msg or "refused" in error_msg:
                # Neo4j is not available - return empty graph
                return {
                    "nodes": [],
                    "edges": [],
                }
            # Re-raise if it's a different error
            raise
        
        return {
            "nodes": nodes,
            "edges": edges,
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Fixed: Provide more specific error message and graceful degradation
        error_detail = str(e)
        if "resolve" in error_detail.lower() or "connection" in error_detail.lower():
            # Return empty graph if Neo4j is not available
            return {
                "nodes": [],
                "edges": [],
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve graph data: {error_detail}"
        ) from e

