import { apiClient } from "@/lib/api-client";
import type { AuthResponse, LoginPayload, RegisterPayload } from "@/types/auth";

export async function login(payload: LoginPayload) {
  const { data } = await apiClient.post<AuthResponse>("/accounts/login/", payload);
  return data;
}

export async function register(payload: RegisterPayload) {
  const { data } = await apiClient.post<AuthResponse>("/accounts/register/", payload);
  return data;
}

export async function googleOAuthLogin(accessToken: string) {
  const { data } = await apiClient.post<AuthResponse>("/accounts/google/", {
    access_token: accessToken,
  });
  return data;
}
