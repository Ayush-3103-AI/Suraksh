"use client";

import { useEffect, useRef, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { RotateCcw, Maximize } from "lucide-react";

// Dynamically import react-force-graph-3d to avoid SSR issues
const ForceGraph3D = dynamic(
  () => import("react-force-graph-3d").then((mod) => mod.default || mod),
  { ssr: false }
);

interface CaseNode {
  id: string;
  name: string;
  type: "case" | "fir" | "suspect" | "officer" | "location" | "evidence" | "document" | "criminal_record" | "witness" | "vehicle" | "weapon";
  caseId?: string;
  x?: number;
  y?: number;
  z?: number;
  color: string;
  size: number;
}

interface CaseLink {
  source: string;
  target: string;
  relation: string;
  color: string;
  isCrossCase?: boolean; // Flag for cross-case connections
}

interface CaseGraphData {
  nodes: CaseNode[];
  links: CaseLink[];
}

// Entity type color mapping
const CASE_ENTITY_COLORS = {
  case: "#00F2FF", // Cyan for case center
  fir: "#FF6B00", // Orange for FIR
  suspect: "#FF0055", // Red
  officer: "#3b82f6", // Blue
  location: "#00FF88", // Green
  evidence: "#BC00FF", // Purple
  document: "#6b7280", // Gray
  criminal_record: "#FF1744", // Deep Red
  witness: "#FFC107", // Amber
  vehicle: "#9C27B0", // Deep Purple
  weapon: "#F44336", // Red-Orange
};

// Generate detailed case data showing real-world connections
function generateCaseDetailData(): CaseGraphData {
  const nodes: CaseNode[] = [];
  const links: CaseLink[] = [];

  // Central Case Node
  const caseNode: CaseNode = {
    id: "case-001",
    name: "CASE-2024-042: Organized Crime Investigation",
    type: "case",
    caseId: "CASE-2024-042",
    color: CASE_ENTITY_COLORS.case,
    size: 20,
  };
  nodes.push(caseNode);

  // FIR Documents (3 FIRs)
  const firNodes: CaseNode[] = [];
  for (let i = 1; i <= 3; i++) {
    const firNode: CaseNode = {
      id: `fir-${i}`,
      name: `FIR-${2024}-RC-${String(i).padStart(3, "0")}`,
      type: "fir",
      caseId: "CASE-2024-042",
      color: CASE_ENTITY_COLORS.fir,
      size: 12,
    };
    firNodes.push(firNode);
    nodes.push(firNode);
    links.push({
      source: caseNode.id,
      target: firNode.id,
      relation: "registered_as",
      color: "rgba(255, 107, 0, 0.6)",
    });
  }

  // Primary Suspects (4 suspects)
  const suspectNodes: CaseNode[] = [];
  const suspectNames = ["Rajesh Kumar", "Vikram Singh", "Amit Sharma", "Deepak Patel"];
  suspectNames.forEach((name, idx) => {
    const suspectNode: CaseNode = {
      id: `suspect-${idx + 1}`,
      name: name,
      type: "suspect",
      caseId: "CASE-2024-042",
      color: CASE_ENTITY_COLORS.suspect,
      size: 10,
    };
    suspectNodes.push(suspectNode);
    nodes.push(suspectNode);
    
    // Connect suspect to case
    links.push({
      source: caseNode.id,
      target: suspectNode.id,
      relation: "investigates",
      color: "rgba(255, 0, 85, 0.6)",
    });

    // Connect suspect to FIRs
    firNodes.forEach((fir) => {
      if (Math.random() > 0.3) {
        links.push({
          source: suspectNode.id,
          target: fir.id,
          relation: "mentioned_in",
          color: "rgba(255, 0, 85, 0.4)",
        });
      }
    });
  });

  // Criminal Records for suspects
  suspectNodes.forEach((suspect, idx) => {
    const recordNode: CaseNode = {
      id: `record-${idx + 1}`,
      name: `Criminal Record: ${suspect.name}`,
      type: "criminal_record",
      caseId: "CASE-2024-042",
      color: CASE_ENTITY_COLORS.criminal_record,
      size: 8,
    };
    nodes.push(recordNode);
    links.push({
      source: suspect.id,
      target: recordNode.id,
      relation: "has_record",
      color: "rgba(255, 23, 68, 0.6)",
    });
  });

  // Investigating Officers (5 officers)
  const officerNodes: CaseNode[] = [];
  const officerNames = ["Insp. Ramesh Kumar", "SI Priya Sharma", "Const. Ajay Verma", "Insp. Meera Singh", "ASI Rajesh Patel"];
  officerNames.forEach((name, idx) => {
    const officerNode: CaseNode = {
      id: `officer-${idx + 1}`,
      name: name,
      type: "officer",
      caseId: "CASE-2024-042",
      color: CASE_ENTITY_COLORS.officer,
      size: 9,
    };
    officerNodes.push(officerNode);
    nodes.push(officerNode);
    
    // Connect officer to case
    links.push({
      source: caseNode.id,
      target: officerNode.id,
      relation: "assigned_to",
      color: "rgba(59, 130, 246, 0.6)",
    });

    // Connect officers to suspects they're investigating
    suspectNodes.forEach((suspect) => {
      if (Math.random() > 0.5) {
        links.push({
          source: officerNode.id,
          target: suspect.id,
          relation: "investigates",
          color: "rgba(59, 130, 246, 0.4)",
        });
      }
    });
  });

  // Crime Locations (4 locations)
  const locationNodes: CaseNode[] = [];
  const locations = ["Warehouse Complex, Sector 12", "Residential Area, Block C", "Highway Checkpoint KM-45", "Abandoned Factory, Industrial Zone"];
  locations.forEach((loc, idx) => {
    const locationNode: CaseNode = {
      id: `location-${idx + 1}`,
      name: loc,
      type: "location",
      caseId: "CASE-2024-042",
      color: CASE_ENTITY_COLORS.location,
      size: 8,
    };
    locationNodes.push(locationNode);
    nodes.push(locationNode);
    
    // Connect location to case
    links.push({
      source: caseNode.id,
      target: locationNode.id,
      relation: "occurred_at",
      color: "rgba(0, 255, 136, 0.6)",
    });

    // Connect suspects to locations
    suspectNodes.forEach((suspect) => {
      if (Math.random() > 0.6) {
        links.push({
          source: suspect.id,
          target: locationNode.id,
          relation: "seen_at",
          color: "rgba(0, 255, 136, 0.4)",
        });
      }
    });
  });

  // Evidence Items (8 evidence pieces)
  const evidenceNodes: CaseNode[] = [];
  const evidenceTypes = ["Digital Evidence: Phone Records", "Fingerprint Evidence", "DNA Sample", "CCTV Footage", "Financial Transaction Records", "Weapon: Firearm", "Vehicle Registration", "Digital Evidence: Email Trail"];
  evidenceTypes.forEach((evidence, idx) => {
    const evidenceNode: CaseNode = {
      id: `evidence-${idx + 1}`,
      name: evidence,
      type: "evidence",
      caseId: "CASE-2024-042",
      color: CASE_ENTITY_COLORS.evidence,
      size: 7,
    };
    evidenceNodes.push(evidenceNode);
    nodes.push(evidenceNode);
    
    // Connect evidence to case
    links.push({
      source: caseNode.id,
      target: evidenceNode.id,
      relation: "contains",
      color: "rgba(188, 0, 255, 0.6)",
    });

    // Connect evidence to suspects
    suspectNodes.forEach((suspect) => {
      if (Math.random() > 0.7) {
        links.push({
          source: evidenceNode.id,
          target: suspect.id,
          relation: "links_to",
          color: "rgba(188, 0, 255, 0.4)",
        });
      }
    });
  });

  // Case Files/Documents (6 documents)
  const documentNodes: CaseNode[] = [];
  const documents = ["Case File: Initial Report", "Forensic Analysis Report", "Witness Statements", "Court Documents", "Medical Examiner Report", "Ballistics Report"];
  documents.forEach((doc, idx) => {
    const docNode: CaseNode = {
      id: `doc-${idx + 1}`,
      name: doc,
      type: "document",
      caseId: "CASE-2024-042",
      color: CASE_ENTITY_COLORS.document,
      size: 6,
    };
    documentNodes.push(docNode);
    nodes.push(docNode);
    
    // Connect document to case
    links.push({
      source: caseNode.id,
      target: docNode.id,
      relation: "references",
      color: "rgba(107, 114, 128, 0.6)",
    });

    // Connect documents to FIRs
    firNodes.forEach((fir) => {
      if (Math.random() > 0.6) {
        links.push({
          source: docNode.id,
          target: fir.id,
          relation: "attached_to",
          color: "rgba(107, 114, 128, 0.4)",
        });
      }
    });
  });

  // Witnesses (3 witnesses)
  const witnessNodes: CaseNode[] = [];
  const witnesses = ["Witness: Shop Owner", "Witness: Security Guard", "Witness: Neighbor"];
  witnesses.forEach((witness, idx) => {
    const witnessNode: CaseNode = {
      id: `witness-${idx + 1}`,
      name: witness,
      type: "witness",
      caseId: "CASE-2024-042",
      color: CASE_ENTITY_COLORS.witness,
      size: 8,
    };
    witnessNodes.push(witnessNode);
    nodes.push(witnessNode);
    
    // Connect witness to case
    links.push({
      source: caseNode.id,
      target: witnessNode.id,
      relation: "testified_in",
      color: "rgba(255, 193, 7, 0.6)",
    });

    // Connect witnesses to locations
    locationNodes.forEach((location) => {
      if (Math.random() > 0.7) {
        links.push({
          source: witnessNode.id,
          target: location.id,
          relation: "present_at",
          color: "rgba(255, 193, 7, 0.4)",
        });
      }
    });
  });

  // Vehicles (2 vehicles)
  const vehicleNodes: CaseNode[] = [];
  const vehicles = ["Vehicle: MH-12-AB-1234", "Vehicle: DL-08-CD-5678"];
  vehicles.forEach((vehicle, idx) => {
    const vehicleNode: CaseNode = {
      id: `vehicle-${idx + 1}`,
      name: vehicle,
      type: "vehicle",
      caseId: "CASE-2024-042",
      color: CASE_ENTITY_COLORS.vehicle,
      size: 7,
    };
    vehicleNodes.push(vehicleNode);
    nodes.push(vehicleNode);
    
    // Connect vehicle to suspects
    suspectNodes.forEach((suspect) => {
      if (Math.random() > 0.5) {
        links.push({
          source: suspect.id,
          target: vehicleNode.id,
          relation: "owns",
          color: "rgba(156, 39, 176, 0.6)",
        });
      }
    });

    // Connect vehicle to locations
    locationNodes.forEach((location) => {
      if (Math.random() > 0.6) {
        links.push({
          source: vehicleNode.id,
          target: location.id,
          relation: "spotted_at",
          color: "rgba(156, 39, 176, 0.4)",
        });
      }
    });
  });

  // Weapons (2 weapons)
  const weaponNodes: CaseNode[] = [];
  const weapons = ["Weapon: Pistol (Serial: XYZ-123)", "Weapon: Knife (Forensic ID: KF-456)"];
  weapons.forEach((weapon, idx) => {
    const weaponNode: CaseNode = {
      id: `weapon-${idx + 1}`,
      name: weapon,
      type: "weapon",
      caseId: "CASE-2024-042",
      color: CASE_ENTITY_COLORS.weapon,
      size: 7,
    };
    weaponNodes.push(weaponNode);
    nodes.push(weaponNode);
    
    // Connect weapon to evidence
    evidenceNodes.forEach((evidence) => {
      if (evidence.name.includes("Weapon")) {
        links.push({
          source: weaponNode.id,
          target: evidence.id,
          relation: "documented_as",
          color: "rgba(244, 67, 54, 0.6)",
        });
      }
    });

    // Connect weapon to suspects
    suspectNodes.forEach((suspect) => {
      if (Math.random() > 0.6) {
        links.push({
          source: suspect.id,
          target: weaponNode.id,
          relation: "possessed",
          color: "rgba(244, 67, 54, 0.4)",
        });
      }
    });
  });

  // ========== CROSS-CASE INTELLIGENCE CONNECTIONS ==========
  // Add entities from other cases to demonstrate cross-case connections
  const otherCases = [
    { id: "CASE-2024-001", name: "CASE-2024-001: Drug Trafficking Ring" },
    { id: "CASE-2024-015", name: "CASE-2024-015: Money Laundering Operation" },
    { id: "CASE-2023-089", name: "CASE-2023-089: Organized Theft Network" },
  ];

  // Create other case center nodes (smaller, different style)
  const otherCaseNodes: CaseNode[] = [];
  otherCases.forEach((otherCase, idx) => {
    const otherCaseNode: CaseNode = {
      id: `other-case-${idx + 1}`,
      name: otherCase.name,
      type: "case",
      caseId: otherCase.id,
      color: "#00D4FF", // Lighter cyan for other cases
      size: 15,
    };
    otherCaseNodes.push(otherCaseNode);
    nodes.push(otherCaseNode);
  });

  // Add suspects from other cases that are connected to current case
  const crossCaseSuspects: CaseNode[] = [];
  const crossCaseSuspectNames = [
    { name: "Mohan Das (CASE-2024-001)", caseId: "CASE-2024-001" },
    { name: "Suresh Reddy (CASE-2024-015)", caseId: "CASE-2024-015" },
    { name: "Kiran Mehta (CASE-2023-089)", caseId: "CASE-2023-089" },
  ];

  crossCaseSuspectNames.forEach((suspectInfo, idx) => {
    const crossSuspect: CaseNode = {
      id: `cross-suspect-${idx + 1}`,
      name: suspectInfo.name,
      type: "suspect",
      caseId: suspectInfo.caseId,
      color: "#FF3366", // Slightly different red for cross-case suspects
      size: 9,
    };
    crossCaseSuspects.push(crossSuspect);
    nodes.push(crossSuspect);

    // Connect cross-case suspect to their case
    const otherCaseNode = otherCaseNodes.find(n => n.caseId === suspectInfo.caseId);
    if (otherCaseNode) {
      links.push({
        source: otherCaseNode.id,
        target: crossSuspect.id,
        relation: "investigates",
        color: "rgba(255, 51, 102, 0.5)",
      });
    }
  });

  // Add locations from other cases
  const crossCaseLocations: CaseNode[] = [];
  const crossCaseLocationData = [
    { name: "Warehouse Complex, Sector 8 (CASE-2024-001)", caseId: "CASE-2024-001" },
    { name: "Bank Branch, Downtown (CASE-2024-015)", caseId: "CASE-2024-015" },
    { name: "Storage Facility, Industrial Zone (CASE-2023-089)", caseId: "CASE-2023-089" },
  ];

  crossCaseLocationData.forEach((locInfo, idx) => {
    const crossLocation: CaseNode = {
      id: `cross-location-${idx + 1}`,
      name: locInfo.name,
      type: "location",
      caseId: locInfo.caseId,
      color: "#33FF99", // Slightly different green
      size: 7,
    };
    crossCaseLocations.push(crossLocation);
    nodes.push(crossLocation);

    // Connect to their case
    const otherCaseNode = otherCaseNodes.find(n => n.caseId === locInfo.caseId);
    if (otherCaseNode) {
      links.push({
        source: otherCaseNode.id,
        target: crossLocation.id,
        relation: "occurred_at",
        color: "rgba(51, 255, 153, 0.5)",
      });
    }
  });

  // Add vehicles from other cases
  const crossCaseVehicles: CaseNode[] = [];
  const crossCaseVehicleData = [
    { name: "Vehicle: UP-14-EF-9012 (CASE-2024-001)", caseId: "CASE-2024-001" },
    { name: "Vehicle: HR-26-GH-3456 (CASE-2024-015)", caseId: "CASE-2024-015" },
  ];

  crossCaseVehicleData.forEach((vehicleInfo, idx) => {
    const crossVehicle: CaseNode = {
      id: `cross-vehicle-${idx + 1}`,
      name: vehicleInfo.name,
      type: "vehicle",
      caseId: vehicleInfo.caseId,
      color: "#B84DFF", // Slightly different purple
      size: 6,
    };
    crossCaseVehicles.push(crossVehicle);
    nodes.push(crossVehicle);
  });

  // ========== CROSS-CASE CONNECTIONS (The Intelligence Links) ==========
  // These connections demonstrate how KG helps find connections across cases

  // Connection 1: Suspect from current case connected to suspect from another case (criminal network)
  // Rajesh Kumar (current case) is connected to Mohan Das (CASE-2024-001) - same criminal network
  if (suspectNodes[0] && crossCaseSuspects[0]) {
    links.push({
      source: suspectNodes[0].id,
      target: crossCaseSuspects[0].id,
      relation: "criminal_associate",
      color: "rgba(255, 255, 0, 0.8)", // Bright yellow for cross-case links
      isCrossCase: true,
    });
  }

  // Connection 2: Location connection - same location used in multiple cases
  // Warehouse Complex, Sector 12 (current case) connected to Warehouse Complex, Sector 8 (other case)
  if (locationNodes[0] && crossCaseLocations[0]) {
    links.push({
      source: locationNodes[0].id,
      target: crossCaseLocations[0].id,
      relation: "same_location_type",
      color: "rgba(255, 255, 0, 0.8)",
      isCrossCase: true,
    });
  }

  // Connection 3: Vehicle connection - same vehicle used across cases
  // Vehicle from current case connected to vehicle from another case (stolen vehicle ring)
  if (vehicleNodes[0] && crossCaseVehicles[0]) {
    links.push({
      source: vehicleNodes[0].id,
      target: crossCaseVehicles[0].id,
      relation: "stolen_vehicle_ring",
      color: "rgba(255, 255, 0, 0.8)",
      isCrossCase: true,
    });
  }

  // Connection 4: Suspect from current case connected to location from another case
  // Vikram Singh (current case) was seen at Bank Branch from CASE-2024-015
  if (suspectNodes[1] && crossCaseLocations[1]) {
    links.push({
      source: suspectNodes[1].id,
      target: crossCaseLocations[1].id,
      relation: "seen_at_cross_case",
      color: "rgba(255, 255, 0, 0.8)",
      isCrossCase: true,
    });
  }

  // Connection 5: Evidence connection - same evidence type across cases
  // Digital Evidence from current case connected to financial records from another case
  const digitalEvidence = evidenceNodes.find(e => e.name.includes("Digital Evidence"));
  if (digitalEvidence && crossCaseSuspects[1]) {
    links.push({
      source: digitalEvidence.id,
      target: crossCaseSuspects[1].id,
      relation: "financial_connection",
      color: "rgba(255, 255, 0, 0.8)",
      isCrossCase: true,
    });
  }

  // Connection 6: Criminal record connection - same person in multiple cases
  // Criminal record from current case connected to suspect from another case
  if (nodes.find(n => n.type === "criminal_record" && n.id === "record-1") && crossCaseSuspects[2]) {
    links.push({
      source: "record-1",
      target: crossCaseSuspects[2].id,
      relation: "same_person_different_case",
      color: "rgba(255, 255, 0, 0.8)",
      isCrossCase: true,
    });
  }

  // Connection 7: Officer connection - same officer worked on multiple cases
  // Inspector Ramesh Kumar worked on both current case and CASE-2024-001
  if (officerNodes[0] && otherCaseNodes[0]) {
    links.push({
      source: officerNodes[0].id,
      target: otherCaseNodes[0].id,
      relation: "investigated_by",
      color: "rgba(255, 255, 0, 0.8)",
      isCrossCase: true,
    });
  }

  // Connection 8: Direct case-to-case connection showing related investigations
  // Current case connected to other cases showing they're part of larger investigation
  otherCaseNodes.forEach((otherCase) => {
    links.push({
      source: caseNode.id,
      target: otherCase.id,
      relation: "related_investigation",
      color: "rgba(255, 255, 0, 0.9)", // Bright yellow, thicker
      isCrossCase: true,
    });
  });

  return { nodes, links };
}

interface CaseDetailKGProps {
  isFullscreen?: boolean;
  onFullscreenClick?: () => void;
}

export function CaseDetailKG({ isFullscreen = false, onFullscreenClick }: CaseDetailKGProps) {
  const graphRef = useRef<any>();
  const [hoveredNode, setHoveredNode] = useState<CaseNode | null>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  // Generate case detail data once using useMemo
  const graphData = useMemo(() => generateCaseDetailData(), []);

  useEffect(() => {
    // Auto-fit the graph after a short delay
    if (graphRef.current) {
      const timer = setTimeout(() => {
        graphRef.current.cameraPosition({ x: 0, y: 0, z: 200 });
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  // Track mouse position for tooltip
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    if (typeof window !== "undefined") {
      window.addEventListener("mousemove", handleMouseMove);
      return () => window.removeEventListener("mousemove", handleMouseMove);
    }
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
      graphRef.current.cameraPosition({ x: 0, y: 0, z: 200 });
    }
  };

  return (
    <div className="w-full h-full relative bg-black rounded-lg border border-cyan-500/20 overflow-hidden">
      {/* Header Overlay */}
      <div className="absolute top-4 left-4 right-4 z-10 pointer-events-none">
        <div className="bg-slate-900/90 backdrop-blur-md border border-cyan-500/30 rounded-lg px-4 py-2 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-display uppercase tracking-wider text-cyan-400">
              CASE DETAIL VIEW: CASE-2024-042
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              {graphData.nodes.length} entities • {graphData.links.length} connections • 
              {graphData.links.filter(l => l.isCrossCase).length} cross-case intelligence links • 
              Demonstrating how KG connects entities across different cases
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

      {/* Cross-Case Intelligence Info Panel */}
      <div className="absolute top-20 right-4 z-10 pointer-events-none max-w-sm">
        <div className="bg-slate-900/90 backdrop-blur-md border border-yellow-500/40 rounded-lg px-4 py-3">
          <div className="text-xs font-semibold text-yellow-400 mb-2 uppercase tracking-wider flex items-center gap-2">
            <span>🔗</span>
            <span>Cross-Case Intelligence</span>
          </div>
          <div className="text-xs text-slate-300 space-y-2">
            <p>
              The Knowledge Graph reveals <span className="text-yellow-400 font-semibold">{graphData.links.filter(l => l.isCrossCase).length} connections</span> between this case and <span className="text-yellow-400 font-semibold">{new Set(graphData.nodes.filter(n => n.caseId && n.caseId !== "CASE-2024-042").map(n => n.caseId)).size} other cases</span>.
            </p>
            <p className="text-slate-400 text-[10px] mt-2">
              Yellow links indicate cross-case connections, helping investigators discover hidden relationships across investigations.
            </p>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 pointer-events-none">
        <div className="bg-slate-900/90 backdrop-blur-md border border-cyan-500/30 rounded-lg px-4 py-3 max-h-96 overflow-y-auto">
          <div className="text-xs font-semibold text-cyan-400 mb-2 uppercase tracking-wider">
            Entity Types
          </div>
          <div className="space-y-1.5 text-xs mb-3">
            {Object.entries(CASE_ENTITY_COLORS).map(([type, color]) => (
              <div key={type} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: color }}
                />
                <span className="text-slate-300 capitalize">{type.replace(/_/g, " ")}</span>
              </div>
            ))}
          </div>
          <div className="border-t border-cyan-500/20 pt-2 mt-2">
            <div className="text-xs font-semibold text-yellow-400 mb-2 uppercase tracking-wider">
              Connection Types
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-6 h-0.5 bg-yellow-400" />
                <span className="text-slate-300">Cross-Case Intelligence Link</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-0.5 bg-slate-500" />
                <span className="text-slate-300">Within-Case Connection</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3D Graph */}
      <ForceGraph3D
        ref={graphRef}
        graphData={graphData}
        nodeLabel={(node: any) => {
          const caseNode = node as CaseNode;
          return `${caseNode.caseId || "Unknown"}: ${caseNode.name} (${caseNode.type})`;
        }}
        nodeColor={(node: any) => (node as CaseNode).color}
        nodeVal={(node: any) => (node as CaseNode).size}
        linkLabel={(link: any) => {
          const linkData = link as CaseLink;
          return linkData.isCrossCase 
            ? `🔗 CROSS-CASE: ${linkData.relation}` 
            : linkData.relation;
        }}
        linkColor={(link: any) => (link as CaseLink).color}
        linkWidth={(link: any) => (link as CaseLink).isCrossCase ? 4.5 : 3}
        linkOpacity={(link: any) => (link as CaseLink).isCrossCase ? 0.9 : 0.7}
        linkDirectionalArrowLength={(link: any) => (link as CaseLink).isCrossCase ? 8 : 6}
        linkDirectionalArrowRelPos={1}
        onNodeHover={handleNodeHover}
        onBackgroundClick={handleBackgroundClick}
        backgroundColor="#000000"
        showNavInfo={false}
        nodeOpacity={0.9}
        nodeResolution={16}
      />

      {/* Hover Tooltip */}
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
            Type: {hoveredNode.type.replace(/_/g, " ")}
          </div>
          {hoveredNode.caseId && hoveredNode.caseId !== "CASE-2024-042" && (
            <div className="text-xs text-yellow-400 mt-1 font-semibold">
              🔗 Cross-Case Entity
            </div>
          )}
        </div>
      )}
    </div>
  );
}

