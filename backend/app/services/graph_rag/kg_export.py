"""
Knowledge Graph JSON Export Service
Exports knowledge graph from Neo4j to portal-compatible JSON schema.
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.database import get_neo4j_driver

logger = logging.getLogger(__name__)


class KGExporter:
    """
    Knowledge Graph Exporter for JSON-compliant output.
    Formats graph data according to portal visualization schema.
    """
    
    async def export_graph(
        self,
        document_id: Optional[str] = None,
        limit: int = 1000,
        include_isolated_nodes: bool = False,
    ) -> Dict[str, Any]:
        """
        Export knowledge graph as JSON-compliant structure.
        
        Args:
            document_id: Optional document ID to filter by
            limit: Maximum number of nodes to export
            include_isolated_nodes: Whether to include nodes without relationships
            
        Returns:
            Dictionary with "nodes" and "edges" arrays
        """
        try:
            driver = get_neo4j_driver()
        except RuntimeError as e:
            logger.warning(f"Neo4j not available: {e}")
            return {"nodes": [], "edges": []}
        
        nodes = []
        edges = []
        node_ids = set()
        edge_ids = set()
        
        try:
            async with driver.session() as session:
                # Build query based on filters
                if document_id:
                    # Query for specific document
                    query = """
                    MATCH (n)-[r]-(connected)
                    WHERE n.source_id = $document_id OR connected.source_id = $document_id
                    RETURN n, r, connected
                    LIMIT $record_limit
                    """
                    result = await session.run(query, document_id=document_id, record_limit=limit * 2)
                elif include_isolated_nodes:
                    # Query all nodes and relationships
                    query = """
                    MATCH (n)
                    OPTIONAL MATCH (n)-[r]-(connected)
                    RETURN n, r, connected
                    LIMIT $record_limit
                    """
                    result = await session.run(query, record_limit=limit * 2)
                else:
                    # Query only connected nodes
                    query = """
                    MATCH (n)-[r]-(connected)
                    RETURN n, r, connected
                    LIMIT $record_limit
                    """
                    result = await session.run(query, record_limit=limit * 2)
                
                async for record in result:
                    # Extract nodes
                    for node_key in ["n", "connected"]:
                        if node_key in record:
                            node = record[node_key]
                            if node is None:
                                continue
                            
                            node_id = self._get_node_id(node)
                            if node_id and node_id not in node_ids:
                                formatted_node = self._format_node(node)
                                if formatted_node:
                                    nodes.append(formatted_node)
                                    node_ids.add(node_id)
                                    
                                    if len(nodes) >= limit:
                                        break
                    
                    # Extract relationships
                    if len(nodes) < limit and "r" in record:
                        rel = record["r"]
                        if rel is None:
                            continue
                        
                        source_id = self._get_node_id(rel.start_node)
                        target_id = self._get_node_id(rel.end_node)
                        
                        if source_id and target_id and source_id in node_ids and target_id in node_ids:
                            edge_key = f"{source_id}-{rel.type}-{target_id}"
                            if edge_key not in edge_ids:
                                formatted_edge = self._format_edge(rel, source_id, target_id)
                                if formatted_edge:
                                    edges.append(formatted_edge)
                                    edge_ids.add(edge_key)
                    
                    if len(nodes) >= limit:
                        break
                
                # If include_isolated_nodes, also get nodes without relationships
                if include_isolated_nodes and len(nodes) < limit:
                    isolated_query = """
                    MATCH (n)
                    WHERE NOT (n)--()
                    RETURN n
                    LIMIT $isolated_limit
                    """
                    isolated_result = await session.run(
                        isolated_query, isolated_limit=limit - len(nodes)
                    )
                    
                    async for record in isolated_result:
                        if "n" in record:
                            node = record["n"]
                            node_id = self._get_node_id(node)
                            if node_id and node_id not in node_ids:
                                formatted_node = self._format_node(node)
                                if formatted_node:
                                    nodes.append(formatted_node)
                                    node_ids.add(node_id)
                                    
                                    if len(nodes) >= limit:
                                        break
        
        except Exception as e:
            logger.error(f"Error exporting graph: {e}", exc_info=True)
            # Return partial results if available
            return {"nodes": nodes, "edges": edges}
        
        return {
            "nodes": nodes,
            "edges": edges,
        }
    
    def _get_node_id(self, node: Any) -> Optional[str]:
        """
        Get unique node ID from Neo4j node.
        
        Args:
            node: Neo4j node object
            
        Returns:
            Node ID string or None
        """
        if node is None:
            return None
        
        # Try to get ID from properties
        node_dict = dict(node)
        if "id" in node_dict:
            return str(node_dict["id"])
        elif "name" in node_dict:
            return str(node_dict["name"])
        else:
            # Fallback to Neo4j internal ID
            return str(node.id)
    
    def _format_node(self, node: Any) -> Optional[Dict[str, Any]]:
        """
        Format Neo4j node as JSON-compliant node.
        
        Args:
            node: Neo4j node object
            
        Returns:
            Formatted node dictionary or None
        """
        if node is None:
            return None
        
        node_dict = dict(node)
        node_id = self._get_node_id(node)
        
        if not node_id:
            return None
        
        # Get label (entity type)
        labels = list(node.labels) if hasattr(node, "labels") else []
        entity_type = labels[0].lower() if labels else "entity"
        
        # Get display label (name or id)
        label = node_dict.get("name", node_dict.get("id", node_id))
        
        # Format properties
        properties = {k: v for k, v in node_dict.items() if k not in ["id", "name"]}
        
        return {
            "id": node_id,
            "label": str(label),
            "type": entity_type,
            "properties": properties,
        }
    
    def _format_edge(
        self, rel: Any, source_id: str, target_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Format Neo4j relationship as JSON-compliant edge.
        
        Args:
            rel: Neo4j relationship object
            source_id: Source node ID
            target_id: Target node ID
            
        Returns:
            Formatted edge dictionary or None
        """
        if rel is None:
            return None
        
        # Get relationship type
        rel_type = rel.type.lower() if hasattr(rel, "type") else "related_to"
        
        # Get relationship properties
        rel_dict = dict(rel) if hasattr(rel, "__iter__") else {}
        
        # Calculate weight (default 1.0)
        weight = rel_dict.get("weight", 1.0)
        if not isinstance(weight, (int, float)):
            weight = 1.0
        
        # Extract properties (excluding weight)
        properties = {k: v for k, v in rel_dict.items() if k != "weight"}
        
        return {
            "source": source_id,
            "target": target_id,
            "relationship": rel_type,
            "weight": float(weight),
            "properties": properties,
        }


# Global instance
_kg_exporter: Optional[KGExporter] = None


def get_kg_exporter() -> KGExporter:
    """
    Get global KG exporter instance.
    
    Returns:
        KGExporter instance
    """
    global _kg_exporter
    if _kg_exporter is None:
        _kg_exporter = KGExporter()
    return _kg_exporter

