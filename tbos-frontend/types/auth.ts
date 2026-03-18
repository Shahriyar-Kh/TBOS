// ============================================================
// types/auth.ts
// ============================================================

export type UserRole = "admin" | "instructor" | "student";

export interface UserProfile {
  id: string;
  avatar: string | null;
  bio: string;
  headline: string;
  country: string;
  city: string;
  timezone: string;
  phone_number: string;
  website: string;
  linkedin: string;
  github: string;
  twitter: string;
  skills: string[];
  education: string;
  experience: string;
  profile_visibility: "public" | "private";
  date_created: string;
  date_updated: string;
}

export interface User {
  id: string;
  email: string;
  username: string | null;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_verified: boolean;
  google_account: boolean;
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
  profile: UserProfile | null;
}

export interface AuthPayload {
  access_token: string;
  refresh_token: string;
  user_role: UserRole;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  first_name: string;
  last_name: string;
  email: string;
  username?: string;
  password: string;
  confirm_password: string;
  role?: "student" | "instructor";
}

export interface GoogleLoginPayload {
  id_token: string;
}

export interface ChangePasswordPayload {
  old_password: string;
  new_password: string;
}

export interface ProfileUpdatePayload {
  bio?: string;
  headline?: string;
  country?: string;
  city?: string;
  timezone?: string;
  phone_number?: string;
  website?: string;
  linkedin?: string;
  github?: string;
  twitter?: string;
  skills?: string[];
  education?: string;
  experience?: string;
  profile_visibility?: "public" | "private";
}
