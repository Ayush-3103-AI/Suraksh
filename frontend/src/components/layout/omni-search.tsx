"use client";

import { useState } from "react";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";

export function OmniSearch() {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <div
      className={cn(
        "relative flex items-center transition-all duration-300",
        isFocused && "scale-[1.02]"
      )}
    >
      <div
        className={cn(
          "absolute inset-0 rounded-lg border-2 transition-all duration-300",
          isFocused
            ? "border-cyan-500 shadow-cyan-glow"
            : "border-cyan-500/30"
        )}
      />
      <div className="relative flex items-center w-full">
        <Search className="absolute left-3 w-5 h-5 text-cyan-400/50" />
        <input
          type="text"
          placeholder="Search intelligence data..."
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          className={cn(
            "w-full pl-10 pr-4 py-2 bg-void-800/50 backdrop-blur-sm",
            "text-cyan-400 placeholder:text-slate-500",
            "focus:outline-none focus:ring-0",
            "font-mono text-sm"
          )}
        />
      </div>
    </div>
  );
}

