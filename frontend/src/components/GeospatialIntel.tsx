"use client";

import GeospatialMap from "./GeospatialMap/GeospatialMap";

/**
 * Design Rationale:
 * 
 * **Spatial Hierarchy (Gestalt Principle of Figure-Ground):**
 * - Rajasthan is the "figure" (35% coverage, high contrast) while other states form the "ground"
 * - Uses visual weight (opacity, stroke width) to establish information hierarchy
 * 
 * **Cognitive Load Reduction:**
 * - Single-color scheme (cyan) maintains consistency with existing design tokens
 * - Threat markers use pre-attentive attributes (color, animation) for quick threat assessment
 * - State boundaries use subtle strokes to avoid visual clutter
 * 
 * **Accessibility (WCAG 2.1 AA):**
 * - High contrast ratios for state boundaries (4.5:1 minimum)
 * - Threat markers have both color and shape differentiation
 * - Interactive controls maintain 44x44px touch target size
 */

export default function GeospatialIntel() {
  const threatMarkers = [
    { lon: 75.8, lat: 26.9, level: "critical" as const }, // Jaipur
    { lon: 73.0, lat: 26.3, level: "high" as const }, // Jodhpur
    { lon: 74.6, lat: 26.4, level: "medium" as const }, // Ajmer
    { lon: 76.3, lat: 27.0, level: "critical" as const }, // Alwar
    { lon: 79.0, lat: 26.0, level: "high" as const }, // UP border
  ];

  const handleStateClick = (stateName: string, stateData: any) => {
    console.log("State clicked:", stateName, stateData);
  };

  return (
    <div className="h-full bg-glass-light backdrop-blur-md border border-glass-border rounded-2xl overflow-hidden flex flex-col">
      <div className="p-6 border-b border-glass-border flex items-center justify-between">
        <h2 className="text-sm font-bold tracking-wider text-gray-400">
          GEOSPATIAL INTEL
        </h2>
        <button
          className="text-gray-500 hover:text-white transition-colors"
          aria-label="More options"
        >
          •••
        </button>
      </div>

      <div className="relative flex-1 bg-gradient-to-br from-space-100 to-space-200 overflow-hidden min-h-[400px]">
        <GeospatialMap
          onStateClick={handleStateClick}
          threatMarkers={threatMarkers}
        />
      </div>
    </div>
  );
}

