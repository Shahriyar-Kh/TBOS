// ============================================================
// store/authStore.ts — Zustand authentication store
// ============================================================

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import Cookies from "js-cookie";

import type { User, UserRole, AuthPayload } from "@/types/auth";
import { ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY, ROLE_ROUTES } from "@/config/constants";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  setAuth: (payload: AuthPayload) => void;
  setUser: (user: User) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  getRedirectPath: () => string;
}

const COOKIE_OPTIONS = {
  secure: process.env.NODE_ENV === "production",
  sameSite: "strict" as const,
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,

      setAuth(payload: AuthPayload) {
        const { access_token, refresh_token, user } = payload;

        // Store tokens in httpOnly-like cookies
        Cookies.set(ACCESS_TOKEN_KEY, access_token, {
          ...COOKIE_OPTIONS,
          expires: 1 / 96, // 15 minutes
        });
        Cookies.set(REFRESH_TOKEN_KEY, refresh_token, {
          ...COOKIE_OPTIONS,
          expires: 1, // 1 day
        });

        set({ user, isAuthenticated: true, isLoading: false });
      },

      setUser(user: User) {
        set({ user });
      },

      logout() {
        Cookies.remove(ACCESS_TOKEN_KEY);
        Cookies.remove(REFRESH_TOKEN_KEY);
        set({ user: null, isAuthenticated: false, isLoading: false });

        if (typeof window !== "undefined") {
          window.location.href = "/auth/login";
        }
      },

      setLoading(isLoading: boolean) {
        set({ isLoading });
      },

      getRedirectPath(): string {
        const role = get().user?.role as UserRole | undefined;
        if (!role) return "/auth/login";
        return ROLE_ROUTES[role] ?? "/";
      },
    }),
    {
      name: "tbos-auth",
      storage: createJSONStorage(() => sessionStorage),
      // Only persist user object; tokens live in cookies
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);

// Convenience selectors
export const selectUser = (state: AuthState) => state.user;
export const selectRole = (state: AuthState) => state.user?.role;
export const selectIsAuthenticated = (state: AuthState) => state.isAuthenticated;
