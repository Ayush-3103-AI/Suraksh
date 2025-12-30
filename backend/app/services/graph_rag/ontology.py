"""
GraphRAG Ontology Definition
Strict entity and relation types for knowledge graph extraction.
"""

# Entity Types
ENTITY_TYPES = {
    "PERSON": {
        "description": "Individual person with attributes: Name, Alias, Nationality, Role",
        "properties": ["name", "alias", "nationality", "role"],
    },
    "ORGANIZATION": {
        "description": "Organization with attributes: Name, Type (Gov/Terror/NGO), Location",
        "properties": ["name", "type", "location"],
    },
    "LOCATION": {
        "description": "Geographic location with attributes: City, Coordinates, Region",
        "properties": ["city", "coordinates", "region"],
    },
    "EVENT": {
        "description": "Event with attributes: Type (Attack/Meeting/Transfer), Date",
        "properties": ["type", "date"],
    },
    "DOCUMENT": {
        "description": "Source document reference",
        "properties": ["source_file", "document_id"],
    },
}

# Relation Types
RELATION_TYPES = {
    "AFFILIATED_WITH": {
        "description": "Person is affiliated with Organization",
        "source": "PERSON",
        "target": "ORGANIZATION",
    },
    "LOCATED_AT": {
        "description": "Person/Organization/Event is located at Location",
        "source": ["PERSON", "ORGANIZATION", "EVENT"],
        "target": "LOCATION",
    },
    "PARTICIPATED_IN": {
        "description": "Person participated in Event",
        "source": "PERSON",
        "target": "EVENT",
    },
    "MENTIONED_IN": {
        "description": "Entity is mentioned in Document",
        "source": ["PERSON", "ORGANIZATION", "LOCATION", "EVENT"],
        "target": "DOCUMENT",
    },
    "FUNDED": {
        "description": "Person/Organization funded Organization/Event",
        "source": ["PERSON", "ORGANIZATION"],
        "target": ["ORGANIZATION", "EVENT"],
    },
}


def get_extraction_prompt() -> str:
    """
    Get the LLM prompt for graph extraction with strict ontology enforcement.
    
    Returns:
        Extraction prompt string
    """
    entity_list = "\n".join(
        [f"- {etype}: {info['description']}" for etype, info in ENTITY_TYPES.items()]
    )
    relation_list = "\n".join(
        [
            f"- {rtype}: {info['description']}"
            for rtype, info in RELATION_TYPES.items()
        ]
    )
    
    return f"""You are a knowledge graph extraction expert. Extract ONLY entities and relations that match the following strict ontology.

ENTITY TYPES (extract ONLY these):
{entity_list}

RELATION TYPES (extract ONLY these):
{relation_list}

EXTRACTION RULES:
1. Extract entities with their properties as specified above
2. Extract relations only between valid entity types as specified
3. Do NOT create entities or relations that don't match the ontology
4. Be precise with entity names - use full names when available
5. Extract dates in ISO format (YYYY-MM-DD) when possible
6. For locations, include city and region when mentioned
7. For organizations, specify type (Government, Terrorist, NGO, etc.) when clear
8. Link entities to documents using MENTIONED_IN when the entity appears in the text
9. Generate unique IDs for entities using format: entity_type_lowercase_name_normalized (e.g., "person_john_smith")
10. Always return valid JSON - no markdown, no code blocks, just pure JSON

OUTPUT FORMAT:
You MUST return ONLY a valid JSON object (no markdown, no code blocks, no explanations) with this exact structure:
{{
  "entities": [
    {{"type": "PERSON", "id": "person_john_smith", "properties": {{"name": "John Smith", "role": "Police Officer"}}}},
    {{"type": "LOCATION", "id": "location_new_york_city", "properties": {{"city": "New York City", "region": "New York"}}}}
  ],
  "relations": [
    {{"source": "person_john_smith", "target": "location_new_york_city", "type": "LOCATED_AT", "properties": {{}}}}
  ]
}}

CRITICAL: Return ONLY the JSON object, nothing else. No markdown, no code blocks, no explanations.

Extract entities and relations from the following text:
"""


def get_synthesis_prompt(query: str, context: str, graph_path: str) -> str:
    """
    Get the LLM prompt for synthesizing answers from graph traversal and context.
    
    Args:
        query: Original user query
        context: Relevant document chunks/context
        graph_path: Graph traversal path description
        
    Returns:
        Synthesis prompt string
    """
    return f"""You are an intelligence analyst assistant. Answer the user's query by synthesizing information from the knowledge graph and document context.

USER QUERY: {query}

GRAPH TRAVERSAL PATH:
{graph_path}

DOCUMENT CONTEXT:
{context}

INSTRUCTIONS:
1. Use the graph path to understand entity relationships
2. Use the document context to provide specific details and citations
3. Provide a clear, concise answer that directly addresses the query
4. Include relevant entity names, dates, and locations
5. If the information is insufficient, state what is known and what is not
6. Maintain security awareness - do not speculate beyond available evidence

Generate a comprehensive answer:
"""

