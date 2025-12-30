"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import Image from "next/image";
import { useAuthStore } from "@/store/auth-store";
import {
  LayoutDashboard,
  MessageSquareText,
  Network,
  FolderLock,
  Settings,
  Shield,
  ChevronLeft,
  ChevronRight,
  Bell,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { icon: LayoutDashboard, label: "Intel-Core", href: "/dashboard" },
  { icon: MessageSquareText, label: "Deep Search", href: "/dashboard/search" },
  { icon: Network, label: "Knowledge Graph", href: "/dashboard/graph" },
  { icon: FolderLock, label: "File Vault", href: "/dashboard/vault" },
  { icon: Bell, label: "Requests & Alerts", href: "/dashboard/requests" },
  { icon: Settings, label: "Admin", href: "/dashboard/settings" },
];

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ isCollapsed, onToggle }: SidebarProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const pathname = usePathname();
  const router = useRouter();
  const { logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    router.push("/auth/login");
  };

  return (
    <aside
      className={cn(
        "border-r border-glass-border bg-glass-light backdrop-blur-md flex flex-col transition-all duration-300 relative",
        isCollapsed ? "w-20" : "w-64"
      )}
    >
      {/* Toggle Button - Rectangular design, fully contained within sidebar */}
      {/* Design Rationale: Positioned at top-right corner inside sidebar (not on border) following 
          F-pattern scanning principles. Rectangular shape (h-10 w-8) provides optimal touch target 
          while maintaining visual hierarchy. High contrast (cyber-cyan border) ensures discoverability 
          without extending beyond sidebar boundaries. WCAG 2.1 AA compliant with proper focus states. */}
      <button
        onClick={onToggle}
        onKeyDown={(e) => {
          // Keyboard accessibility: Enter and Space activate button
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onToggle();
          }
        }}
        className={cn(
          // Base styles: Rectangular shape, fully contained within sidebar
          "absolute z-50 h-10 w-8 rounded-md",
          "bg-glass-medium border-2 border-cyber-cyan/50",
          "flex items-center justify-center",
          "transition-all duration-200 ease-out",
          "shadow-md shadow-cyber-cyan/20",
          "backdrop-blur-sm",
          // Positioning: Top-right corner, fully inside sidebar with padding from edges
          "top-4 right-3",
          // Hover state: Increased visibility and feedback
          "hover:bg-cyber-cyan/20 hover:border-cyber-cyan/90",
          "hover:shadow-cyber-cyan/40 hover:shadow-lg",
          "hover:scale-105",
          // Focus state: WCAG 2.1 AA compliant - visible focus ring
          "focus:outline-none focus:ring-2 focus:ring-cyber-cyan/60 focus:ring-offset-1 focus:ring-offset-glass-light",
          // Active state: Pressed feedback
          "active:scale-100 active:bg-cyber-cyan/30"
        )}
        aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        aria-expanded={!isCollapsed}
        title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {isCollapsed ? (
          <ChevronRight 
            className="w-5 h-5 text-cyber-cyan transition-colors duration-200" 
            strokeWidth={2.5}
            aria-hidden="true"
          />
        ) : (
          <ChevronLeft 
            className="w-5 h-5 text-cyber-cyan transition-colors duration-200" 
            strokeWidth={2.5}
            aria-hidden="true"
          />
        )}
      </button>
      {/* Logo */}
      <div className={cn("border-b border-glass-border transition-all duration-300", isCollapsed ? "p-4" : "p-6")}>
        <div className={cn("flex flex-col gap-2", isCollapsed && "items-center")}>
          <div className={cn("flex items-center", isCollapsed ? "justify-center" : "gap-3")}>
            <div className="relative w-10 h-10 flex-shrink-0">
              <Image
                src="/suraksh_logo.png"
                alt="SURAKSH Logo"
                fill
                sizes="40px"
                className="object-contain"
                priority
              />
            </div>
            {!isCollapsed && (
              <>
                <span className="text-xl font-bold tracking-tight text-white whitespace-nowrap">
                  SURAKSH
                </span>
              </>
            )}
          </div>
          {!isCollapsed && (
            <span className="text-xs text-gray-500 ml-[52px]">Intelligence Portal</span>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2 overflow-hidden">
        {navItems.map((item, idx) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.label}
              href={item.href}
              onClick={() => setActiveIndex(idx)}
              className={cn(
                "flex items-center rounded-lg transition-all duration-200 group relative",
                isCollapsed ? "justify-center px-3 py-3 w-full" : "gap-3 px-4 py-3 w-full",
                isActive
                  ? "bg-cyber-cyan/10 text-cyber-cyan border border-cyber-cyan/30 shadow-glow-cyan"
                  : "text-gray-400 hover:text-white hover:bg-glass-medium",
                "max-w-full"
              )}
              title={isCollapsed ? item.label : undefined}
            >
              <item.icon className={cn(
                "w-5 h-5 flex-shrink-0",
                !isCollapsed && "ml-0"
              )} />
              {!isCollapsed && (
                <span className="font-medium whitespace-nowrap truncate">{item.label}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Secure Mode Indicator */}
      <div className="p-4 border-t border-glass-border">
        <div className={cn(
          "flex items-center rounded-lg bg-glass-medium border border-glass-border",
          isCollapsed ? "justify-center px-3 py-3" : "gap-3 px-4 py-3"
        )}>
          <Shield className="w-5 h-5 text-cyber-cyan flex-shrink-0 flex items-center" />
          {!isCollapsed && (
            <div className="flex flex-col items-start">
              <span className="text-xs font-medium text-gray-400">Secure Mode</span>
              <span className="text-xs text-cyber-cyan font-mono">E2E Encrypted</span>
            </div>
          )}
        </div>
      </div>

      {/* Logout Button */}
      <div className="p-4 border-t border-glass-border">
        <button
          onClick={handleLogout}
          className={cn(
            "flex items-center rounded-lg transition-all duration-200 w-full",
            isCollapsed ? "justify-center px-3 py-3" : "gap-3 px-4 py-3",
            "text-gray-400 hover:text-white hover:bg-glass-medium",
            "hover:border-crimson-500/30 border border-transparent"
          )}
          title={isCollapsed ? "Logout" : undefined}
        >
          <LogOut className="w-5 h-5 flex-shrink-0" />
          {!isCollapsed && (
            <span className="font-medium whitespace-nowrap truncate">Logout</span>
          )}
        </button>
      </div>
    </aside>
  );
}
