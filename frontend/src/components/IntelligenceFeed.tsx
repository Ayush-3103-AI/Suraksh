"use client";

import { FileText, Lock, TrendingUp } from "lucide-react";

const feedItems = [
  {
    type: "document",
    title: "Kashmir Cell Chatter Report",
    source: "RAW",
    confidence: 84,
    icon: FileText,
  },
  {
    type: "classified",
    title: "[REDACTED] *** 🔒",
    source: "IB",
    confidence: 68,
    icon: Lock,
  },
  {
    type: "trending",
    title: "Border Activity Spike Analysis",
    source: "BORDER_INTEL",
    confidence: 92,
    icon: TrendingUp,
  },
  {
    type: "document",
    title: "Financial Transaction Pattern Report",
    source: "FIN-INTEL",
    confidence: 76,
    icon: FileText,
  },
];

export default function IntelligenceFeed() {
  return (
    <div className="bg-glass-light backdrop-blur-md border border-glass-border rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-sm font-bold tracking-wider text-gray-400">
          RECENT INTELLIGENCE FEED
        </h2>
        <button className="text-gray-500 hover:text-white transition-colors">
          •••
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-glass-border">
              <th className="text-left text-xs font-mono text-gray-500 pb-3 pr-4">
                TYPE
              </th>
              <th className="text-left text-xs font-mono text-gray-500 pb-3 pr-4">
                TITLE
              </th>
              <th className="text-left text-xs font-mono text-gray-500 pb-3 pr-4">
                SOURCE AGENCY
              </th>
              <th className="text-left text-xs font-mono text-gray-500 pb-3">
                CONFIDENCE SCORE
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-glass-border">
            {feedItems.map((item, idx) => (
              <tr
                key={idx}
                className="hover:bg-glass-medium transition-colors group cursor-pointer"
              >
                <td className="py-4 pr-4">
                  <div className="w-8 h-8 rounded-lg bg-space-200 flex items-center justify-center group-hover:bg-cyber-cyan/10 transition-colors">
                    <item.icon className="w-4 h-4 text-gray-400 group-hover:text-cyber-cyan transition-colors" />
                  </div>
                </td>
                <td className="py-4 pr-4 font-medium text-white">{item.title}</td>
                <td className="py-4 pr-4">
                  <span className="px-2 py-1 rounded bg-glass-medium text-xs font-mono border border-glass-border text-gray-300">
                    {item.source}
                  </span>
                </td>
                <td className="py-4">
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 bg-space-200 rounded-full overflow-hidden max-w-xs">
                      <div
                        className={`h-full rounded-full ${
                          item.confidence >= 80
                            ? "bg-cyber-green"
                            : "bg-cyber-cyan"
                        }`}
                        style={{ width: `${item.confidence}%` }}
                      />
                    </div>
                    <span className="text-sm font-mono text-gray-400">
                      {item.confidence}%
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

