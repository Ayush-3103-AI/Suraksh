/**
 * Ingest API Client
 * Handles data ingestion into GraphRAG pipeline.
 */

import { apiClient } from "./client";

export interface IngestRequest {
  text: string;
  source_id?: string;
  source_name?: string;
  clearance_level?: string;
  extract_graph?: boolean;
}

export interface IngestResponse {
  source_id: string;
  source_name: string | null;
  entities_extracted: number;
  relations_extracted: number;
  chunks_created: number;
  status: string;
}

/**
 * Ingest text data into the GraphRAG pipeline
 */
export async function ingestData(
  text: string,
  sourceId?: string,
  sourceName?: string,
  clearanceLevel: string = "L3",
  extractGraph: boolean = true
): Promise<IngestResponse> {
  const response = await apiClient.post<IngestResponse>("/api/v1/ingest", {
    text,
    source_id: sourceId,
    source_name: sourceName,
    clearance_level: clearanceLevel,
    extract_graph: extractGraph,
  });
  return response.data;
}

/**
 * Ingest a file from the vault into the GraphRAG pipeline
 */
export async function ingestFile(
  fileId: string,
  extractGraph: boolean = true
): Promise<IngestResponse> {
  // Fixed: Validate and normalize file_id before sending
  if (!fileId || typeof fileId !== 'string') {
    throw new Error("file_id must be a non-empty string");
  }
  const normalizedFileId = String(fileId).trim();
  if (!normalizedFileId || normalizedFileId === 'undefined' || normalizedFileId === 'null') {
    throw new Error("file_id cannot be empty or invalid");
  }
  
  // Log the request payload for debugging
  const requestPayload = {
    file_id: normalizedFileId,
    extract_graph: extractGraph,
  };
  console.log("[INGEST] Sending request:", requestPayload);
  
  const response = await apiClient.post<IngestResponse>("/api/v1/ingest/file", requestPayload);
  return response.data;
}

/**
 * Get ingestion diagnostics (LLM configuration, pipeline status)
 */
export async function getIngestionDiagnostics(): Promise<{
  pipeline_available: boolean;
  llm_configured: boolean;
  llm_error?: string;
  extractor_available: boolean;
  extractor_error?: string;
  llm_type?: string;
}> {
  const response = await apiClient.get("/api/v1/ingest/diagnostics");
  return response.data;
}

