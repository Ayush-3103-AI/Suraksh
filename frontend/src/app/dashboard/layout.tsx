"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";
import { AppShell } from "@/components/layout/app-shell";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { token, isAuthenticated } = useAuthStore();
  // Fixed: Use state to track if we've checked auth on client (prevents hydration mismatch)
  const [hasCheckedAuth, setHasCheckedAuth] = useState(false);
  const [isClient, setIsClient] = useState(false);

  // Ensure we're on the client before using client-only hooks
  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    // Only run auth check on client side
    if (!isClient) return;

    // Check authentication status
    // Wait a tick to ensure Zustand has hydrated from localStorage
    const checkAuth = () => {
      const currentToken = token || (typeof window !== "undefined" ? localStorage.getItem("auth_token") : null);
      const hasAuth = isAuthenticated || !!currentToken;

      if (!hasAuth) {
        // No token found, redirect to login
        router.push("/auth/login");
      } else {
        // Fixed: Mark that we've checked auth on client side
        setHasCheckedAuth(true);
      }
    };

    // Use setTimeout to ensure Zustand hydration completes
    const timeoutId = setTimeout(checkAuth, 0);

    return () => clearTimeout(timeoutId);
  }, [token, isAuthenticated, router, isClient]);

  // Fixed: Always render a valid React element during SSR
  // Return a loading state instead of null to prevent SSR errors
  if (!isClient || !hasCheckedAuth) {
    return (
      <div className="flex h-screen items-center justify-center bg-space text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyber-cyan mx-auto mb-4"></div>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  return <AppShell>{children}</AppShell>;
}

