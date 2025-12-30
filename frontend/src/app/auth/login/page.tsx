"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { useAuthStore } from "@/store/auth-store";
import { authApi } from "@/lib/api/auth";
import { HoloCard } from "@/components/ui/holo-card";
import { ConnectionTest } from "@/components/connection-test";

export default function LoginPage() {
  const router = useRouter();
  const { setUser, setToken, token, isAuthenticated } = useAuthStore();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    const checkAuth = () => {
      const currentToken = token || (typeof window !== "undefined" ? localStorage.getItem("auth_token") : null);
      const hasAuth = isAuthenticated || !!currentToken;

      if (hasAuth) {
        // Already authenticated, redirect to dashboard
        router.push("/dashboard");
      }
    };

    // Wait for Zustand to hydrate
    const timeoutId = setTimeout(checkAuth, 100);

    return () => clearTimeout(timeoutId);
  }, [token, isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await authApi.login({ username, password });
      // Set token in both apiClient and auth store
      setToken(response.access_token);
      
      // Fetch user info - wrap in try-catch to prevent interceptor redirect
      try {
        const user = await authApi.getCurrentUser();
        setUser(user);
      } catch (userErr: any) {
        // If getCurrentUser fails, still proceed with login but log the error
        console.error("Failed to fetch user info:", userErr);
        // Create a minimal user object from the token payload if possible
        // For now, we'll still redirect as the token is valid
      }
      
      // Use window.location for more reliable navigation
      // This ensures a full page navigation and prevents any reload issues
      window.location.href = "/dashboard";
    } catch (err: any) {
      setError(
        err.response?.data?.detail || err.message || "Connection failed"
      );
      setLoading(false);
    }
  };

  return (
    <div className="h-screen flex bg-void-950 grid-overlay relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 grid-overlay opacity-20"></div>
      <div className="absolute top-0 left-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl"></div>
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl"></div>
      
      {/* Left Side - Logo Section (55% width) */}
      <div className="hidden lg:flex lg:w-[55%] flex-col items-center justify-center px-8 py-6 relative z-10">
        <div className="w-full max-w-2xl space-y-6">
          {/* Logo with subtle glow effect - Median size */}
          <div className="relative w-full aspect-square max-w-lg mx-auto">
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-purple-500/10 rounded-full blur-2xl"></div>
            <div className="relative w-full h-full">
              <Image
                src="/suraksh_logo.png"
                alt="SURAKSH Logo"
                fill
                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                className="object-contain drop-shadow-2xl"
                priority
              />
            </div>
          </div>
          
          {/* Branding Text - Without SURAKSH heading */}
          <div className="text-center space-y-3">
            <p className="text-slate-300 text-base font-mono font-medium tracking-wide">
              High-Security Intelligence Platform
            </p>
            <p className="text-slate-500 text-xs font-mono leading-relaxed max-w-sm mx-auto">
              Quantum-resilient multi-agency intelligence collaboration
            </p>
          </div>
        </div>
      </div>

      {/* Right Side - Login Form (45% width) */}
      <div className="w-full lg:w-[45%] flex items-center justify-center px-4 lg:px-8 py-4 relative z-10">
        <div className="w-full max-w-md">
        <ConnectionTest />
          
          {/* Mobile Logo - Only visible on small screens */}
          <div className="mb-4 lg:hidden">
            <div className="flex flex-col items-center gap-3 mb-3">
              <div className="relative w-24 h-24">
                <Image
                  src="/suraksh_logo.png"
                  alt="SURAKSH Logo"
                  fill
                  sizes="96px"
                  className="object-contain"
                  priority
                />
              </div>
            </div>
            <p className="text-slate-500 text-xs font-mono text-center">High-security intelligence platform</p>
          </div>

          {/* Login Card */}
          <HoloCard className="w-full tech-border backdrop-blur-xl bg-void-900/70 border-cyan-500/30 shadow-2xl">
            <div className="p-6 lg:p-8 space-y-5">
              {/* Header */}
              <div className="space-y-1.5 pb-1">
                <h2 className="text-xl font-display uppercase tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-cyan-300 font-bold">
                  Access Portal
                </h2>
                <p className="text-slate-400 text-xs font-mono">
                  Authenticate to continue
                </p>
          </div>

              {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
                  <div className="p-2.5 bg-crimson-500/10 border border-crimson-500/40 rounded-lg">
                    <p className="text-crimson-400 text-xs font-mono">{error}</p>
            </div>
          )}

                <div className="space-y-1.5">
                  <label className="block text-xs font-display uppercase tracking-widest text-cyan-400/90 font-semibold">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
                    className="w-full px-4 py-2.5 bg-void-800/60 border border-cyan-500/30 rounded-lg text-cyan-300 placeholder:text-slate-600 font-mono text-sm focus:outline-none focus:border-cyan-500 focus:shadow-[0_0_15px_rgba(6,182,212,0.25)] focus:ring-1 focus:ring-cyan-500/20 transition-all duration-200"
              placeholder="Enter username"
              required
            />
          </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-display uppercase tracking-widest text-cyan-400/90 font-semibold">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-2.5 bg-void-800/60 border border-cyan-500/30 rounded-lg text-cyan-300 placeholder:text-slate-600 font-mono text-sm focus:outline-none focus:border-cyan-500 focus:shadow-[0_0_15px_rgba(6,182,212,0.25)] focus:ring-1 focus:ring-cyan-500/20 transition-all duration-200"
              placeholder="Enter password"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
                  className="w-full py-2.5 mt-1 bg-gradient-to-r from-cyan-500/10 via-cyan-500/15 to-purple-500/10 border-2 border-cyan-500/50 rounded-lg text-cyan-300 font-display uppercase tracking-wider text-xs font-semibold hover:from-cyan-500/20 hover:via-cyan-500/25 hover:to-purple-500/20 hover:border-cyan-500 hover:shadow-[0_0_20px_rgba(6,182,212,0.3)] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none"
          >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
                      AUTHENTICATING...
                    </span>
                  ) : (
                    "LOGIN"
                  )}
          </button>
        </form>

              {/* Test Credentials - Compact */}
              <div className="pt-3 border-t border-cyan-500/20">
                <p className="text-xs font-display uppercase tracking-wider text-slate-500 mb-2 text-center">Test Credentials</p>
                <div className="space-y-1.5 font-mono text-xs">
                  {[
                    { user: "test", pass: "test", level: "L1" },
                    { user: "admin", pass: "test", level: "L3" },
                    { user: "analyst", pass: "test", level: "L2" }
                  ].map((cred, idx) => (
                    <div key={idx} className="flex items-center gap-2 px-2.5 py-1.5 rounded bg-void-800/30 border border-cyan-500/10 hover:border-cyan-500/30 transition-colors">
                      <div className="w-1.5 h-1.5 rounded-full bg-cyan-500/60"></div>
                      <span className="text-cyan-400/90 flex-1">{cred.user} / {cred.pass}</span>
                      <span className="text-slate-500 text-[10px] px-1.5 py-0.5 rounded bg-slate-800/50">{cred.level}</span>
            </div>
                  ))}
            </div>
          </div>
        </div>
      </HoloCard>
        </div>
      </div>
    </div>
  );
}

