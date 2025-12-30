"use client";

export default function IngestVelocity() {
  return (
    <div className="h-full bg-glass-light backdrop-blur-md border border-glass-border rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6 h-14">
        <h2 className="text-sm font-bold tracking-wider text-gray-400 flex items-center">
          INGEST VELOCITY
        </h2>
        <button className="text-gray-500 hover:text-white transition-colors flex items-center h-6">
          •••
        </button>
      </div>

      <div className="relative h-64 pl-8">
        {/* Chart Axes */}
        <div className="absolute bottom-0 left-8 right-0 h-px bg-glass-border" />
        <div className="absolute bottom-0 left-8 top-0 w-px bg-glass-border" />

        {/* Y-axis labels - aligned with grid lines */}
        <div className="absolute left-0 top-0 text-xs font-mono text-gray-500 flex flex-col h-full justify-between">
          <div className="flex items-center h-0">1,000</div>
          <div className="flex items-center h-0">800</div>
          <div className="flex items-center h-0">600</div>
          <div className="flex items-center h-0">400</div>
          <div className="flex items-center h-0">200</div>
          <div className="flex items-center h-0">0</div>
        </div>

        {/* Grid lines for alignment */}
        <div className="absolute inset-0 left-8 flex flex-col justify-between">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-px bg-glass-border/30" />
          ))}
        </div>

        {/* Area Chart */}
        <svg viewBox="0 0 300 200" className="absolute inset-0 w-full h-full left-8">
          <defs>
            <linearGradient id="velocityGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#00F2FF" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#00F2FF" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path
            d="M0,180 L20,160 L40,170 L60,140 L80,150 L100,120 L120,100 L140,90 L160,70 L180,60 L200,50 L220,40 L240,50 L260,40 L280,30 L300,30 L300,200 L0,200 Z"
            fill="url(#velocityGradient)"
          />
          <path
            d="M0,180 L20,160 L40,170 L60,140 L80,150 L100,120 L120,100 L140,90 L160,70 L180,60 L200,50 L220,40 L240,50 L260,40 L280,30 L300,30"
            fill="none"
            stroke="#00F2FF"
            strokeWidth="2"
          />
        </svg>

        {/* X-axis labels */}
        <div className="absolute bottom-0 left-8 right-0 -mb-6 flex justify-between text-xs font-mono text-gray-500">
          <span className="ml-0">00:00</span>
          <span>08:00</span>
          <span>Last Hour</span>
        </div>
      </div>
    </div>
  );
}

