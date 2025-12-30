"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { Bell, Wifi, Lock, Clock, Search } from "lucide-react";
import { useAuthStore } from "@/store/auth-store";

export function TopBar() {
  const { user } = useAuthStore();
  const [currentTime, setCurrentTime] = useState<string>("");

  // Update UTC time
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const hours = String(now.getUTCHours()).padStart(2, '0');
      const minutes = String(now.getUTCMinutes()).padStart(2, '0');
      setCurrentTime(`${hours}:${minutes} UTC`);
    };
    updateTime();
    const interval = setInterval(updateTime, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-glass-border bg-glass-light backdrop-blur-md flex items-center justify-between px-8">
      {/* Left: Classification Banner Only (Branding removed - kept only on sidebar) */}
      <div className="flex items-center gap-4 h-full">
        <div className="px-3 py-1 bg-yellow-500/20 border border-yellow-500/50 rounded text-yellow-400 text-xs font-bold tracking-wider flex items-center h-full">
          CLASSIFIED // INTERNAL
        </div>
      </div>

      {/* Center: Search Bar */}
      <div className="flex-1 max-w-2xl mx-8 flex items-center h-full">
        <div className="relative w-full">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-gray-500" />
          </div>
          <input
            type="text"
            placeholder="Search entities..."
            className="w-full bg-glass-medium border border-glass-border rounded-lg pl-10 pr-20 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyber-cyan/50 focus:ring-1 focus:ring-cyber-cyan/50 transition-all leading-tight flex items-center"
            style={{ lineHeight: '1.5' }}
          />
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <kbd className="px-2 py-1 text-xs font-semibold text-gray-400 bg-glass-light border border-glass-border rounded">⌘K</kbd>
          </div>
        </div>
      </div>

      {/* Right: System Status and Notifications */}
      <div className="flex items-center gap-6 h-full">
        {/* System Status Indicators - Aligned horizontally with search bar */}
        <div className="flex items-center gap-3 h-full">
          <div className="flex items-center gap-1.5 h-full">
            <span className="text-xs font-mono text-gray-400 px-2 py-1 bg-glass-medium border border-glass-border rounded">NFT</span>
          </div>
          <div className="flex items-center gap-1.5 h-full">
            <span className="text-xs font-mono text-gray-400 px-2 py-1 bg-glass-medium border border-glass-border rounded">CRYPTO</span>
          </div>
          <div className="flex items-center gap-1.5 h-full">
            <span className="text-xs font-mono text-gray-400 px-2 py-1 bg-glass-medium border border-glass-border rounded">DB</span>
          </div>
        </div>

        {/* User Profile Card */}
        <div className="flex items-center h-full">
          <div className="px-4 py-2.5 bg-gradient-to-r from-cyber-purple/20 to-space-200 border border-cyber-purple/30 rounded-full flex items-center gap-2.5 h-auto">
            <div className="w-6 h-6 rounded-full bg-cyber-cyan/20 border border-cyber-cyan/50 flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold text-cyber-cyan">VS</span>
            </div>
            <span className="text-sm font-medium text-white whitespace-nowrap">Major V. Singh</span>
          </div>
        </div>

        {/* Notification Bell */}
        <div className="relative flex items-center h-full">
          <Bell className="w-5 h-5 text-gray-400 hover:text-white cursor-pointer transition-colors" />
          <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full border-2 border-space"></div>
        </div>
      </div>
    </header>
  );
}
