"use client";

import { useState } from "react";
import { Search, Loader2, Send } from "lucide-react";
import { search, SearchResponse } from "@/lib/api/search";
import { HoloCard } from "@/components/ui/holo-card";

interface SearchInterfaceProps {
  onSearchComplete?: (result: SearchResponse) => void;
  onEntitiesFound?: (entities: string[]) => void;
}

export function SearchInterface({
  onSearchComplete,
  onEntitiesFound,
}: SearchInterfaceProps) {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    // Fixed: Validate query length before sending request
    if (!query.trim() || isSearching) return;
    if (query.trim().length < 3) {
      setError("Query must be at least 3 characters long");
      return;
    }

    setIsSearching(true);
    setError(null);
    setResult(null);

    try {
      const searchResult = await search(query, 5);
      setResult(searchResult);
      onSearchComplete?.(searchResult);
      onEntitiesFound?.(searchResult.entities_found);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Search failed");
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <div className="space-y-4">
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-slate-500" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question... (e.g., 'How is Person X connected to Location Y?')"
          className="w-full pl-12 pr-12 py-3 bg-slate-900/50 border border-cyan-500/20 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20"
          disabled={isSearching}
        />
        <button
          onClick={handleSearch}
          disabled={isSearching || !query.trim() || query.trim().length < 3}
          className="absolute inset-y-0 right-0 pr-4 flex items-center text-cyan-400 hover:text-cyan-300 disabled:text-slate-600 disabled:cursor-not-allowed"
        >
          {isSearching ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Send className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Search Results */}
      {result && (
        <div className="space-y-4">
          {/* Answer */}
          <HoloCard>
            <div className="space-y-3">
              <div className="text-sm text-slate-400 uppercase tracking-wider">
                Answer
              </div>
              <div className="text-slate-200 leading-relaxed">
                {result.answer}
              </div>
            </div>
          </HoloCard>

          {/* Graph Path Info */}
          {result.graph_path.path_found && (
            <HoloCard>
              <div className="space-y-2">
                <div className="text-sm text-slate-400 uppercase tracking-wider">
                  Graph Path Found
                </div>
                <div className="text-slate-300">
                  Path length: {result.graph_path.path_length} relationships
                </div>
                <div className="text-slate-400 text-sm">
                  Entities: {result.graph_path.entities.join(", ")}
                </div>
              </div>
            </HoloCard>
          )}

          {/* Entities Found */}
          {result.entities_found.length > 0 && (
            <HoloCard>
              <div className="space-y-2">
                <div className="text-sm text-slate-400 uppercase tracking-wider">
                  Entities Identified
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.entities_found.map((entity, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 rounded text-cyan-400 text-sm"
                    >
                      {entity}
                    </span>
                  ))}
                </div>
              </div>
            </HoloCard>
          )}

          {/* Reasoning */}
          {result.reasoning && (
            <HoloCard>
              <div className="space-y-2">
                <div className="text-sm text-slate-400 uppercase tracking-wider">
                  Reasoning
                </div>
                <div className="text-slate-300 text-sm">{result.reasoning}</div>
              </div>
            </HoloCard>
          )}
        </div>
      )}
    </div>
  );
}

