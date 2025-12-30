import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { UserResponse } from "@/lib/api/auth";
import { registerAuthTokenAccessors } from "@/lib/api/client";

interface AuthState {
  user: UserResponse | null;
  token: string | null;
  isAuthenticated: boolean;
  setUser: (user: UserResponse | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setUser: (user) =>
        set({ user, isAuthenticated: !!user }),
      setToken: (token) => {
        set({ token });
        // Sync token to apiClient's legacy storage for backward compatibility
        // This ensures apiClient can read the token even before Zustand fully hydrates
        if (typeof window !== "undefined") {
          if (token) {
            localStorage.setItem("auth_token", token);
          } else {
            localStorage.removeItem("auth_token");
          }
        }
      },
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false });
        // Clear legacy storage
        if (typeof window !== "undefined") {
          localStorage.removeItem("auth_token");
        }
      },
    }),
    {
      name: "auth-storage",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ token: state.token, user: state.user }),
      onRehydrateStorage: () => (state) => {
        // After Zustand hydrates, register token accessors with apiClient
        if (state && typeof window !== "undefined") {
          registerAuthTokenAccessors(
            () => state.token,
            () => {
              state.setToken(null);
              state.setUser(null);
            }
          );
          // Sync token to legacy storage on hydration
          if (state.token) {
            localStorage.setItem("auth_token", state.token);
          }
        }
      },
    }
  )
);

// Fixed: Register accessors immediately if store is already hydrated (client-side only)
// Wrapped in a function to prevent SSR execution
if (typeof window !== "undefined") {
  try {
    const store = useAuthStore.getState();
    registerAuthTokenAccessors(
      () => store.token,
      () => {
        store.logout();
      }
    );
    // Sync on initial load
    if (store.token) {
      localStorage.setItem("auth_token", store.token);
    }
  } catch (error) {
    // Silently fail during SSR or if store is not ready
    console.debug('[AuthStore] Initial registration skipped:', error);
  }
}

