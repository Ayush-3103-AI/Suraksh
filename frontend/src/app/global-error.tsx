"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-space text-white">
        <div className="min-h-screen flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-glass-light border border-crimson-500/30 rounded-lg p-6">
            <h2 className="text-xl font-display text-crimson-500 mb-4">
              Application Error
            </h2>
            <p className="text-slate-400 mb-4">
              {error.message || "A critical error occurred"}
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
                Reload
              </button>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}

