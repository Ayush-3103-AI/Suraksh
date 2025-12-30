"use client";

import { useEffect, useRef, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { RotateCcw, Maximize } from "lucide-react";

// Dynamically import react-force-graph-3d to avoid SSR issues
const ForceGraph3D = dynamic(
  () => import("react-force-graph-3d").then((mod) => mod.default || mod),
  { ssr: false }
);

interface MockNode {
  id: string;
  name: string;
  type: "case" | "suspect" | "officer" | "location" | "evidence" | "document";
  caseId?: string;
  x?: number;
  y?: number;
  z?: number;
  color: string;
  size: number;
}

interface MockLink {
  source: string;
  target: string;
  relation: string;
  color: string;
}

interface GraphData {
  nodes: MockNode[];
  links: MockLink[];
}

// Entity type color mapping
const ENTITY_COLORS = {
  case: "#00F2FF", // Cyan for case centers
  suspect: "#FF0055", // Red
  officer: "#3b82f6", // Blue
  location: "#00FF88", // Green
  evidence: "#BC00FF", // Purple
  document: "#6b7280", // Gray
};

// Generate mock data with clustering logic
function generateMockData(): GraphData {
  const nodes: MockNode[] = [];
  const links: MockLink[] = [];
  const nodeMap = new Map<string, MockNode>();

  // Generate 18 case centers
  const numCases = 18;
  const cases: MockNode[] = [];

  for (let i = 0; i < numCases; i++) {
    const caseId = `CASE-2024-${String(i + 1).padStart(3, "0")}`;
    const caseNode: MockNode = {
      id: `case-${i}`,
      name: caseId,
      type: "case",
      caseId,
      color: ENTITY_COLORS.case,
      size: 15,
    };
    cases.push(caseNode);
    nodes.push(caseNode);
    nodeMap.set(caseNode.id, caseNode);
  }

  // Generate entities around each case center
  let nodeIdCounter = numCases;
  const entitiesPerCase = 170; // ~170 nodes per case to reach ~3,000 total

  cases.forEach((caseNode, caseIndex) => {
    const caseId = caseNode.caseId!;
    const caseEntities: MockNode[] = [caseNode];

    // Generate suspects (30-40 per case)
    const numSuspects = 30 + Math.floor(Math.random() * 11);
    for (let i = 0; i < numSuspects; i++) {
      const suspectNode: MockNode = {
        id: `node-${nodeIdCounter++}`,
        name: `Suspect-${caseId}-${i + 1}`,
        type: "suspect",
        caseId,
        color: ENTITY_COLORS.suspect,
        size: 6 + Math.random() * 3,
      };
      caseEntities.push(suspectNode);
      nodes.push(suspectNode);
      nodeMap.set(suspectNode.id, suspectNode);

      // Link suspect to case
      links.push({
        source: caseNode.id,
        target: suspectNode.id,
        relation: "investigates",
        color: "rgba(255, 0, 85, 0.3)",
      });
    }

    // Generate officers (20-30 per case)
    const numOfficers = 20 + Math.floor(Math.random() * 11);
    for (let i = 0; i < numOfficers; i++) {
      const officerNode: MockNode = {
        id: `node-${nodeIdCounter++}`,
        name: `Officer-${caseId}-${i + 1}`,
        type: "officer",
        caseId,
        color: ENTITY_COLORS.officer,
        size: 5 + Math.random() * 2,
      };
      caseEntities.push(officerNode);
      nodes.push(officerNode);
      nodeMap.set(officerNode.id, officerNode);

      // Link officer to case
      links.push({
        source: caseNode.id,
        target: officerNode.id,
        relation: "assigned_to",
        color: "rgba(59, 130, 246, 0.3)",
      });
    }

    // Generate locations (25-35 per case)
    const numLocations = 25 + Math.floor(Math.random() * 11);
    for (let i = 0; i < numLocations; i++) {
      const locationNode: MockNode = {
        id: `node-${nodeIdCounter++}`,
        name: `Location-${caseId}-${i + 1}`,
        type: "location",
        caseId,
        color: ENTITY_COLORS.location,
        size: 5 + Math.random() * 2,
      };
      caseEntities.push(locationNode);
      nodes.push(locationNode);
      nodeMap.set(locationNode.id, locationNode);

      // Link location to case
      links.push({
        source: caseNode.id,
        target: locationNode.id,
        relation: "occurred_at",
        color: "rgba(0, 255, 136, 0.3)",
      });
    }

    // Generate evidence (40-50 per case)
    const numEvidence = 40 + Math.floor(Math.random() * 11);
    for (let i = 0; i < numEvidence; i++) {
      const evidenceNode: MockNode = {
        id: `node-${nodeIdCounter++}`,
        name: `Evidence-${caseId}-${i + 1}`,
        type: "evidence",
        caseId,
        color: ENTITY_COLORS.evidence,
        size: 4 + Math.random() * 2,
      };
      caseEntities.push(evidenceNode);
      nodes.push(evidenceNode);
      nodeMap.set(evidenceNode.id, evidenceNode);

      // Link evidence to case
      links.push({
        source: caseNode.id,
        target: evidenceNode.id,
        relation: "contains",
        color: "rgba(188, 0, 255, 0.3)",
      });
    }

    // Generate documents (25-35 per case)
    const numDocuments = 25 + Math.floor(Math.random() * 11);
    for (let i = 0; i < numDocuments; i++) {
      const documentNode: MockNode = {
        id: `node-${nodeIdCounter++}`,
        name: `Doc-${caseId}-${i + 1}`,
        type: "document",
        caseId,
        color: ENTITY_COLORS.document,
        size: 3 + Math.random() * 2,
      };
      caseEntities.push(documentNode);
      nodes.push(documentNode);
      nodeMap.set(documentNode.id, documentNode);

      // Link document to case
      links.push({
        source: caseNode.id,
        target: documentNode.id,
        relation: "references",
        color: "rgba(107, 114, 128, 0.3)",
      });
    }

    // Create internal connections within the case (suspects connected to evidence, locations, etc.)
    const suspects = caseEntities.filter((e) => e.type === "suspect");
    const evidence = caseEntities.filter((e) => e.type === "evidence");
    const locations = caseEntities.filter((e) => e.type === "location");

    // Connect suspects to evidence (30-40% of suspects get evidence links)
    suspects.forEach((suspect) => {
      if (Math.random() < 0.35) {
        const randomEvidence =
          evidence[Math.floor(Math.random() * evidence.length)];
        if (randomEvidence) {
          links.push({
            source: suspect.id,
            target: randomEvidence.id,
            relation: "linked_to",
            color: "rgba(255, 0, 85, 0.2)",
          });
        }
      }
    });

    // Connect suspects to locations (20-30% of suspects get location links)
    suspects.forEach((suspect) => {
      if (Math.random() < 0.25) {
        const randomLocation =
          locations[Math.floor(Math.random() * locations.length)];
        if (randomLocation) {
          links.push({
            source: suspect.id,
            target: randomLocation.id,
            relation: "seen_at",
            color: "rgba(0, 255, 136, 0.2)",
          });
        }
      }
    });

    // Connect officers to suspects (40-50% of officers get suspect links)
    const officers = caseEntities.filter((e) => e.type === "officer");
    officers.forEach((officer) => {
      if (Math.random() < 0.45) {
        const randomSuspect =
          suspects[Math.floor(Math.random() * suspects.length)];
        if (randomSuspect) {
          links.push({
            source: officer.id,
            target: randomSuspect.id,
            relation: "investigates",
            color: "rgba(59, 130, 246, 0.2)",
          });
        }
      }
    });
  });

  // Create bridge nodes connecting different cases (cross-agency intelligence)
  // Select 15-20 suspects to be bridge nodes (involved in multiple cases)
  const allSuspects = nodes.filter((n) => n.type === "suspect");
  const bridgeSuspects = allSuspects
    .sort(() => Math.random() - 0.5)
    .slice(0, 18);

  bridgeSuspects.forEach((bridgeSuspect, idx) => {
    // Each bridge suspect connects to 1-2 other cases
    const numConnections = 1 + Math.floor(Math.random() * 2);
    const otherCases = cases.filter((c) => c.caseId !== bridgeSuspect.caseId);

    for (let i = 0; i < numConnections && i < otherCases.length; i++) {
      const targetCase = otherCases[Math.floor(Math.random() * otherCases.length)];
      // Find a suspect in the target case to connect to
      const targetSuspects = nodes.filter(
        (n) => n.type === "suspect" && n.caseId === targetCase.caseId
      );
      if (targetSuspects.length > 0) {
        const targetSuspect =
          targetSuspects[Math.floor(Math.random() * targetSuspects.length)];
        links.push({
          source: bridgeSuspect.id,
          target: targetSuspect.id,
          relation: "cross_case_link",
          color: "rgba(255, 255, 0, 0.4)", // Yellow for cross-case links
        });
      }
    }
  });

  return { nodes, links };
}

interface TerabyteKGProps {
  isFullscreen?: boolean;
  onFullscreenClick?: () => void;
}

export function TerabyteKG({ isFullscreen = false, onFullscreenClick }: TerabyteKGProps) {
  const graphRef = useRef<any>();
  const [hoveredNode, setHoveredNode] = useState<MockNode | null>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  // Generate mock data once using useMemo
  const graphData = useMemo(() => generateMockData(), []);

  useEffect(() => {
    // Auto-fit the graph after a short delay
    if (graphRef.current) {
      const timer = setTimeout(() => {
        graphRef.current.cameraPosition({ x: 0, y: 0, z: 300 });
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  // Track mouse position for tooltip
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const handleNodeHover = (node: any) => {
    if (node) {
      setHoveredNode(node);
    } else {
      setHoveredNode(null);
    }
  };

  const handleBackgroundClick = () => {
    setHoveredNode(null);
  };

  const handleReset = () => {
    if (graphRef.current) {
      graphRef.current.cameraPosition({ x: 0, y: 0, z: 300 });
    }
  };

  return (
    <div className="w-full h-full relative bg-black rounded-lg border border-cyan-500/20 overflow-hidden">
      {/* Header Overlay */}
      <div className="absolute top-4 left-4 right-4 z-10 pointer-events-none">
        <div className="bg-slate-900/90 backdrop-blur-md border border-cyan-500/30 rounded-lg px-4 py-2 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-display uppercase tracking-wider text-cyan-400">
              TERABYTE-SCALE INTELLIGENCE GRAPH [SIMULATION]
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              {graphData.nodes.length.toLocaleString()} nodes •{" "}
              {graphData.links.length.toLocaleString()} connections •{" "}
              {new Set(graphData.nodes.map((n) => n.caseId).filter(Boolean)).size}{" "}
              active cases
            </p>
          </div>
          <div className="flex items-center gap-2 pointer-events-auto">
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-3 py-1.5 bg-cyber-cyan/20 border border-cyber-cyan/30 rounded-lg text-cyber-cyan hover:bg-cyber-cyan/30 hover:border-cyber-cyan/50 transition-all text-sm"
              title="Reset view to default orientation"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reset View</span>
            </button>
            {!isFullscreen && onFullscreenClick && (
              <button
                onClick={onFullscreenClick}
                className="flex items-center gap-2 px-3 py-1.5 bg-cyber-cyan/20 border border-cyber-cyan/30 rounded-lg text-cyber-cyan hover:bg-cyber-cyan/30 hover:border-cyber-cyan/50 transition-all text-sm"
                title="View in fullscreen"
              >
                <Maximize className="w-4 h-4" />
                <span>Fullscreen</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 pointer-events-none">
        <div className="bg-slate-900/90 backdrop-blur-md border border-cyan-500/30 rounded-lg px-4 py-3">
          <div className="text-xs font-semibold text-cyan-400 mb-2 uppercase tracking-wider">
            Entity Types
          </div>
          <div className="space-y-1.5 text-xs">
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: ENTITY_COLORS.case }}
              />
              <span className="text-slate-300">Case Centers</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: ENTITY_COLORS.suspect }}
              />
              <span className="text-slate-300">Suspects</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: ENTITY_COLORS.officer }}
              />
              <span className="text-slate-300">Officers</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: ENTITY_COLORS.location }}
              />
              <span className="text-slate-300">Locations</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: ENTITY_COLORS.evidence }}
              />
              <span className="text-slate-300">Evidence</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: ENTITY_COLORS.document }}
              />
              <span className="text-slate-300">Documents</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3D Graph */}
      <ForceGraph3D
        ref={graphRef}
        graphData={graphData}
        nodeLabel={(node: any) => {
          const mockNode = node as MockNode;
          return `${mockNode.caseId || "Unknown"}: ${mockNode.name} (${mockNode.type})`;
        }}
        nodeColor={(node: any) => (node as MockNode).color}
        nodeVal={(node: any) => (node as MockNode).size}
        linkLabel={(link: any) => link.relation}
        linkColor={(link: any) => link.color}
        linkWidth={2.5}
        linkOpacity={0.6}
        linkDirectionalArrowLength={5}
        linkDirectionalArrowRelPos={1}
        onNodeHover={handleNodeHover}
        onBackgroundClick={handleBackgroundClick}
        backgroundColor="#000000"
        showNavInfo={false}
        nodeOpacity={0.9}
        nodeResolution={16}
      />

      {/* Hover Tooltip - positioned at mouse */}
      {hoveredNode && (
        <div
          className="fixed z-50 bg-slate-900/95 backdrop-blur-md border border-cyan-500/50 rounded-lg px-3 py-2 pointer-events-none shadow-lg"
          style={{
            left: `${mousePosition.x}px`,
            top: `${mousePosition.y}px`,
            transform: "translate(-50%, -100%)",
            marginTop: "-10px",
          }}
        >
          <div className="text-sm font-semibold text-cyan-400">
            {hoveredNode.caseId || "Unknown"}: {hoveredNode.name}
          </div>
          <div className="text-xs text-slate-400 mt-1 capitalize">
            Type: {hoveredNode.type}
          </div>
        </div>
      )}
    </div>
  );
}

