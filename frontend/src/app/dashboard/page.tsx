"use client";

import { useEffect } from "react";
import ThreatTicker from "@/components/ThreatTicker";
import GeospatialIntel from "@/components/GeospatialIntel";
import AICommand from "@/components/AICommand";
import LiveInvestigations from "@/components/LiveInvestigations";
import IntelligenceFeed from "@/components/IntelligenceFeed";

export default function Dashboard() {
  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="p-8 pb-4">
        <h1 className="text-4xl font-display uppercase tracking-wider text-white mb-2">
          INTEL-CORE
        </h1>
        <p className="text-slate-500 text-lg">
          Real-time intelligence dashboard and operational awareness
        </p>
      </div>
      <ThreatTicker />

      <div className="flex-1 overflow-y-auto p-8 space-y-8">
        <div className="grid grid-cols-12 gap-6 mt-6">
          {/* Left Column - Geospatial Intel */}
          <div className="col-span-12 lg:col-span-5">
            <GeospatialIntel />
          </div>

          {/* Middle Column - AI Command */}
          <div className="col-span-12 lg:col-span-4">
            <AICommand />
          </div>

          {/* Right Column - Live Investigations */}
          <div className="col-span-12 lg:col-span-3">
            <LiveInvestigations />
          </div>
        </div>

        {/* Bottom Row - Intelligence Feed */}
        <IntelligenceFeed />
      </div>
    </div>
  );
}
