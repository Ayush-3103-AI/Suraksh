"use client";

import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface HoloCardProps {
  children: ReactNode;
  title?: string;
  className?: string;
  hover?: boolean;
}

export function HoloCard({
  children,
  title,
  className,
  hover = true,
}: HoloCardProps) {
  return (
    <div
      className={cn(
        "glass tech-border rounded-lg p-6 transition-all duration-300 relative overflow-hidden",
        hover && "hover:shadow-cyan-glow hover:border-cyan-500/50",
        className
      )}
    >
      {/* Subtle corner accent */}
      <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-br from-cyan-500/5 to-transparent pointer-events-none"></div>
      
      {title && (
        <div className="mb-4 pb-3 border-b border-cyan-500/30 relative">
          <h3 className="text-lg font-display uppercase tracking-wider text-cyan-400 font-semibold">
            {title}
          </h3>
          <div className="absolute bottom-0 left-0 h-0.5 w-12 bg-gradient-to-r from-cyan-500 to-transparent"></div>
        </div>
      )}
      {children}
    </div>
  );
}

