"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function ConnectionTest() {
  const [status, setStatus] = useState<"checking" | "connected" | "failed">("checking");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const testConnection = async () => {
      try {
        // Fixed: Add timeout and proper error handling for connection refused
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
        
        try {
          const directResponse = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
            signal: controller.signal,
          });
          
          clearTimeout(timeoutId);
          
          console.log('[DEBUG] Direct fetch response:', directResponse.status, directResponse.statusText);
          
          if (!directResponse.ok) {
            throw new Error(`HTTP ${directResponse.status}: ${directResponse.statusText}`);
          }
          
          const data = await directResponse.json();
          console.log('[DEBUG] Health check data:', data);
          
          setStatus("connected");
        } catch (fetchError: any) {
          clearTimeout(timeoutId);
          
          // Fixed: Handle connection refused gracefully without throwing to React error boundary
          if (fetchError.name === 'AbortError') {
            throw new Error('Connection timeout. Backend may not be running.');
          }
          
          // Fixed: Check for all network error types including ERR_CONNECTION_RESET
          const errorMessage = fetchError.message || '';
          const errorCode = fetchError.code || '';
          const errorString = `${errorMessage} ${errorCode}`.toLowerCase();
          
          if (errorMessage?.includes('Failed to fetch') || 
              errorMessage?.includes('ERR_CONNECTION_REFUSED') ||
              errorMessage?.includes('ERR_CONNECTION_RESET') ||
              errorMessage?.includes('NetworkError') ||
              errorCode?.includes('ERR_CONNECTION_REFUSED') ||
              errorCode?.includes('ERR_CONNECTION_RESET') ||
              errorCode?.includes('ECONNREFUSED') ||
              errorString.includes('connection') && (errorString.includes('reset') || errorString.includes('refused') || errorString.includes('failed'))) {
            throw new Error('Backend server is not running.');
          }
          
          throw fetchError;
        }
      } catch (err: any) {
        // Fixed: Use console.debug instead of console.error to prevent React error overlay
        const errorMessage = err?.message || 'Connection failed. Please ensure the backend is running on http://localhost:8000';
        
        // Only log to debug, not error level
        console.debug('[DEBUG] Backend connection failed:', errorMessage);
        
        setStatus("failed");
        setError(errorMessage);
      }
    };

    testConnection();
  }, []);

  if (status === "checking") {
    return (
      <div className="glass tech-border rounded-lg p-3">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse-slow"></div>
          <span className="text-cyan-400 text-sm font-mono">Checking backend connection...</span>
        </div>
      </div>
    );
  }

  if (status === "failed") {
    return (
      <div className="glass-strong border-2 border-crimson-500/50 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-2 h-2 rounded-full bg-crimson-500"></div>
          <div className="text-crimson-500 font-display uppercase tracking-wider text-sm font-semibold">
            Connection Failed
          </div>
        </div>
        <div className="text-xs text-slate-400 font-mono mb-2">{error}</div>
      </div>
    );
  }

  return (
    <div className="glass tech-border rounded-lg p-3">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse-slow"></div>
        <span className="text-cyan-400 text-sm font-mono">Backend Connected</span>
      </div>
    </div>
  );
}

