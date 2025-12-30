import { apiClient } from "./client";
import { z } from "zod";

// Zod schemas for API validation
export const LoginRequestSchema = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
});

export const RegisterRequestSchema = z.object({
  username: z.string().min(3),
  email: z.string().email(),
  password: z.string().min(6),
  clearance_level: z.enum(["L1", "L2", "L3"]).default("L1"),
});

export const TokenResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string().default("bearer"),
  pqc_public_key: z.string().optional(),
});

export const UserResponseSchema = z.object({
  username: z.string(),
  email: z.string(),
  clearance_level: z.enum(["L1", "L2", "L3"]),
  is_active: z.boolean(),
});

export type LoginRequest = z.infer<typeof LoginRequestSchema>;
export type RegisterRequest = z.infer<typeof RegisterRequestSchema>;
export type TokenResponse = z.infer<typeof TokenResponseSchema>;
export type UserResponse = z.infer<typeof UserResponseSchema>;

// API functions
export const authApi = {
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    try {
      const response = await apiClient.axiosInstance.post<TokenResponse>(
        "/api/v1/auth/login",
        credentials
      );
      // Store token
      if (response.data.access_token) {
        apiClient.setToken(response.data.access_token);
      }
      return response.data;
    } catch (error: any) {
      // Fixed: Provide user-friendly error message for connection failures including ERR_CONNECTION_RESET
      const errorCode = error.code || '';
      const errorMessage = error.message || '';
      const errorString = `${errorMessage} ${errorCode}`.toLowerCase();
      
      if (errorCode === 'ERR_NETWORK' || 
          errorCode === 'ERR_CONNECTION_REFUSED' ||
          errorCode === 'ERR_CONNECTION_RESET' ||
          errorMessage?.includes('ERR_CONNECTION_REFUSED') ||
          errorMessage?.includes('ERR_CONNECTION_RESET') ||
          errorMessage?.includes('ECONNREFUSED') ||
          (errorString.includes('connection') && (errorString.includes('reset') || errorString.includes('refused') || errorString.includes('failed')))) {
        throw new Error('Cannot connect to backend server. Please ensure the backend is running on http://localhost:8000');
      }
      throw error;
    }
  },

  async register(userData: RegisterRequest): Promise<UserResponse> {
    const response = await apiClient.axiosInstance.post<UserResponse>(
      "/api/v1/auth/register",
      userData
    );
    return response.data;
  },

  async getCurrentUser(): Promise<UserResponse> {
    try {
      const response = await apiClient.axiosInstance.get<UserResponse>(
        "/api/v1/auth/me"
      );
      return response.data;
    } catch (error: any) {
      // Fixed: Provide user-friendly error message for connection failures
      const errorCode = error.code || '';
      const errorMessage = error.message || '';
      const errorString = `${errorMessage} ${errorCode}`.toLowerCase();
      
      if (errorCode === 'ERR_NETWORK' || 
          errorCode === 'ERR_CONNECTION_REFUSED' ||
          errorCode === 'ERR_CONNECTION_RESET' ||
          errorMessage?.includes('ERR_CONNECTION_REFUSED') ||
          errorMessage?.includes('ERR_CONNECTION_RESET') ||
          errorMessage?.includes('ECONNREFUSED') ||
          (errorString.includes('connection') && (errorString.includes('reset') || errorString.includes('refused') || errorString.includes('failed')))) {
        throw new Error('Cannot connect to backend server. Please ensure the backend is running on http://localhost:8000');
      }
      throw error;
    }
  },

  logout(): void {
    apiClient.setToken("");
    if (typeof window !== "undefined") {
      window.location.href = "/auth/login";
    }
  },
};

