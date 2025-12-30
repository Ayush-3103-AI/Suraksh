"use client";

import { SearchInterface } from "@/components/search/search-interface";
import { GraphCanvas } from "@/components/graph/graph-canvas";
import { useState } from "react";
import { SearchResponse, GraphNode, GraphEdge, getGraphData } from "@/lib/api/search";

export default function IntelPage() {
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);

  const handleSearchComplete = async (result: SearchResponse) => {
    // If entities found, try to load graph data for the first entity
    if (result.entities_found.length > 0) {
      const entityName = result.entities_found[0];
      setSelectedEntity(entityName);
      try {
        const graphData = await getGraphData(entityName, 2);
        setGraphNodes(graphData.nodes);
        setGraphEdges(graphData.edges);
      } catch (error: any) {
        console.error("Failed to load graph data:", error);
      }
    }
  };

  const handleEntityClick = async (entityName: string) => {
    setSelectedEntity(entityName);
    try {
      const graphData = await getGraphData(entityName, 2);
      setGraphNodes(graphData.nodes);
      setGraphEdges(graphData.edges);
    } catch (error: any) {
      console.error("Failed to load graph data:", error);
    }
  };

  return (
    <div className="p-6 space-y-6 h-full flex flex-col">
      <div>
        <h1 className="text-3xl font-display uppercase tracking-wider text-cyan-400 mb-2">
          Deep Search & Analysis
        </h1>
        <p className="text-slate-500">Hybrid search with GraphRAG capabilities</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-0">
        {/* Left: Search Interface */}
        <div className="space-y-4 overflow-y-auto">
          <SearchInterface
            onSearchComplete={handleSearchComplete}
            onEntitiesFound={(entities) => {
              if (entities.length > 0) {
                handleEntityClick(entities[0]);
              }
            }}
          />
        </div>

        {/* Right: Graph Visualization */}
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-cyan-400 mb-2">
              Knowledge Graph
            </h2>
            {selectedEntity && (
              <p className="text-sm text-slate-500">
                Showing connections for: <span className="text-cyan-400">{selectedEntity}</span>
              </p>
            )}
          </div>
          <div className="flex-1 min-h-[600px]">
            <GraphCanvas
              nodes={graphNodes}
              edges={graphEdges}
              onNodeClick={(node) => {
                const nodeName = node.properties.name || node.id;
                handleEntityClick(nodeName);
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

