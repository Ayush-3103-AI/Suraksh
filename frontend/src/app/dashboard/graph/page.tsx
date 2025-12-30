"use client";

import { GraphCanvas } from "@/components/graph/graph-canvas";
import { TerabyteKG } from "@/components/graph/TerabyteKG";
import { CaseDetailKG } from "@/components/graph/CaseDetailKG";
import { useState, useEffect, useTransition, useCallback } from "react";
import { GraphNode, GraphEdge, getGraphData, getAllGraphData } from "@/lib/api/search";
import { Search, ZoomIn, ZoomOut, Maximize, Minimize, Filter, Network, Loader2, Database, FileText } from "lucide-react";

type TabType = "current" | "terabytes" | "case-detail";

export default function GraphPage() {
  const [activeTab, setActiveTab] = useState<TabType>("current");
  const [isPending, startTransition] = useTransition();
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);
  const [entityName, setEntityName] = useState("");
  const [depth, setDepth] = useState(2);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Auto-load all entities on mount
  useEffect(() => {
    loadAllGraphData();
  }, []);

  // Listen for graph data updates (e.g., after file ingestion)
  useEffect(() => {
    const handleGraphUpdate = (event: CustomEvent) => {
      console.log("[GRAPH] Graph data updated, refreshing...", event.detail);
      // Refresh graph data when ingestion completes
      loadAllGraphData();
    };

    window.addEventListener('graph-data-updated', handleGraphUpdate as EventListener);
    
    return () => {
      window.removeEventListener('graph-data-updated', handleGraphUpdate as EventListener);
    };
  }, []);

  const loadAllGraphData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      console.log("[GRAPH] Loading all graph data...");
      const graphData = await getAllGraphData(200);
      console.log("[GRAPH] Graph data loaded:", {
        nodes: graphData.nodes.length,
        edges: graphData.edges.length,
      });
      setGraphNodes(graphData.nodes);
      setGraphEdges(graphData.edges);
      
      if (graphData.nodes.length === 0 && graphData.edges.length === 0) {
        console.warn("[GRAPH] No graph data found. Make sure files have been ingested.");
      }
    } catch (err: any) {
      console.error("[GRAPH] Failed to load graph data:", err);
      // If no entities exist yet, that's okay - just show empty state
      if (err.response?.status !== 404) {
        setError(err.response?.data?.detail || err.message || "Failed to load graph");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadGraph = async () => {
    if (!entityName.trim()) {
      // If empty, load all entities
      await loadAllGraphData();
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const graphData = await getGraphData(entityName, depth);
      setGraphNodes(graphData.nodes);
      setGraphEdges(graphData.edges);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to load graph");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleLoadGraph();
    }
  };

  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen);
  }, [isFullscreen]);

  // Optimized tab switching with transition for non-blocking updates
  const handleTabChange = useCallback((tab: TabType) => {
    startTransition(() => {
      setActiveTab(tab);
    });
  }, []);

  return (
    <>
      {/* Fullscreen Overlay */}
      {isFullscreen && (
        <div className="fixed inset-0 z-50 bg-black flex flex-col">
          <div className="flex items-center justify-between p-4 bg-slate-900/90 backdrop-blur-md border-b border-cyan-500/30">
            <div>
              <h1 className="text-2xl font-display uppercase tracking-wider text-white">
                KNOWLEDGE GRAPH EXPLORER - FULLSCREEN
              </h1>
              <p className="text-slate-400 text-sm">
                {activeTab === "current" ? "Current Graph" : activeTab === "terabytes" ? "Terabytes KG" : "Case Detail View"}
              </p>
            </div>
            <button
              onClick={toggleFullscreen}
              className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400 hover:bg-cyan-500/20 transition-all flex items-center gap-2"
            >
              <Minimize className="w-4 h-4" />
              <span>Exit Fullscreen</span>
            </button>
          </div>
          <div className="flex-1 relative overflow-hidden">
            {/* Current Graph Tab - Keep mounted, use visibility */}
            <div 
              className={`absolute inset-0 transition-opacity duration-200 ${
                activeTab === "current" ? "opacity-100 z-10" : "opacity-0 z-0 pointer-events-none"
              }`}
            >
              {isLoading ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-center space-y-4">
                    <Loader2 className="w-12 h-12 text-cyan-500 animate-spin mx-auto" />
                    <p className="text-slate-400 text-lg">Loading graph data...</p>
                  </div>
                </div>
              ) : graphNodes.length === 0 && graphEdges.length === 0 ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-center space-y-4">
                    <div className="flex justify-center">
                      <Network className="w-24 h-24 text-cyan-500/30" />
                    </div>
                    <div className="space-y-2">
                      <p className="text-slate-400 text-lg">Graph Visualization Canvas</p>
                      <p className="text-slate-600 text-sm">
                        No entities found. Upload files to the vault and ingest them to populate the graph.
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <GraphCanvas
                  nodes={graphNodes}
                  edges={graphEdges}
                  onNodeClick={(node) => {
                    const nodeName = node.properties.name || node.id;
                    setEntityName(nodeName);
                    handleLoadGraph();
                  }}
                />
              )}
            </div>

            {/* Terabytes KG Tab - Keep mounted, use visibility */}
            <div 
              className={`absolute inset-0 transition-opacity duration-200 ${
                activeTab === "terabytes" ? "opacity-100 z-10" : "opacity-0 z-0 pointer-events-none"
              }`}
            >
              <TerabyteKG isFullscreen={true} />
            </div>

            {/* Case Detail KG Tab - Keep mounted, use visibility */}
            <div 
              className={`absolute inset-0 transition-opacity duration-200 ${
                activeTab === "case-detail" ? "opacity-100 z-10" : "opacity-0 z-0 pointer-events-none"
              }`}
            >
              <CaseDetailKG isFullscreen={true} />
            </div>
          </div>
        </div>
      )}

      {/* Normal View */}
      <div className="h-full overflow-y-auto p-8 space-y-6 pb-12">
        <div>
          <h1 className="text-4xl font-display uppercase tracking-wider text-white mb-2">
            KNOWLEDGE GRAPH EXPLORER
          </h1>
          <p className="text-slate-500 text-lg">
            Deep link analysis and pathfinding visualization
          </p>
        </div>

      {/* Search Bar - only show for current graph */}
      {activeTab === "current" && (
      <div className="flex gap-4 items-center">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            value={entityName}
            onChange={(e) => setEntityName(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Search for entity (leave empty to show all entities)..."
            className="w-full pl-10 pr-4 py-3 bg-glass-light border border-glass-border rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-slate-400 text-sm">Depth:</label>
          <input
            type="number"
            min="1"
            max="5"
            value={depth}
            onChange={(e) => setDepth(parseInt(e.target.value) || 2)}
            className="w-16 px-2 py-1 bg-glass-light border border-glass-border rounded text-white text-sm focus:outline-none focus:border-cyan-500/50"
          />
        </div>
        <button
          onClick={handleLoadGraph}
          disabled={isLoading}
          className="px-6 py-3 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400 hover:bg-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Loading...</span>
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              <span>Search</span>
            </>
          )}
        </button>
        <button
          onClick={loadAllGraphData}
          disabled={isLoading}
          className="px-4 py-3 bg-glass-light border border-glass-border rounded-lg text-slate-300 hover:bg-glass-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          title="Refresh graph data (auto-refreshes after file ingestion)"
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
          <Network className="w-4 h-4" />
          )}
          <span>Refresh</span>
        </button>
      </div>
      )}

      {/* Error Message */}
      {error && activeTab === "current" && (
        <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-glass-border">
        <button
          onClick={() => handleTabChange("current")}
          disabled={isPending}
          className={`px-6 py-3 font-medium transition-all relative flex items-center gap-2 ${
            activeTab === "current"
              ? "text-cyber-cyan border-b-2 border-cyber-cyan"
              : "text-slate-500 hover:text-slate-300"
          } ${isPending ? "opacity-50 cursor-wait" : ""}`}
        >
          <Network className="w-5 h-5" />
          <span>Current Graph</span>
        </button>
        <button
          onClick={() => handleTabChange("terabytes")}
          disabled={isPending}
          className={`px-6 py-3 font-medium transition-all relative flex items-center gap-2 ${
            activeTab === "terabytes"
              ? "text-cyber-cyan border-b-2 border-cyber-cyan"
              : "text-slate-500 hover:text-slate-300"
          } ${isPending ? "opacity-50 cursor-wait" : ""}`}
        >
          <Database className="w-5 h-5" />
          <span>Terabytes KG</span>
        </button>
        <button
          onClick={() => handleTabChange("case-detail")}
          disabled={isPending}
          className={`px-6 py-3 font-medium transition-all relative flex items-center gap-2 ${
            activeTab === "case-detail"
              ? "text-cyber-cyan border-b-2 border-cyber-cyan"
              : "text-slate-500 hover:text-slate-300"
          } ${isPending ? "opacity-50 cursor-wait" : ""}`}
        >
          <FileText className="w-5 h-5" />
          <span>Case Detail View</span>
        </button>
      </div>

      {/* Control Buttons - Top Right */}
      <div className="flex justify-end gap-2">
        {activeTab === "current" && (
          <>
            <button
              className="w-10 h-10 rounded-full bg-glass-medium border border-glass-border flex items-center justify-center hover:bg-glass-light transition-all text-gray-400 hover:text-white"
              title="Zoom In"
            >
              <ZoomIn className="w-5 h-5" />
            </button>
            <button
              className="w-10 h-10 rounded-full bg-glass-medium border border-glass-border flex items-center justify-center hover:bg-glass-light transition-all text-gray-400 hover:text-white"
              title="Zoom Out"
            >
              <ZoomOut className="w-5 h-5" />
            </button>
            <button
              className="w-10 h-10 rounded-full bg-glass-medium border border-glass-border flex items-center justify-center hover:bg-glass-light transition-all text-gray-400 hover:text-white"
              title="Filter"
            >
              <Filter className="w-5 h-5" />
            </button>
          </>
        )}
        <button
          onClick={toggleFullscreen}
          className="w-10 h-10 rounded-full bg-glass-medium border border-glass-border flex items-center justify-center hover:bg-glass-light transition-all text-gray-400 hover:text-white"
          title="Fullscreen"
        >
          <Maximize className="w-5 h-5" />
        </button>
      </div>

      {/* Graph Canvas - Using CSS visibility instead of conditional rendering for better performance */}
      <div className="h-[900px] relative bg-glass-light backdrop-blur-md border border-glass-border rounded-2xl overflow-hidden">
        {/* Current Graph Tab - Keep mounted, use visibility */}
        <div 
          className={`absolute inset-0 transition-opacity duration-200 ${
            activeTab === "current" ? "opacity-100 z-10" : "opacity-0 z-0 pointer-events-none"
          }`}
        >
          {isLoading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <div className="text-center space-y-4">
                <Loader2 className="w-12 h-12 text-cyan-500 animate-spin mx-auto" />
                <p className="text-slate-400 text-lg">Loading graph data...</p>
              </div>
            </div>
          ) : graphNodes.length === 0 && graphEdges.length === 0 ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <div className="text-center space-y-4">
                <div className="flex justify-center">
                  <Network className="w-24 h-24 text-cyan-500/30" />
                </div>
                <div className="space-y-2">
                  <p className="text-slate-400 text-lg">Graph Visualization Canvas</p>
                  <p className="text-slate-600 text-sm">
                    No entities found. Upload files to the vault and ingest them to populate the graph.
                  </p>
                  <p className="text-slate-600 text-xs mt-4">
                    Or search for a specific entity name above.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <GraphCanvas
              nodes={graphNodes}
              edges={graphEdges}
              onNodeClick={(node) => {
                const nodeName = node.properties.name || node.id;
                setEntityName(nodeName);
                handleLoadGraph();
              }}
            />
          )}
        </div>

        {/* Terabytes KG Tab - Keep mounted, use visibility */}
        <div 
          className={`absolute inset-0 transition-opacity duration-200 ${
            activeTab === "terabytes" ? "opacity-100 z-10" : "opacity-0 z-0 pointer-events-none"
          }`}
        >
          <TerabyteKG isFullscreen={false} onFullscreenClick={toggleFullscreen} />
        </div>

        {/* Case Detail KG Tab - Keep mounted, use visibility */}
        <div 
          className={`absolute inset-0 transition-opacity duration-200 ${
            activeTab === "case-detail" ? "opacity-100 z-10" : "opacity-0 z-0 pointer-events-none"
          }`}
        >
          <CaseDetailKG isFullscreen={false} onFullscreenClick={toggleFullscreen} />
        </div>
      </div>
    </div>
    </>
  );
}

