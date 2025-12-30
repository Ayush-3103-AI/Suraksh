import axios, { AxiosInstance, InternalAxiosRequestConfig } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Import auth store to sync token storage
let getAuthToken: (() => string | null) | null = null;
let clearAuthToken: (() => void) | null = null;

// Function to register auth store getters (called from auth-store.ts)
export function registerAuthTokenAccessors(
  getToken: () => string | null,
  clearToken: () => void
) {
  getAuthToken = getToken;
  clearAuthToken = clearToken;
}


class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
      // Fixed: Add default timeout (5 minutes) for all requests, especially file uploads
      timeout: 5 * 60 * 1000, // 5 minutes in milliseconds
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = this.getToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized - clear token and redirect to login
          // Only redirect if we're not already on the login page
          if (typeof window !== "undefined" && !window.location.pathname.startsWith("/auth/login")) {
            this.clearToken();
            // Also clear Zustand store
            try {
              const authStorage = localStorage.getItem("auth-storage");
              if (authStorage) {
                const parsed = JSON.parse(authStorage);
                const updated = { ...parsed, state: { ...parsed.state, token: null, user: null } };
                localStorage.setItem("auth-storage", JSON.stringify(updated));
              }
            } catch (e) {
              // If clearing Zustand fails, legacy storage is already cleared
            }
            window.location.href = "/auth/login";
          }
        }
        return Promise.reject(error);
      }
    );
  }

  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    
    // Primary: Get token from Zustand store (single source of truth)
    // Read directly from Zustand's localStorage to avoid hydration race conditions
    try {
      const authStorage = localStorage.getItem("auth-storage");
      if (authStorage) {
        const parsed = JSON.parse(authStorage);
        const token = parsed.state?.token;
        if (token) {
          // Sync to legacy storage for backward compatibility
          localStorage.setItem("auth_token", token);
          return token;
        }
      }
    } catch (e) {
      // If parsing fails, fall through to legacy storage
    }

    // Fallback: Check registered accessor (for runtime access)
    if (getAuthToken) {
      const token = getAuthToken();
      if (token) {
        localStorage.setItem("auth_token", token);
        return token;
      }
    }

    // Legacy fallback: Check old storage location
    const legacyToken = localStorage.getItem("auth_token");
    if (legacyToken) {
      // Migrate to Zustand store if found
      try {
        const authStorage = localStorage.getItem("auth-storage");
        if (authStorage) {
          const parsed = JSON.parse(authStorage);
          if (!parsed.state?.token) {
            // Token exists in legacy location but not in Zustand, sync it
            const updated = { ...parsed, state: { ...parsed.state, token: legacyToken } };
            localStorage.setItem("auth-storage", JSON.stringify(updated));
          }
        } else {
          // Create new Zustand storage entry
          localStorage.setItem("auth-storage", JSON.stringify({
            state: { token: legacyToken, user: null },
            version: 0
          }));
        }
      } catch (e) {
        // If migration fails, return legacy token anyway
      }
      return legacyToken;
    }
    
    return null;
  }

  private clearToken(): void {
    if (typeof window === "undefined") return;
    // Clear from Zustand store
    if (clearAuthToken) {
      clearAuthToken();
    }
    // Also clear legacy storage for cleanup
    localStorage.removeItem("auth_token");
  }

  public setToken(token: string): void {
    if (typeof window === "undefined") return;
    // Token is set via Zustand store's setToken, which persists automatically
    // This method is kept for backward compatibility but should not be used directly
    // The auth store's setToken should be used instead
    if (getAuthToken && typeof window !== "undefined") {
      // Sync to Zustand store if accessor is available
      try {
        const authStorage = localStorage.getItem("auth-storage");
        if (authStorage) {
          const parsed = JSON.parse(authStorage);
          const updated = { ...parsed, state: { ...parsed.state, token } };
          localStorage.setItem("auth-storage", JSON.stringify(updated));
        } else {
          // Create new storage entry
          localStorage.setItem("auth-storage", JSON.stringify({
            state: { token, user: null },
            version: 0
          }));
        }
      } catch (e) {
        // Fallback to legacy storage if Zustand storage is unavailable
        localStorage.setItem("auth_token", token);
      }
    } else {
      // Fallback to legacy storage
    localStorage.setItem("auth_token", token);
    }
  }

  public get axiosInstance(): AxiosInstance {
    return this.client;
  }

  // Convenience methods for direct API calls
  public async post<T = any>(url: string, data?: any, config?: any): Promise<{ data: T }> {
    const response = await this.client.post<T>(url, data, config);
    return response;
  }

  public async get<T = any>(url: string, config?: any): Promise<{ data: T }> {
    const response = await this.client.get<T>(url, config);
    return response;
  }
}

export const apiClient = new ApiClient();

