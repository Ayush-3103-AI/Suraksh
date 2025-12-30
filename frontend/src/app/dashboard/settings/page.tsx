"use client";

import { HoloCard } from "@/components/ui/holo-card";
import { useAuthStore } from "@/store/auth-store";
import { authApi } from "@/lib/api/auth";

export default function SettingsPage() {
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    authApi.logout();
    logout();
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-display uppercase tracking-wider text-cyan-400 mb-2">
          Settings
        </h1>
        <p className="text-slate-500">User preferences and system configuration</p>
      </div>

      <HoloCard title="User Information">
        {user && (
          <div className="space-y-3">
            <div>
              <div className="text-sm text-slate-500">Username</div>
              <div className="text-cyan-400 font-mono">{user.username}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500">Email</div>
              <div className="text-cyan-400 font-mono">{user.email}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500">Clearance Level</div>
              <div className="text-cyan-400 font-mono">{user.clearance_level}</div>
            </div>
          </div>
        )}
      </HoloCard>

      <HoloCard title="Actions">
        <button
          onClick={handleLogout}
          className="px-4 py-2 bg-crimson-500/20 border border-crimson-500/50 rounded text-crimson-500 hover:bg-crimson-500/30 transition-colors"
        >
          Logout
        </button>
      </HoloCard>
    </div>
  );
}

