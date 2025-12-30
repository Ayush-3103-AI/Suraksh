"use client";

import { useEffect } from "react";
import { AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";

const threats = [
  {
    time: "10:42 AM",
    source: "BORDER_CAM_04",
    text: "Vehicle detected in restricted zone",
    level: "critical",
  },
  {
    time: "10:45 AM",
    source: "FIN-INTEL",
    text: "Large crypto transaction flagged",
    level: "high",
  },
  {
    time: "10:48 AM",
    source: "SIGINT",
    text: "Unusual communication pattern detected",
    level: "medium",
  },
];

export default function ThreatTicker() {
  return (
    <div className="h-12 bg-space-200 border-b border-threat-critical/30 flex items-center px-8 overflow-hidden relative">
      <div className="flex items-center gap-3 mr-6 flex-shrink-0 z-10">
        <AlertTriangle className="w-4 h-4 text-threat-critical animate-pulse" />
        <span className="text-xs font-bold text-threat-critical tracking-wider">
          THREAT TICKER
        </span>
      </div>

      <div className="flex-1 overflow-hidden relative">
        <motion.div
          className="flex gap-8 text-sm items-center h-full"
          animate={{ x: ["0%", "-50%"] }}
          transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
        >
          {[...threats, ...threats].map((threat, idx) => (
            <div
              key={idx}
              className="flex items-center gap-4 whitespace-nowrap h-full"
            >
              <span className="text-xs font-mono text-gray-500 flex items-center h-full">
                [{threat.time}]
              </span>
              <span className="text-xs font-mono text-cyber-cyan flex items-center h-full">
                {threat.source}
              </span>
              <span className="text-sm text-gray-300 flex items-center h-full">{threat.text}</span>
              <span
                className={`text-xs px-2.5 py-1 rounded border flex items-center h-full ${
                  threat.level === "critical"
                    ? "bg-threat-critical/20 text-threat-critical border-threat-critical/30"
                    : threat.level === "high"
                    ? "bg-threat-high/20 text-threat-high border-threat-high/30"
                    : "bg-threat-medium/20 text-threat-medium border-threat-medium/30"
                }`}
              >
                {threat.level.toUpperCase()}
              </span>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  );
}

