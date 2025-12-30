"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error to console for debugging
    console.error("Application error:", error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-space p-4">
      <div className="max-w-md w-full bg-glass-light border border-crimson-500/30 rounded-lg p-6">
        <h2 className="text-xl font-display text-crimson-500 mb-4">
          Something went wrong
        </h2>
        <p className="text-slate-400 mb-4">
          {error.message || "An unexpected error occurred"}
        </p>
        {error.digest && (
          <p className="text-xs text-slate-500 mb-4">Error ID: {error.digest}</p>
        )}
        <div className="flex gap-3">
          <button
            onClick={reset}
            className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400 hover:bg-cyan-500/20 transition-colors"
          >
            Try again
          </button>
          <button
            onClick={() => {
              window.location.href = "/";
            }}
            className="px-4 py-2 bg-slate-500/10 border border-slate-500/30 rounded-lg text-slate-400 hover:bg-slate-500/20 transition-colors"
          >
            Go home
          </button>
        </div>
      </div>
    </div>
  );
}

