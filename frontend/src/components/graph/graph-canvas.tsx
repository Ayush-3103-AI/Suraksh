"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import dynamic from "next/dynamic";
import { GraphNode, GraphEdge } from "@/lib/api/search";
import { RotateCcw } from "lucide-react";

// Dynamically import react-force-graph to avoid SSR issues
const ForceGraph2D = dynamic(
  () => import("react-force-graph").then((mod) => mod.ForceGraph2D),
  { ssr: false }
);

interface GraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (node: GraphNode) => void;
  onNodeHover?: (node: GraphNode | null) => void;
  height?: number;
}

export function GraphCanvas({
  nodes,
  edges,
  onNodeClick,
  onNodeHover,
  height = 600,
}: GraphCanvasProps) {
  const graphRef = useRef<any>();
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // Color mapping for node types
  const getNodeColor = (label: string): string => {
    const colors: Record<string, string> = {
      PERSON: "#3b82f6", // Blue
      ORGANIZATION: "#ef4444", // Red
      LOCATION: "#10b981", // Green
      EVENT: "#f59e0b", // Amber
      DOCUMENT: "#8b5cf6", // Purple
    };
    return colors[label] || "#6b7280"; // Gray default
  };

  // Prepare graph data
  const graphData = useMemo(() => {
    const formattedNodes = nodes.map((node) => ({
      id: node.id,
      name: node.properties.name || node.id,
      label: node.label,
      color: getNodeColor(node.label),
    }));

    const formattedLinks = edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
      relation: edge.relation || "",
      color: "rgba(0, 242, 255, 0.3)",
    }));

    return {
      nodes: formattedNodes,
      links: formattedLinks,
    };
  }, [nodes, edges]);

  const handleReset = () => {
    if (graphRef.current) {
      // Reset zoom and center
      graphRef.current.zoom(1);
      graphRef.current.centerAt(0, 0);
      // Then fit to view
      setTimeout(() => {
        if (graphRef.current) {
          graphRef.current.zoomToFit(400, 20);
        }
      }, 100);
    }
  };

  return (
    <div className="w-full h-full bg-black rounded-lg border border-cyan-500/20 overflow-hidden relative">
      {/* Reset Button */}
      {nodes.length > 0 && (
        <button
          onClick={handleReset}
          className="absolute top-4 right-4 z-10 flex items-center gap-2 px-3 py-1.5 bg-cyber-cyan/20 border border-cyber-cyan/30 rounded-lg text-cyber-cyan hover:bg-cyber-cyan/30 hover:border-cyber-cyan/50 transition-all text-sm"
          title="Reset view to default orientation"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Reset View</span>
        </button>
      )}
      {nodes.length === 0 ? (
        <div className="flex items-center justify-center h-full text-slate-500">
          No graph data available. Search for entities to visualize connections.
        </div>
      ) : (
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          nodeLabel={(node: any) => `${node.name} (${node.label})`}
          nodeColor={(node: any) => node.color}
          nodeVal={(node: any) => 10}
          linkLabel={(link: any) => link.relation}
          linkDirectionalArrowLength={6}
          linkDirectionalArrowRelPos={1}
          linkColor={(link: any) => link.color}
          linkWidth={2}
          onNodeClick={(node: any) => {
            setSelectedNode(node);
            onNodeClick?.(node as GraphNode);
          }}
          onNodeHover={(node: any) => {
            onNodeHover?.(node as GraphNode | null);
          }}
          cooldownTicks={100}
          onEngineStop={() => {
            if (graphRef.current) {
              graphRef.current.zoomToFit(400, 20);
            }
          }}
          height={height}
          backgroundColor="#000000"
        />
      )}
      
      {selectedNode && (
        <div className="absolute bottom-4 left-4 right-4 bg-slate-900/90 border border-cyan-500/30 rounded-lg p-4 text-sm">
          <div className="font-semibold text-cyan-400 mb-2">
            {selectedNode.properties.name || selectedNode.id}
          </div>
          <div className="text-slate-400 space-y-1">
            <div>Type: {selectedNode.label}</div>
            {Object.entries(selectedNode.properties)
              .filter(([key]) => key !== "name" && key !== "id")
              .slice(0, 5)
              .map(([key, value]) => (
                <div key={key}>
                  {key}: {String(value)}
                </div>
              ))}
          </div>
          <button
            onClick={() => setSelectedNode(null)}
            className="mt-2 text-xs text-cyan-400 hover:text-cyan-300"
          >
            Close
          </button>
        </div>
      )}
    </div>
  );
}

