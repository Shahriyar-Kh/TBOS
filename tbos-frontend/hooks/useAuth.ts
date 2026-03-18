// ============================================================
// hooks/useAuth.ts
// ============================================================
"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import Cookies from "js-cookie";

import AuthService from "@/services/authService";
import { useAuthStore } from "@/store/authStore";
import { QUERY_KEYS, REFRESH_TOKEN_KEY, ROLE_ROUTES } from "@/config/constants";
import type {
  LoginCredentials,
  RegisterCredentials,
  ChangePasswordPayload,
  ProfileUpdatePayload,
} from "@/types/auth";
import { extractApiError } from "@/lib/utils";

// ── Me Query ─────────────────────────────────────────────────
export function useMe() {
  const { isAuthenticated } = useAuthStore();
  return useQuery({
    queryKey: QUERY_KEYS.auth.me,
    queryFn: AuthService.getMe,
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });
}

// ── Profile Query ─────────────────────────────────────────────
export function useProfile() {
  const { isAuthenticated } = useAuthStore();
  return useQuery({
    queryKey: QUERY_KEYS.auth.profile,
    queryFn: AuthService.getProfile,
    enabled: isAuthenticated,
  });
}

// ── Login Mutation ────────────────────────────────────────────
export function useLogin() {
  const { setAuth } = useAuthStore();
  const router = useRouter();

  return useMutation({
    mutationFn: (credentials: LoginCredentials) =>
      AuthService.login(credentials),
    onSuccess: (response) => {
      setAuth(response.data);
      const role = response.data.user_role;
      const redirectTo = ROLE_ROUTES[role] ?? "/";
      toast.success(`Welcome back, ${response.data.user.first_name}!`);
      router.push(redirectTo);
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ── Register Mutation ──────────────────────────────────────────
export function useRegister() {
  const { setAuth } = useAuthStore();
  const router = useRouter();

  return useMutation({
    mutationFn: (credentials: RegisterCredentials) =>
      AuthService.register(credentials),
    onSuccess: (response) => {
      setAuth(response.data);
      const role = response.data.user_role;
      toast.success("Account created successfully!");
      router.push(ROLE_ROUTES[role] ?? "/");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ── Google Login Mutation ──────────────────────────────────────
export function useGoogleLogin() {
  const { setAuth } = useAuthStore();
  const router = useRouter();

  return useMutation({
    mutationFn: (idToken: string) =>
      AuthService.googleLogin({ id_token: idToken }),
    onSuccess: (response) => {
      setAuth(response.data);
      const role = response.data.user_role;
      toast.success(`Welcome, ${response.data.user.first_name}!`);
      router.push(ROLE_ROUTES[role] ?? "/");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ── Logout Mutation ────────────────────────────────────────────
export function useLogout() {
  const { logout } = useAuthStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const refreshToken = Cookies.get(REFRESH_TOKEN_KEY);
      if (refreshToken) {
        await AuthService.logout(refreshToken);
      }
    },
    onSettled: () => {
      queryClient.clear();
      logout();
      toast.success("Signed out successfully.");
    },
  });
}

// ── Change Password Mutation ───────────────────────────────────
export function useChangePassword() {
  return useMutation({
    mutationFn: (payload: ChangePasswordPayload) =>
      AuthService.changePassword(payload),
    onSuccess: () => {
      toast.success("Password changed successfully.");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ── Update Profile Mutation ────────────────────────────────────
export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProfileUpdatePayload) =>
      AuthService.updateProfile(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.auth.profile });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.auth.me });
      toast.success("Profile updated successfully.");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}
