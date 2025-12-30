"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { vaultApi } from "@/lib/api/vault";
import { ingestFile } from "@/lib/api/ingest";
import { HoloCard } from "@/components/ui/holo-card";
import { Upload, File, Brain, Loader2, Lock, Eye } from "lucide-react";
import { createNotification } from "@/lib/utils/notifications";

export default function VaultPage() {
  const [uploading, setUploading] = useState(false);
  const [ingestingFileId, setIngestingFileId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const queryClient = useQueryClient();

  const { data: files, isLoading, error: filesError } = useQuery({
    queryKey: ["vault-files"],
    queryFn: async () => {
      try {
        const result = await vaultApi.listFiles();
        return result;
      } catch (err: any) {
        throw err;
      }
    },
    retry: (failureCount, error: any) => {
      // Don't retry on network errors - backend is likely down
      if (error?.code === 'ERR_NETWORK') {
        return false;
      }
      return failureCount < 3;
    },
    retryDelay: 1000,
  });

  const ingestMutation = useMutation({
    mutationFn: (fileId: string) => ingestFile(fileId, true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vault-files"] });
      setIngestingFileId(null);
    },
    onError: () => {
      setIngestingFileId(null);
    },
  });

  // Fixed: Unified file upload handler
  const uploadFile = async (file: File) => {
    if (!file) return;

    setUploading(true);
    const fileInput = document.getElementById('file-upload') as HTMLInputElement;
    
    try {
      const uploadResult = await vaultApi.uploadFile(file);
      // Create success notification
      createNotification(
        "success",
        "File Uploaded Successfully",
        `${file.name} has been uploaded and is queued for processing.`,
        "/dashboard/requests"
      );
      
      // Fixed: Refetch files immediately after successful upload
      await queryClient.invalidateQueries({ queryKey: ["vault-files"] });
      await queryClient.refetchQueries({ queryKey: ["vault-files"] });
    } catch (error: any) {
      console.error("Upload failed:", error);
      
      // Fixed: Extract better error message for timeout and network errors
      let errorMessage = "Unknown error";
      if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
        errorMessage = "Upload timed out. The file may be too large or the connection is slow. Please try again.";
      } else if (error?.code === 'ERR_NETWORK' || error?.message?.includes('Network Error')) {
        errorMessage = "Network error. Please check your connection and ensure the backend server is running.";
      } else {
        errorMessage = error?.response?.data?.detail || error?.message || "Unknown error";
      }
      
      // Create error notification
      createNotification(
        "error",
        "File Upload Failed",
        `Failed to upload ${file.name}. ${errorMessage}`,
        "/dashboard/vault"
      );
    } finally {
      // Fixed: Always reset uploading state and file input
      setUploading(false);
      if (fileInput) {
        fileInput.value = '';
      }
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await uploadFile(file);
    }
  };

  // Fixed: Add drag-and-drop handlers
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (uploading) return;

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      await uploadFile(files[0]);
    }
  };

  const getClassificationTag = (clearance: string) => {
    const level = clearance.toUpperCase();
    if (level.includes("L1") || level.includes("TOP")) {
      return { text: "TOP-SECRET", color: "bg-red-500/20 text-red-400 border-red-500/50" };
    } else if (level.includes("L2") || level.includes("SECRET")) {
      return { text: "SECRET", color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/50" };
    } else {
      return { text: "CONFIDENTIAL", color: "bg-teal-500/20 text-teal-400 border-teal-500/50" };
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatTimeAgo = (date: string) => {
    const now = new Date();
    const uploaded = new Date(date);
    const diffMs = now.getTime() - uploaded.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffHours < 1) return "Just now";
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  };

  return (
    <div className="p-8 space-y-8 h-full flex flex-col">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-display uppercase tracking-wider text-white mb-2">
            SECURE FILE VAULT
          </h1>
          <p className="text-slate-500 text-lg">
            E2E encrypted document storage with watermark protection.
          </p>
        </div>
        <button
          onClick={() => document.getElementById('file-upload')?.click()}
          disabled={uploading}
          className="px-6 py-3 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400 hover:bg-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <Upload className="w-5 h-5" />
          <span>Upload Files</span>
        </button>
      </div>

      {/* Large Drag-Drop Upload Area */}
      <HoloCard>
        <div
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
            isDragging
              ? "border-cyan-500 bg-cyan-500/10"
              : "border-cyan-500/30 hover:border-cyan-500/50"
          }`}
        >
          <label className="flex flex-col items-center justify-center w-full h-full cursor-pointer">
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <Upload className="w-16 h-16 mb-4 text-cyan-400/50" />
              <p className="mb-2 text-lg text-cyan-400 font-semibold">
                {isDragging ? "Drop file here" : "Drop files here to upload"}
              </p>
              <p className="text-sm text-slate-500">
                Files will be encrypted with AES-256 before storage.
              </p>
            </div>
            <input
              id="file-upload"
              type="file"
              className="hidden"
              onChange={handleFileUpload}
              disabled={uploading}
            />
          </label>
        </div>
        {uploading && (
          <div className="mt-4 text-sm text-cyan-400 text-center flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            Uploading...
          </div>
        )}
      </HoloCard>

      {/* File List - Grid Layout */}
      {filesError ? (
        <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg text-red-400 text-sm space-y-2">
          <div className="font-semibold">Error loading files</div>
          <div className="text-xs text-red-300">
            {filesError instanceof Error 
              ? filesError.message === "Network Error" 
                ? "Cannot connect to backend. Please ensure the backend server is running on http://localhost:8000"
                : filesError.message
              : "Unknown error"}
          </div>
        </div>
      ) : isLoading ? (
        <div className="text-slate-500">Loading files...</div>
      ) : files && files.files.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {files.files.map((file) => {
            // Fixed: Normalize file ID for consistent comparison
            const normalizedFileId = String(file.id).trim();
            const isIngesting = ingestMutation.isPending && 
              (ingestMutation.variables === normalizedFileId || ingestingFileId === normalizedFileId);
            const classification = getClassificationTag(file.clearance_level);
            
            return (
              <div
                key={file.id}
                className="relative bg-glass-light backdrop-blur-md border border-glass-border rounded-xl p-6 hover:border-cyan-500/50 transition-all group"
              >
                {/* Lock Icon - Top Right */}
                <div className="absolute top-4 right-4">
                  <Lock className="w-5 h-5 text-cyan-400/50" />
                </div>

                {/* File Icon */}
                <div className="mb-4">
                  <File className="w-12 h-12 text-cyan-400/50" />
                </div>

                {/* File Name */}
                <div className="mb-2">
                  <div className="text-cyan-400 font-mono text-sm font-semibold truncate">
                    {file.filename}
                  </div>
                </div>

                {/* File Details */}
                <div className="text-xs text-slate-500 mb-4">
                  {formatFileSize(file.size)} • {formatTimeAgo(file.uploaded_at)}
                </div>

                {/* Classification Tag */}
                <div className="mb-4">
                  <span className={`px-2 py-1 rounded text-xs font-bold border ${classification.color}`}>
                    {classification.text}
                  </span>
                </div>

                {/* Action Buttons - Bottom Right */}
                <div className="absolute bottom-4 right-4 flex gap-2">
                  <button
                    onClick={async () => {
                      // Fixed: Prevent concurrent mutations
                      if (isIngesting || ingestMutation.isPending) {
                        return;
                      }

                      let fileId: string | null = null;

                      try {
                        // Fixed: Validate file.id exists and convert to string properly
                        if (file.id === undefined || file.id === null) {
                          createNotification(
                            "error",
                            "Ingestion Failed",
                            `File ${file.filename} has no valid ID.`,
                            "/dashboard/vault"
                          );
                          return;
                        }
                        // Convert to string, handling both string and number types
                        fileId = String(file.id).trim();
                        if (!fileId || fileId === 'undefined' || fileId === 'null') {
                          createNotification(
                            "error",
                            "Ingestion Failed",
                            `File ${file.filename} has an invalid ID.`,
                            "/dashboard/vault"
                          );
                          return;
                        }

                        // Fixed: Set ingesting state before mutation
                        setIngestingFileId(fileId);
                        
                        const result = await ingestMutation.mutateAsync(fileId);
                        
                        // Log ingestion results for debugging
                        console.log("[INGEST] Ingestion completed:", {
                          file_id: fileId,
                          filename: file.filename,
                          entities_extracted: result.entities_extracted,
                          relations_extracted: result.relations_extracted,
                          chunks_created: result.chunks_created,
                          status: result.status,
                        });
                        
                        // Warn if no entities were extracted
                        if (result.entities_extracted === 0 && result.status !== "skipped_duplicate") {
                          console.warn("[INGEST] No entities extracted from file. This may indicate an issue with the extraction process or the file content.");
                          
                          // Check diagnostics to provide helpful error message
                          try {
                            const { getIngestionDiagnostics } = await import("@/lib/api/ingest");
                            const diagnostics = await getIngestionDiagnostics();
                            console.log("[INGEST] Diagnostics:", diagnostics);
                            
                            if (!diagnostics.llm_configured) {
                              console.error("[INGEST] LLM is not configured! Check LLM_API_KEY environment variable.");
                              createNotification(
                                "error",
                                "LLM Not Configured",
                                "LLM API key is missing. Please set LLM_API_KEY in backend .env file.",
                                "/dashboard/vault"
                              );
                            } else if (!diagnostics.extractor_available) {
                              console.error("[INGEST] Extractor is not available:", diagnostics.extractor_error);
                              createNotification(
                                "error",
                                "Extraction Failed",
                                `Extractor error: ${diagnostics.extractor_error || "Unknown error"}`,
                                "/dashboard/vault"
                              );
                            }
                          } catch (diagError) {
                            console.warn("[INGEST] Could not fetch diagnostics:", diagError);
                          }
                        }
                        
                        // Dispatch custom event to notify graph page to refresh
                        window.dispatchEvent(new CustomEvent('graph-data-updated', {
                          detail: {
                            entities_extracted: result.entities_extracted,
                            relations_extracted: result.relations_extracted,
                          }
                        }));
                        
                        // Show appropriate notification based on results
                        if (result.status === "skipped_duplicate") {
                          createNotification(
                            "info",
                            "File Already Processed",
                            `${file.filename} was already ingested (idempotency check).`,
                            "/dashboard/graph"
                          );
                        } else if (result.entities_extracted === 0) {
                          createNotification(
                            "warning",
                            "Ingestion Complete - No Entities",
                            `${file.filename} was ingested but no entities were extracted. Check the file content.`,
                            "/dashboard/graph"
                          );
                        } else {
                          createNotification(
                            "success",
                            "File Ingested",
                            `${file.filename} has been ingested. ${result.entities_extracted} entities and ${result.relations_extracted} relations extracted.`,
                            "/dashboard/graph"
                          );
                        }
                      } catch (error: any) {
                        // Fixed: Handle AbortError and other browser errors gracefully
                        if (error?.name === 'AbortError' || error?.message?.includes('play()') || error?.message?.includes('pause()')) {
                          // Suppress media-related browser errors (likely from extensions)
                          console.warn("Browser media error (non-critical):", error);
                          // Still show success if the actual ingestion succeeded
                          if (!error?.response) {
                            return;
                          }
                        }
                        
                        console.error("Failed to ingest file:", error);
                        
                        // Fixed: Extract detailed error message from response
                        let errorMessage = "Unknown error";
                        let errorTitle = "Ingestion Failed";
                        
                        if (error?.response?.status === 503) {
                          // Service Unavailable - usually means LLM not configured
                          errorTitle = "Service Unavailable";
                          if (error?.response?.data?.detail) {
                            errorMessage = error.response.data.detail;
                            // Check if it's an LLM API key issue
                            if (errorMessage.includes("LLM_API_KEY")) {
                              errorMessage = "LLM API key is not configured. Please set LLM_API_KEY in backend/.env file. See COMPLETE_SETUP_GUIDE.md for instructions.";
                            }
                          } else {
                            errorMessage = "Ingestion service is not available. The backend may be missing required configuration. Check backend logs for details.";
                          }
                        } else if (error?.response?.data) {
                          // Handle validation errors
                          if (error.response.data.errors && Array.isArray(error.response.data.errors)) {
                            const firstError = error.response.data.errors[0];
                            if (firstError.msg) {
                              errorMessage = `${firstError.loc?.join('.') || 'field'}: ${firstError.msg}`;
                            } else {
                              errorMessage = error.response.data.detail || error.response.data.message || "Validation error";
                            }
                          } else {
                            errorMessage = error.response.data.detail || error.response.data.message || "Unknown error";
                          }
                        } else if (error?.message) {
                          errorMessage = error.message;
                        }
                        
                        createNotification(
                          "error",
                          errorTitle,
                          `Failed to ingest ${file.filename}. ${errorMessage}`,
                          "/dashboard/vault"
                        );
                      } finally {
                        // Fixed: Clear ingesting state only if mutation was actually called
                        if (fileId !== null) {
                          setIngestingFileId(null);
                        }
                      }
                    }}
                    disabled={isIngesting || ingestMutation.isPending}
                    className="w-8 h-8 rounded-lg bg-glass-medium border border-glass-border flex items-center justify-center hover:bg-glass-light transition-all text-gray-400 hover:text-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Ingest into knowledge graph"
                  >
                    {isIngesting ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Brain className="w-4 h-4" />
                    )}
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        await vaultApi.openFilePreview(file.id);
                      } catch (error: any) {
                        console.error("Failed to open file preview:", error);
                        alert(`Failed to open file: ${error.message || "Unknown error"}`);
                      }
                    }}
                    className="w-8 h-8 rounded-lg bg-glass-medium border border-glass-border flex items-center justify-center hover:bg-glass-light transition-all text-gray-400 hover:text-cyan-400"
                    title="Preview file"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-slate-500 text-center py-12">No files uploaded yet</div>
      )}
    </div>
  );
}

