"use client";

export function ClassificationBanner() {
  return (
    <div className="flex items-center gap-2 px-4 py-1.5 bg-crimson-500/20 border-2 border-crimson-500/60 rounded tech-border relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-r from-crimson-500/10 via-transparent to-crimson-500/10 animate-pulse-slow"></div>
      <div className="w-2 h-2 rounded-full bg-crimson-500 animate-pulse-slow mr-1"></div>
      <span className="text-xs font-display uppercase tracking-widest text-crimson-500 font-bold relative z-10">
        TOP SECRET // NOFORN
      </span>
    </div>
  );
}

