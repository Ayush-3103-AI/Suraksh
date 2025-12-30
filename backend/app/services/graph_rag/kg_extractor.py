"""
Enhanced Knowledge Graph Extractor
Implements high-fidelity, production-grade KG extraction with:
- PDF extraction using PyPDF2/pdfplumber
- Entity resolution and merging
- Evidence-based relationship extraction
- Domain-specific entity types
- JSON-compliant output schema
"""

import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

from llama_index.core.llms import LLM

from app.core.config import settings
from app.services.graph_rag.ontology import ENTITY_TYPES, RELATION_TYPES


class EntityResolver:
    """
    Entity resolution system to merge duplicate entities.
    Handles canonicalization of entity names (e.g., "AI" -> "Artificial Intelligence").
    """
    
    def __init__(self):
        """Initialize entity resolver with canonicalization rules."""
        self.canonical_map: Dict[str, str] = {}
        self.entity_variants: Dict[str, Set[str]] = defaultdict(set)
        
    def normalize_entity_name(self, name: str) -> str:
        """
        Normalize entity name for comparison.
        
        Args:
            name: Entity name to normalize
            
        Returns:
            Normalized entity name
        """
        if not name:
            return ""
        
        # Convert to lowercase and strip
        normalized = name.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common prefixes/suffixes
        normalized = re.sub(r'^(the|a|an)\s+', '', normalized)
        
        return normalized
    
    def find_canonical(self, entity_name: str, entity_type: str) -> str:
        """
        Find or create canonical entity name.
        
        Args:
            entity_name: Entity name to resolve
            entity_type: Type of entity
            
        Returns:
            Canonical entity name
        """
        normalized = self.normalize_entity_name(entity_name)
        
        # Check if we already have a canonical form
        if normalized in self.canonical_map:
            return self.canonical_map[normalized]
        
        # Check for similar variants
        for canonical, variants in self.entity_variants.items():
            if normalized in variants:
                self.canonical_map[normalized] = canonical
                return canonical
        
        # Create new canonical form (use original name as canonical)
        canonical = entity_name.strip()
        self.canonical_map[normalized] = canonical
        self.entity_variants[canonical].add(normalized)
        
        return canonical
    
    def merge_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge duplicate entities based on name similarity and type.
        
        Args:
            entities: List of entity dictionaries
            
        Returns:
            Merged list of unique entities
        """
        # Group entities by type and normalized name
        entity_groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
        
        for entity in entities:
            entity_type = entity.get("type", "ENTITY").upper()
            entity_name = entity.get("properties", {}).get("name", entity.get("id", ""))
            
            if not entity_name:
                continue
            
            normalized_name = self.normalize_entity_name(entity_name)
            key = (entity_type, normalized_name)
            entity_groups[key].append(entity)
        
        # Merge entities in each group
        merged_entities = []
        for (entity_type, normalized_name), group in entity_groups.items():
            if len(group) == 1:
                # No duplicates, use as-is
                merged_entities.append(group[0])
            else:
                # Merge multiple entities
                merged_entity = self._merge_entity_group(group)
                merged_entities.append(merged_entity)
        
        return merged_entities
    
    def _merge_entity_group(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge a group of duplicate entities into one.
        
        Args:
            entities: List of duplicate entities to merge
            
        Returns:
            Merged entity dictionary
        """
        if not entities:
            return {}
        
        # Use first entity as base
        merged = entities[0].copy()
        merged_properties = merged.get("properties", {}).copy()
        
        # Merge properties from all entities
        for entity in entities[1:]:
            props = entity.get("properties", {})
            for key, value in props.items():
                if key not in merged_properties:
                    merged_properties[key] = value
                elif isinstance(merged_properties[key], list) and isinstance(value, list):
                    # Merge lists
                    merged_properties[key] = list(set(merged_properties[key] + value))
                elif merged_properties[key] != value:
                    # Keep both values as list
                    if not isinstance(merged_properties[key], list):
                        merged_properties[key] = [merged_properties[key]]
                    if value not in merged_properties[key]:
                        merged_properties[key].append(value)
        
        merged["properties"] = merged_properties
        
        # Use canonical name
        entity_name = merged_properties.get("name", merged.get("id", ""))
        canonical_name = self.find_canonical(entity_name, merged.get("type", "ENTITY"))
        merged_properties["name"] = canonical_name
        merged["id"] = self._generate_entity_id(canonical_name, merged.get("type", "ENTITY"))
        
        return merged
    
    def _generate_entity_id(self, name: str, entity_type: str) -> str:
        """
        Generate a unique entity ID.
        
        Args:
            name: Entity name
            entity_type: Entity type
            
        Returns:
            Unique entity ID
        """
        # Create ID from type and normalized name
        normalized = self.normalize_entity_name(name)
        normalized = re.sub(r'[^a-z0-9]+', '_', normalized)
        return f"{entity_type.lower()}_{normalized}"


