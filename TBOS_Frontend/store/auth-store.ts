import { create } from "zustand";
import { clearAuthCookies, getRoleFromCookie, setAuthCookies } from "@/lib/auth-cookies";
import type { AuthResponse, User, UserRole } from "@/types/auth";

interface AuthState {
  user: User | null;
  role: UserRole | null;
  accessToken: string | null;
  setAuth: (auth: AuthResponse) => void;
  logout: () => void;
  hydrateRoleFromCookie: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  role: null,
  accessToken: null,
  setAuth: (auth) => {
    setAuthCookies(auth.access, auth.user.role);
    set({ user: auth.user, role: auth.user.role, accessToken: auth.access });
  },
  logout: () => {
    clearAuthCookies();
    set({ user: null, role: null, accessToken: null });
  },
  hydrateRoleFromCookie: () => {
    const role = getRoleFromCookie();
    if (role) {
      set({ role });
    }
  },
}));
