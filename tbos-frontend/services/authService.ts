// ============================================================
// services/authService.ts
// ============================================================

import { api, publicApi } from "@/lib/axios";
import type {
  AuthPayload,
  ChangePasswordPayload,
  GoogleLoginPayload,
  LoginCredentials,
  ProfileUpdatePayload,
  RegisterCredentials,
  User,
  UserProfile,
} from "@/types/auth";
import type { ApiSuccess } from "@/types/api";

const AuthService = {
  /** Register a new user */
  async register(credentials: RegisterCredentials): Promise<ApiSuccess<AuthPayload>> {
    const { data } = await publicApi.post<ApiSuccess<AuthPayload>>(
      "/auth/register/",
      credentials
    );
    return data;
  },

  /** Email/password login */
  async login(credentials: LoginCredentials): Promise<ApiSuccess<AuthPayload>> {
    const { data } = await publicApi.post<ApiSuccess<AuthPayload>>(
      "/auth/login/",
      credentials
    );
    return data;
  },

  /** Google OAuth login */
  async googleLogin(payload: GoogleLoginPayload): Promise<ApiSuccess<AuthPayload>> {
    const { data } = await publicApi.post<ApiSuccess<AuthPayload>>(
      "/auth/google-login/",
      payload
    );
    return data;
  },

  /** Logout — blacklists refresh token */
  async logout(refreshToken: string): Promise<void> {
    await api.post("/auth/logout/", { refresh_token: refreshToken });
  },

  /** Get current authenticated user */
  async getMe(): Promise<User> {
    const { data } = await api.get<ApiSuccess<User>>("/auth/me/");
    return data.data;
  },

  /** Get current user's profile */
  async getProfile(): Promise<UserProfile> {
    const { data } = await api.get<ApiSuccess<UserProfile>>("/auth/profile/");
    return data.data;
  },

  /** Update profile */
  async updateProfile(payload: ProfileUpdatePayload): Promise<UserProfile> {
    const { data } = await api.patch<ApiSuccess<UserProfile>>(
      "/auth/profile/update/",
      payload
    );
    return data.data;
  },

  /** Change password */
  async changePassword(payload: ChangePasswordPayload): Promise<void> {
    await api.put("/auth/change-password/", payload);
  },
};

export default AuthService;
