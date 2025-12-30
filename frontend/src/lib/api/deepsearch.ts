/**
 * DeepSearch RAG API Client
 * Handles chatbot-style queries to the RAG Sentinel agent.
 */

import { apiClient } from "./client";

export interface DeepSearchRequest {
  query: string;
  top_k?: number;
}

export interface Citation {
  filename: string;
  page: number | null;
  confidence: number | null;
}

export interface SourceSummary {
  filename: string;
  pages: number[];
  confidence: number | null;
}

export interface DeepSearchResponse {
  query: string;
  answer: string;
  citations: Citation[];
  source_summary: SourceSummary[];
  error: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  citations?: Citation[];
  sources?: SourceSummary[];
  isLoading?: boolean;
  error?: string;
}

/**
 * Perform DeepSearch RAG query
 * Uses the File Vault documents as the knowledge base
 */
export async function deepSearch(
  query: string,
  topK: number = 5
): Promise<DeepSearchResponse> {
  if (!query || query.trim().length < 3) {
    throw new Error("Query must be at least 3 characters long");
  }
  if (topK < 1 || topK > 50) {
    throw new Error("top_k must be between 1 and 50");
  }

  const response = await apiClient.post<DeepSearchResponse>(
    "/api/v1/deepsearch/",
    {
      query: query.trim(),
      top_k: topK,
    }
  );
  return response.data;
}

/**
 * Generate a unique message ID
 */
export function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}


