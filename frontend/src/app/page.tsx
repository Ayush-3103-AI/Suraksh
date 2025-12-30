"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  // Fixed: Track client-side state to prevent blank page during SSR
  const [isClient, setIsClient] = useState(false);
  
  useEffect(() => {
    setIsClient(true);
    if (typeof window !== "undefined") {
      router.push("/dashboard");
    }
  }, [router]);
  
  // Fixed: Return loading state instead of null to prevent blank page
  if (!isClient) {
    return (
      <div className="flex h-screen items-center justify-center bg-space text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyber-cyan mx-auto mb-4"></div>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="flex h-screen items-center justify-center bg-space text-white">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyber-cyan mx-auto mb-4"></div>
        <p className="text-gray-400">Redirecting to dashboard...</p>
      </div>
    </div>
  );
}

