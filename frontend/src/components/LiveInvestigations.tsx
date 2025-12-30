"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Search, Clock, CheckCircle2, XCircle, Loader2 } from "lucide-react";

interface Investigation {
  query: string;
  timestamp: string;
  status: "pending" | "completed" | "failed";
}

export default function LiveInvestigations() {
  const router = useRouter();
  const [investigations, setInvestigations] = useState<Investigation[]>([]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const loadInvestigations = () => {
      try {
        const stored = localStorage.getItem("recent-queries");
        if (stored) {
          const parsed = JSON.parse(stored);
          // Filter to only completed investigations and sort by most recent
          const completedInvestigations = parsed
            .filter((inv: Investigation) => inv.status === "completed")
            .sort((a: Investigation, b: Investigation) => 
              new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
            )
            .slice(0, 5); // Show only the 5 most recent
          setInvestigations(completedInvestigations);
        }
      } catch (e) {
        console.error("Failed to load investigations:", e);
      }
    };

    loadInvestigations();

    // Listen for storage changes to update in real-time
    const handleStorageChange = () => {
      loadInvestigations();
    };

    window.addEventListener("storage", handleStorageChange);
    // Also check periodically for changes (in case same-tab updates)
    const interval = setInterval(loadInvestigations, 2000);

    return () => {
      window.removeEventListener("storage", handleStorageChange);
      clearInterval(interval);
    };
  }, []);

  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const handleInvestigationClick = (query: string) => {
    router.push(`/dashboard/search?query=${encodeURIComponent(query)}`);
  };

  const getStatusIcon = (status: Investigation["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-4 h-4 text-cyber-green" />;
      case "pending":
        return <Loader2 className="w-4 h-4 text-cyber-cyan animate-spin" />;
      case "failed":
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div className="h-full bg-glass-light backdrop-blur-md border border-glass-border rounded-2xl p-6 flex flex-col">
      <div className="flex items-center justify-between mb-6 h-14">
        <h2 className="text-sm font-bold tracking-wider text-gray-400 flex items-center">
          LIVE INVESTIGATIONS
        </h2>
        <button className="text-gray-500 hover:text-white transition-colors flex items-center h-6">
          •••
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3">
        {investigations.length > 0 ? (
          investigations.map((investigation, idx) => (
            <button
              key={idx}
              onClick={() => handleInvestigationClick(investigation.query)}
              className="w-full text-left p-4 rounded-xl bg-glass-medium border border-glass-border hover:border-cyber-cyan/50 hover:bg-glass-light transition-all group cursor-pointer"
            >
              <div className="flex items-start gap-3 mb-2">
                <div className="flex-shrink-0 mt-0.5">
                  <Search className="w-4 h-4 text-gray-500 group-hover:text-cyber-cyan transition-colors" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white group-hover:text-cyber-cyan transition-colors line-clamp-2">
                    {investigation.query}
                  </p>
                </div>
                <div className="flex-shrink-0">
                  {getStatusIcon(investigation.status)}
                </div>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500 ml-7">
                <Clock className="w-3 h-3" />
                <span>{formatTimeAgo(investigation.timestamp)}</span>
              </div>
            </button>
          ))
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <Search className="w-12 h-12 text-slate-700/50 mb-4" />
            <p className="text-slate-500 text-sm">No recent investigations</p>
            <p className="text-slate-600 text-xs mt-1">
              Start a new investigation to see it here
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

