/**
 * Vault API Client
 * Handles secure file vault operations.
 */

import { apiClient } from "./client";

export interface FileMetadata {
  id: string | number;
  filename: string;
  size: number;
  clearance_level: string;
  uploaded_at: string;
  uploaded_by?: string;
  content_type?: string;
}

export interface ListFilesResponse {
  files: FileMetadata[];
  total: number;
}

export interface UploadFileResponse {
  file_id: string;
  filename: string;
  size: number;
  uploaded_at: string;
}

/**
 * Vault API client
 */
export const vaultApi = {
  /**
   * List all files in the vault
   */
  async listFiles(): Promise<ListFilesResponse> {
    const response = await apiClient.get<ListFilesResponse>("/api/v1/vault/files");
    return response.data;
  },

  /**
   * Upload a file to the vault
   */
  async uploadFile(file: File): Promise<UploadFileResponse> {
    const formData = new FormData();
    formData.append("file", file);
    
    // Fixed: Add timeout for file uploads (5 minutes for large files)
    const timeout = 5 * 60 * 1000; // 5 minutes in milliseconds
    
    const response = await apiClient.post<UploadFileResponse>(
      "/api/v1/vault/upload",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        timeout: timeout,
      }
    );
    return response.data;
  },

  /**
   * Open file preview in a new tab
   */
  async openFilePreview(fileId: string | number): Promise<void> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    
    // Get token from localStorage
    let token: string | null = null;
    if (typeof window !== "undefined") {
      try {
        const authStorage = localStorage.getItem("auth-storage");
        if (authStorage) {
          const parsed = JSON.parse(authStorage);
          token = parsed.state?.token;
        }
        if (!token) {
          token = localStorage.getItem("auth_token");
        }
      } catch (e) {
        token = localStorage.getItem("auth_token");
      }
    }
    
    if (!token) {
      throw new Error("Authentication token not found");
    }
    
    // Fetch file with authentication
    const response = await fetch(`${API_BASE_URL}/api/v1/vault/files/${fileId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch file: ${response.statusText}`);
    }
    
    // Get file content and content type
    const blob = await response.blob();
    const contentType = response.headers.get("content-type") || "application/octet-stream";
    
    // Create blob URL and open in new tab
    const blobUrl = URL.createObjectURL(blob);
    const newWindow = window.open(blobUrl, "_blank");
    
    // Clean up blob URL after a delay (give browser time to load)
    if (newWindow) {
      newWindow.addEventListener("load", () => {
        setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
      });
    } else {
      // If popup was blocked, clean up immediately
      setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
    }
  },
};