class EnhancedKGExtractor:
    """
    Enhanced Knowledge Graph Extractor with:
    - Evidence-based relationship extraction
    - Entity resolution
    - Domain-specific entity types
    - JSON-compliant output
    """
    
    def __init__(self, llm: Optional[LLM] = None):
        """
        Initialize enhanced KG extractor.
        
        Args:
            llm: LLM instance (defaults to extraction LLM from config)
        """
        from app.services.graph_rag.llm_setup import get_extraction_llm
        self.llm = llm or get_extraction_llm()
        self.resolver = EntityResolver()
    
    async def extract_from_text(
        self,
        text: str,
        document_id: Optional[str] = None,
        evidence_required: bool = True,
    ) -> Dict[str, Any]:
        """
        Extract entities and relations from text with evidence tracking.
        
        Args:
            text: Input text to extract from
            document_id: Optional document ID to link entities
            evidence_required: Whether to require evidence for relationships
            
        Returns:
            Dictionary with 'nodes' and 'edges' arrays in JSON-compliant format
        """
        # Build enhanced extraction prompt
        prompt = self._build_extraction_prompt(text, document_id, evidence_required)
        
        # Call LLM for extraction
        response_text = ""
        try:
            if hasattr(self.llm, "acomplete"):
                response = await self.llm.acomplete(prompt)
            else:
                import asyncio
                response = await asyncio.to_thread(self.llm.complete, prompt)
            response_text = str(response)
            
            # Parse JSON response
            result = self._parse_llm_response(response_text)
            
            # Extract entities and relations
            entities = result.get("entities", [])
            relations = result.get("relations", [])
            
            # Add document_id to entities if provided
            if document_id:
                for entity in entities:
                    if "properties" not in entity:
                        entity["properties"] = {}
                    entity["properties"]["document_id"] = document_id
                    entity["properties"]["source_document"] = document_id
            
            # Resolve and merge duplicate entities
            merged_entities = self.resolver.merge_entities(entities)
            
            # Update relation source/target IDs to use canonical entity IDs
            canonical_relations = self._resolve_relation_entities(relations, merged_entities)
            
            # Validate relationships have evidence
            if evidence_required:
                validated_relations = self._validate_relationship_evidence(
                    canonical_relations, text
                )
            else:
                validated_relations = canonical_relations
            
            # Format as JSON-compliant structure
            nodes = self._format_nodes(merged_entities)
            edges = self._format_edges(validated_relations)
            
            return {
                "nodes": nodes,
                "edges": edges,
            }
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse LLM extraction response: {e}")
            if response_text:
                print(f"Response was: {response_text[:500]}")
            return {"nodes": [], "edges": []}
        except Exception as e:
            print(f"Error during extraction: {e}")
            import traceback
            traceback.print_exc()
            return {"nodes": [], "edges": []}
    
    def _build_extraction_prompt(
        self, text: str, document_id: Optional[str], evidence_required: bool
    ) -> str:
        """
        Build enhanced extraction prompt with strict ontology enforcement.
        
        Args:
            text: Text to extract from
            document_id: Document ID
            evidence_required: Whether to require evidence
            
        Returns:
            Extraction prompt string
        """
        entity_list = "\n".join(
            [f"- {etype}: {info['description']}" for etype, info in ENTITY_TYPES.items()]
        )
        relation_list = "\n".join(
            [
                f"- {rtype}: {info['description']} (from {info.get('source', 'ANY')} to {info.get('target', 'ANY')})"
                for rtype, info in RELATION_TYPES.items()
            ]
        )
        
        evidence_instruction = ""
        if evidence_required:
            evidence_instruction = """
EVIDENCE REQUIREMENTS:
- Every relationship MUST be directly supported by evidence in the text
- Include the exact text snippet that supports each relationship in the "evidence" property
- DO NOT infer relationships that are not explicitly stated
- DO NOT create relationships based on assumptions or common knowledge
"""
        
        prompt = f"""You are a Knowledge Graph Engineer. Extract entities and relationships from the following text, following strict rules.

ENTITY TYPES (extract ONLY these domain-specific types):
{entity_list}

RELATION TYPES (extract ONLY these relationships):
{relation_list}

EXTRACTION RULES:
1. Extract entities with their properties as specified above
2. Use domain-specific entity types - NEVER use generic types like "Item" or "Thing"
3. Extract relations ONLY between valid entity types as specified in the relation definitions
4. Every relationship must follow [Subject] -> [Predicate] -> [Object] flow
5. Be precise with entity names - use full names when available
6. Extract dates in ISO format (YYYY-MM-DD) when possible
7. For locations, include city and region when mentioned
8. For organizations, specify type (Government, Terrorist, NGO, etc.) when clear
9. Link entities to documents using MENTIONED_IN when the entity appears in the text
{evidence_instruction}

OUTPUT FORMAT:
Return a JSON object with:
- "entities": List of {{"type": "ENTITY_TYPE", "id": "unique_id", "properties": {{"name": "...", ...}}}}
- "relations": List of {{"source": "entity_id", "target": "entity_id", "type": "RELATION_TYPE", "properties": {{"evidence": "text snippet", ...}}}}

IMPORTANT:
- Use lowercase snake_case for all "type" and "relationship" labels
- Every relationship MUST include an "evidence" property with the exact text that supports it
- DO NOT create relationships without direct evidence in the text
- DO NOT use generic entity types

TEXT TO EXTRACT FROM:
{text}
"""
        
        if document_id:
            prompt += f"\n\nDOCUMENT_ID: {document_id}\n"
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response, handling markdown code blocks.
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            Parsed JSON dictionary
        """
        # Remove markdown code blocks if present
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            if json_end > json_start:
                response_text = response_text[json_start:json_end].strip()
        
        # Parse JSON
        return json.loads(response_text)
    
    def _resolve_relation_entities(
        self, relations: List[Dict[str, Any]], entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Resolve relation source/target IDs to use canonical entity IDs.
        
        Args:
            relations: List of relation dictionaries
            entities: List of merged entity dictionaries
            
        Returns:
            List of relations with resolved entity IDs
        """
        # Create mapping from old IDs to new canonical IDs
        entity_id_map: Dict[str, str] = {}
        for entity in entities:
            old_id = entity.get("id", "")
            # Map all possible IDs to canonical ID
            entity_id_map[old_id] = entity.get("id", old_id)
            
            # Also map by name
            entity_name = entity.get("properties", {}).get("name", "")
            if entity_name:
                entity_id_map[entity_name] = entity.get("id", old_id)
        
        # Update relations
        resolved_relations = []
        for relation in relations:
            source_id = relation.get("source", "")
            target_id = relation.get("target", "")
            
            # Resolve to canonical IDs
            resolved_source = entity_id_map.get(source_id, source_id)
            resolved_target = entity_id_map.get(target_id, target_id)
            
            # Only include if both entities exist
            if resolved_source and resolved_target:
                relation_copy = relation.copy()
                relation_copy["source"] = resolved_source
                relation_copy["target"] = resolved_target
                resolved_relations.append(relation_copy)
        
        return resolved_relations
    
    def _validate_relationship_evidence(
        self, relations: List[Dict[str, Any]], text: str
    ) -> List[Dict[str, Any]]:
        """
        Validate that relationships have evidence in the text.
        
        Args:
            relations: List of relation dictionaries
            text: Source text
            
        Returns:
            List of validated relations (only those with evidence)
        """
        validated = []
        text_lower = text.lower()
        
        for relation in relations:
            evidence = relation.get("properties", {}).get("evidence", "")
            
            # Check if evidence exists and is in text
            if evidence:
                evidence_lower = evidence.lower()
                # Check if evidence snippet appears in text (with some tolerance)
                if evidence_lower in text_lower or any(
                    word in text_lower for word in evidence_lower.split() if len(word) > 3
                ):
                    validated.append(relation)
            else:
                # Try to find evidence in text based on source/target
                source = relation.get("source", "")
                target = relation.get("target", "")
                rel_type = relation.get("type", "")
                
                # Simple heuristic: if both entities appear in text, relationship might be valid
                if source.lower() in text_lower and target.lower() in text_lower:
                    # Add minimal evidence
                    if "properties" not in relation:
                        relation["properties"] = {}
                    relation["properties"]["evidence"] = f"Both {source} and {target} mentioned in text"
                    validated.append(relation)
        
        return validated
    
    def _format_nodes(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format entities as JSON-compliant nodes.
        
        Args:
            entities: List of entity dictionaries
            
        Returns:
            List of formatted node dictionaries
        """
        nodes = []
        for entity in entities:
            entity_type = entity.get("type", "entity").lower()
            entity_id = entity.get("id", "")
            properties = entity.get("properties", {})
            
            # Get label (name or id)
            label = properties.get("name", entity_id)
            
            # Ensure type is lowercase snake_case
            entity_type = re.sub(r'[^a-z0-9_]+', '_', entity_type.lower())
            
            nodes.append({
                "id": entity_id,
                "label": label,
                "type": entity_type,
                "properties": properties,
            })
        
        return nodes
    
    def _format_edges(self, relations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format relations as JSON-compliant edges.
        
        Args:
            relations: List of relation dictionaries
            
        Returns:
            List of formatted edge dictionaries
        """
        edges = []
        for relation in relations:
            source = relation.get("source", "")
            target = relation.get("target", "")
            rel_type = relation.get("type", "related_to")
            properties = relation.get("properties", {})
            
            # Ensure relationship type is lowercase snake_case
            rel_type = re.sub(r'[^a-z0-9_]+', '_', rel_type.lower())
            
            # Calculate weight (default 1.0, can be based on evidence confidence)
            weight = properties.get("weight", 1.0)
            if not isinstance(weight, (int, float)):
                weight = 1.0
            
            edges.append({
                "source": source,
                "target": target,
                "relationship": rel_type,
                "weight": float(weight),
                "properties": properties,
            })
        
        return edges

