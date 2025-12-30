/**
 * Search API Client
 * Handles GraphRAG search and graph data requests.
 */

import { apiClient } from "./client";

export interface SearchRequest {
  query: string;
  top_k?: number;
}

export interface SearchResponse {
  query: string;
  answer: string;
  graph_path: {
    path_found: boolean;
    path_length: number;
    entities: string[];
    error?: string;
  };
  entities_found: string[];
  reasoning: string;
}

export interface GraphNode {
  id: string;
  label: string;
  properties: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
  properties?: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

/**
 * Perform hybrid search (Vector + Graph)
 */
export async function search(query: string, topK: number = 5): Promise<SearchResponse> {
  // Fixed: Add trailing slash to match backend endpoint and validate query
  if (!query || query.trim().length < 3) {
    throw new Error("Query must be at least 3 characters long");
  }
  if (topK < 1 || topK > 50) {
    throw new Error("top_k must be between 1 and 50");
  }
  const response = await apiClient.post<SearchResponse>("/api/v1/search/", {
    query: query.trim(),
    top_k: topK,
  });
  return response.data;
}

/**
 * Get all graph data for visualization (all entities)
 */
export async function getAllGraphData(limit: number = 200): Promise<GraphData> {
  const response = await apiClient.get<GraphData>("/api/v1/search/graph/all", {
    params: {
      limit,
    },
  });
  return response.data;
}

/**
 * Get graph data for visualization
 */
export async function getGraphData(
  entityName: string,
  depth: number = 2
): Promise<GraphData> {
  const response = await apiClient.get<GraphData>("/api/v1/search/graph", {
    params: {
      entity_name: entityName,
      depth,
    },
  });
  return response.data;
}

